"""
Order Service - Gestiona la creación y procesamiento de órdenes
Patrón: Event Sourcing + CQRS
"""
import json
import uuid
import time
from datetime import datetime
from typing import Dict, List, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderService:
    def __init__(self, bootstrap_servers: List[str]):
        self.bootstrap_servers = bootstrap_servers

        # Producer con configuración para garantías transaccionales
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Esperar confirmación de todos los replicas
            retries=3,
            max_in_flight_requests_per_connection=1,  # Garantizar orden
            enable_idempotence=True,  # Evitar duplicados
            transactional_id='order-service-tx'  # Habilitar transacciones
        )

        # Inicializar transacciones
        self.producer.init_transactions()

        # Consumer para respuestas del servicio de inventario
        self.consumer = KafkaConsumer(
            'inventory.responses',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='order-service-group',
            auto_offset_reset='latest',
            enable_auto_commit=False
        )

        # Estado en memoria (en producción sería una BD)
        self.orders = {}

    def create_order(self, customer_id: str, items: List[Dict]) -> str:
        """Crear una nueva orden con patrón transaccional"""
        order_id = str(uuid.uuid4())
        order = {
            'order_id': order_id,
            'customer_id': customer_id,
            'items': items,
            'status': 'PENDING',
            'total': sum(item['price'] * item['quantity'] for item in items),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            # Iniciar transacción
            self.producer.begin_transaction()

            # 1. Publicar evento de orden creada
            order_created_event = {
                'event_type': 'ORDER_CREATED',
                'order_id': order_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data': order
            }

            self.producer.send(
                'orders.events',
                key=order_id,
                value=order_created_event
            )

            # 2. Solicitar reserva de inventario
            inventory_request = {
                'request_id': str(uuid.uuid4()),
                'order_id': order_id,
                'items': items,
                'action': 'RESERVE',
                'timestamp': datetime.utcnow().isoformat()
            }

            self.producer.send(
                'inventory.requests',
                key=order_id,
                value=inventory_request
            )

            # Commit transacción
            self.producer.commit_transaction()

            # Guardar en estado local
            self.orders[order_id] = order

            logger.info(f"✅ Order created: {order_id} with {len(items)} items")
            return order_id

        except KafkaError as e:
            logger.error(f"❌ Error creating order: {e}")
            self.producer.abort_transaction()
            raise

    def process_inventory_responses(self):
        """Procesar respuestas del servicio de inventario"""
        logger.info("🔄 Listening for inventory responses...")

        try:
            for message in self.consumer:
                response = message.value
                order_id = response.get('order_id')

                if order_id not in self.orders:
                    logger.warning(f"⚠️  Unknown order: {order_id}")
                    continue

                order = self.orders[order_id]

                if response.get('status') == 'RESERVED':
                    # Inventario reservado exitosamente
                    self._confirm_order(order_id, order)

                elif response.get('status') == 'INSUFFICIENT_STOCK':
                    # Inventario insuficiente
                    self._cancel_order(order_id, order, response.get('reason'))

                # Commit manual del offset
                self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping inventory response processor...")
        finally:
            self.consumer.close()

    def _confirm_order(self, order_id: str, order: Dict):
        """Confirmar orden cuando el inventario está reservado"""
        try:
            self.producer.begin_transaction()

            order['status'] = 'CONFIRMED'
            order['updated_at'] = datetime.utcnow().isoformat()

            # Publicar evento de orden confirmada
            order_confirmed_event = {
                'event_type': 'ORDER_CONFIRMED',
                'order_id': order_id,
                'timestamp': datetime.utcnow().isoformat(),
                'data': order
            }

            self.producer.send(
                'orders.events',
                key=order_id,
                value=order_confirmed_event
            )

            # Notificar al cliente
            notification_request = {
                'notification_id': str(uuid.uuid4()),
                'order_id': order_id,
                'customer_id': order['customer_id'],
                'type': 'ORDER_CONFIRMED',
                'message': f"Your order {order_id} has been confirmed!",
                'channel': 'email',
                'timestamp': datetime.utcnow().isoformat()
            }

            self.producer.send(
                'notifications.requests',
                key=order['customer_id'],
                value=notification_request
            )

            self.producer.commit_transaction()
            self.orders[order_id] = order

            logger.info(f"✅ Order confirmed: {order_id}")

        except KafkaError as e:
            logger.error(f"❌ Error confirming order {order_id}: {e}")
            self.producer.abort_transaction()

    def _cancel_order(self, order_id: str, order: Dict, reason: str):
        """Cancelar orden por falta de inventario"""
        try:
            self.producer.begin_transaction()

            order['status'] = 'CANCELLED'
            order['cancellation_reason'] = reason
            order['updated_at'] = datetime.utcnow().isoformat()

            # Publicar evento de orden cancelada
            order_cancelled_event = {
                'event_type': 'ORDER_CANCELLED',
                'order_id': order_id,
                'timestamp': datetime.utcnow().isoformat(),
                'reason': reason,
                'data': order
            }

            self.producer.send(
                'orders.events',
                key=order_id,
                value=order_cancelled_event
            )

            # Notificar al cliente
            notification_request = {
                'notification_id': str(uuid.uuid4()),
                'order_id': order_id,
                'customer_id': order['customer_id'],
                'type': 'ORDER_CANCELLED',
                'message': f"Your order {order_id} was cancelled: {reason}",
                'channel': 'email',
                'timestamp': datetime.utcnow().isoformat()
            }

            self.producer.send(
                'notifications.requests',
                key=order['customer_id'],
                value=notification_request
            )

            self.producer.commit_transaction()
            self.orders[order_id] = order

            logger.info(f"❌ Order cancelled: {order_id} - {reason}")

        except KafkaError as e:
            logger.error(f"❌ Error cancelling order {order_id}: {e}")
            self.producer.abort_transaction()

    def get_order_status(self, order_id: str) -> Optional[Dict]:
        """Consultar estado de una orden"""
        return self.orders.get(order_id)

    def close(self):
        """Cerrar conexiones"""
        self.producer.close()
        self.consumer.close()


if __name__ == '__main__':
    import sys

    service = OrderService(['localhost:9092'])

    if len(sys.argv) > 1 and sys.argv[1] == 'processor':
        # Modo procesador de respuestas
        service.process_inventory_responses()
    else:
        # Modo creación de órdenes de ejemplo
        logger.info("📦 Creating sample orders...")

        # Orden 1: Exitosa (stock suficiente)
        order1_id = service.create_order(
            customer_id='customer-001',
            items=[
                {'product_id': 'LAPTOP-001', 'quantity': 1, 'price': 999.99},
                {'product_id': 'MOUSE-001', 'quantity': 2, 'price': 29.99}
            ]
        )
        logger.info(f"Order 1 created: {order1_id}")
        time.sleep(1)

        # Orden 2: Puede fallar (mucha cantidad)
        order2_id = service.create_order(
            customer_id='customer-002',
            items=[
                {'product_id': 'LAPTOP-001', 'quantity': 100, 'price': 999.99}
            ]
        )
        logger.info(f"Order 2 created: {order2_id}")
        time.sleep(1)

        # Orden 3: Producto existente
        order3_id = service.create_order(
            customer_id='customer-003',
            items=[
                {'product_id': 'KEYBOARD-001', 'quantity': 1, 'price': 79.99},
                {'product_id': 'MONITOR-001', 'quantity': 1, 'price': 299.99}
            ]
        )
        logger.info(f"Order 3 created: {order3_id}")

        logger.info("\n✅ Sample orders created. Run with 'processor' argument to process responses.")

        service.close()
