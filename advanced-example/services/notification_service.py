"""
Notification Service - Envía notificaciones a clientes
Patrón: Dead Letter Queue + Retry Logic
"""
import json
import time
from datetime import datetime
from typing import Dict
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bootstrap_servers: list):
        self.bootstrap_servers = bootstrap_servers

        # Producer para DLQ (Dead Letter Queue)
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3
        )

        # Consumer para notificaciones
        self.consumer = KafkaConsumer(
            'notifications.requests',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='notification-service-group',
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            max_poll_records=10
        )

        # Configuración de reintentos
        self.max_retries = 3
        self.retry_delay = 2  # segundos

        # Simulación de tasa de fallo
        self.failure_rate = 0.2  # 20% de fallos simulados

    def process_notifications(self):
        """Procesar solicitudes de notificación con retry y DLQ"""
        logger.info("🔔 Listening for notification requests...")

        try:
            for message in self.consumer:
                notification = message.value
                notification_id = notification.get('notification_id')

                logger.info(f"📬 Processing notification {notification_id}")

                # Procesar con reintentos
                success = self._send_notification_with_retry(notification)

                if success:
                    logger.info(f"✅ Notification sent: {notification_id}")

                    # Publicar evento de éxito
                    self._publish_notification_event(notification, 'SENT')
                else:
                    logger.error(f"❌ Failed to send notification: {notification_id}")

                    # Enviar a Dead Letter Queue
                    self._send_to_dlq(notification, message)

                    # Publicar evento de fallo
                    self._publish_notification_event(notification, 'FAILED')

                # Commit del offset
                self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping notification service...")
        finally:
            self.consumer.close()
            self.producer.close()

    def _send_notification_with_retry(self, notification: Dict) -> bool:
        """Intentar enviar notificación con reintentos"""
        attempt = 0

        while attempt < self.max_retries:
            attempt += 1

            try:
                # Simular envío de notificación
                success = self._send_notification(notification, attempt)

                if success:
                    return True

            except Exception as e:
                logger.warning(f"⚠️  Attempt {attempt} failed: {e}")

            if attempt < self.max_retries:
                wait_time = self.retry_delay * attempt  # Backoff exponencial
                logger.info(f"🔄 Retrying in {wait_time}s... (attempt {attempt}/{self.max_retries})")
                time.sleep(wait_time)

        return False

    def _send_notification(self, notification: Dict, attempt: int) -> bool:
        """
        Simular envío de notificación
        En producción, esto integraría con servicios como:
        - SendGrid/Mailgun para email
        - Twilio para SMS
        - Firebase para push notifications
        """
        notification_type = notification.get('type')
        channel = notification.get('channel', 'email')
        customer_id = notification.get('customer_id')
        message = notification.get('message')

        logger.info(f"  📤 Sending {channel} notification to {customer_id} (attempt {attempt})")
        logger.info(f"  📝 Message: {message}")

        # Simular latencia de red
        time.sleep(random.uniform(0.1, 0.5))

        # Simular fallos aleatorios (excepto en último intento)
        if attempt < self.max_retries and random.random() < self.failure_rate:
            raise Exception(f"Simulated {channel} service error")

        # Éxito
        return True

    def _send_to_dlq(self, notification: Dict, original_message):
        """Enviar notificación fallida a Dead Letter Queue"""
        dlq_message = {
            'original_notification': notification,
            'failure_timestamp': datetime.utcnow().isoformat(),
            'original_topic': original_message.topic,
            'original_partition': original_message.partition,
            'original_offset': original_message.offset,
            'reason': 'Max retries exceeded',
            'retry_count': self.max_retries
        }

        try:
            self.producer.send(
                'notifications.dlq',
                key=notification.get('notification_id'),
                value=dlq_message
            )
            self.producer.flush()

            logger.warning(f"⚠️  Sent to DLQ: {notification.get('notification_id')}")

        except KafkaError as e:
            logger.error(f"❌ Failed to send to DLQ: {e}")

    def _publish_notification_event(self, notification: Dict, status: str):
        """Publicar evento de notificación para analytics"""
        event = {
            'event_type': f'NOTIFICATION_{status}',
            'notification_id': notification.get('notification_id'),
            'order_id': notification.get('order_id'),
            'customer_id': notification.get('customer_id'),
            'channel': notification.get('channel'),
            'type': notification.get('type'),
            'timestamp': datetime.utcnow().isoformat()
        }

        self.producer.send(
            'notifications.events',
            key=notification.get('customer_id'),
            value=event
        )

    def close(self):
        """Cerrar conexiones"""
        self.producer.close()
        self.consumer.close()


class DLQProcessor:
    """Procesador para reintentar mensajes de Dead Letter Queue"""

    def __init__(self, bootstrap_servers: list):
        self.bootstrap_servers = bootstrap_servers

        self.consumer = KafkaConsumer(
            'notifications.dlq',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='dlq-processor-group',
            auto_offset_reset='earliest',
            enable_auto_commit=False
        )

        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all'
        )

    def process_dlq(self):
        """Procesar mensajes de DLQ y reintentar después de intervención"""
        logger.info("🔄 Processing Dead Letter Queue...")

        try:
            for message in self.consumer:
                dlq_message = message.value
                original_notification = dlq_message['original_notification']
                notification_id = original_notification.get('notification_id')

                logger.info(f"📋 DLQ Message: {notification_id}")
                logger.info(f"   Failed at: {dlq_message['failure_timestamp']}")
                logger.info(f"   Reason: {dlq_message['reason']}")
                logger.info(f"   Retries: {dlq_message['retry_count']}")

                # En producción, aquí habría lógica para:
                # - Analizar el motivo del fallo
                # - Notificar a un equipo de ops
                # - Decidir si reintentar o descartar
                # - Aplicar correcciones al mensaje si es necesario

                logger.info(f"   ⏸️  Manual intervention required")

                self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping DLQ processor...")
        finally:
            self.consumer.close()
            self.producer.close()


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'dlq':
        # Modo procesador de DLQ
        processor = DLQProcessor(['localhost:9092'])
        processor.process_dlq()
    else:
        # Modo servicio de notificaciones
        service = NotificationService(['localhost:9092'])
        service.process_notifications()
