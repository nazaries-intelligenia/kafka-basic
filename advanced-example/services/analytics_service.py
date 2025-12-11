"""
Analytics Service - Procesa eventos para generar métricas y reportes
Patrón: Stream Processing + Windowing
"""
import json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import defaultdict
from kafka import KafkaConsumer
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, bootstrap_servers: list):
        self.bootstrap_servers = bootstrap_servers

        # Consumer para múltiples topics (fan-in pattern)
        self.consumer = KafkaConsumer(
            'orders.events',
            'inventory.events',
            'notifications.events',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='analytics-service-group',
            auto_offset_reset='earliest',
            enable_auto_commit=True
        )

        # Métricas en memoria (en producción sería una BD analítica)
        self.metrics = {
            'orders': defaultdict(int),
            'revenue': defaultdict(float),
            'inventory': defaultdict(dict),
            'notifications': defaultdict(int),
            'events_by_hour': defaultdict(int)
        }

        # Ventana de tiempo para agregaciones
        self.window_size = timedelta(minutes=5)
        self.current_window_start = datetime.utcnow()

    def process_events(self):
        """Procesar eventos de múltiples topics para analytics"""
        logger.info("📊 Starting Analytics Service...")
        logger.info("📡 Listening to: orders.events, inventory.events, notifications.events")

        try:
            for message in self.consumer:
                event = message.value
                topic = message.topic
                event_type = event.get('event_type')

                # Procesar según el topic
                if topic == 'orders.events':
                    self._process_order_event(event)
                elif topic == 'inventory.events':
                    self._process_inventory_event(event)
                elif topic == 'notifications.events':
                    self._process_notification_event(event)

                # Verificar si debemos cerrar la ventana temporal
                self._check_window()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping analytics service...")
            self._print_final_report()
        finally:
            self.consumer.close()

    def _process_order_event(self, event: Dict):
        """Procesar eventos de órdenes"""
        event_type = event['event_type']
        order_data = event.get('data', {})
        order_id = event.get('order_id')

        # Contadores por tipo de evento
        self.metrics['orders'][event_type] += 1

        if event_type == 'ORDER_CREATED':
            total = order_data.get('total', 0)
            self.metrics['revenue']['pending'] += total

            logger.info(f"📈 Order Created: {order_id} - ${total:.2f}")

        elif event_type == 'ORDER_CONFIRMED':
            total = order_data.get('total', 0)
            self.metrics['revenue']['pending'] -= total
            self.metrics['revenue']['confirmed'] += total

            logger.info(f"✅ Order Confirmed: {order_id} - ${total:.2f}")

        elif event_type == 'ORDER_CANCELLED':
            total = order_data.get('total', 0)
            self.metrics['revenue']['pending'] -= total
            self.metrics['revenue']['lost'] += total

            reason = event.get('reason', 'Unknown')
            logger.info(f"❌ Order Cancelled: {order_id} - ${total:.2f} ({reason})")

        # Registrar en ventana temporal
        hour = datetime.utcnow().hour
        self.metrics['events_by_hour'][hour] += 1

    def _process_inventory_event(self, event: Dict):
        """Procesar eventos de inventario"""
        event_type = event['event_type']
        order_id = event.get('order_id')
        snapshot = event.get('inventory_snapshot', {})

        # Actualizar snapshot de inventario
        self.metrics['inventory'] = snapshot

        logger.info(f"📦 Inventory Update: {event_type} for order {order_id}")

        # Calcular métricas de inventario
        total_stock = sum(p['stock'] for p in snapshot.values())
        total_reserved = sum(p['reserved'] for p in snapshot.values())
        total_available = sum(p['available'] for p in snapshot.values())

        logger.info(f"   Total Stock: {total_stock} | Reserved: {total_reserved} | Available: {total_available}")

    def _process_notification_event(self, event: Dict):
        """Procesar eventos de notificaciones"""
        event_type = event['event_type']
        notification_id = event.get('notification_id')
        channel = event.get('channel', 'unknown')

        # Contadores por tipo y canal
        self.metrics['notifications'][event_type] += 1
        self.metrics['notifications'][f'{event_type}_{channel}'] += 1

        status = '✅' if event_type == 'NOTIFICATION_SENT' else '❌'
        logger.info(f"{status} Notification {event_type}: {notification_id} via {channel}")

    def _check_window(self):
        """Verificar si debemos cerrar la ventana temporal y generar reporte"""
        now = datetime.utcnow()
        if now - self.current_window_start >= self.window_size:
            self._generate_window_report()
            self.current_window_start = now

    def _generate_window_report(self):
        """Generar reporte de la ventana temporal"""
        logger.info("\n" + "="*70)
        logger.info(f"📊 WINDOW REPORT - {self.current_window_start.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("="*70)

        # Órdenes
        logger.info("\n📦 ORDERS:")
        for event_type, count in self.metrics['orders'].items():
            logger.info(f"  {event_type}: {count}")

        # Revenue
        logger.info("\n💰 REVENUE:")
        confirmed = self.metrics['revenue'].get('confirmed', 0)
        pending = self.metrics['revenue'].get('pending', 0)
        lost = self.metrics['revenue'].get('lost', 0)
        total = confirmed + pending + lost

        logger.info(f"  Confirmed: ${confirmed:,.2f}")
        logger.info(f"  Pending: ${pending:,.2f}")
        logger.info(f"  Lost: ${lost:,.2f}")
        logger.info(f"  Total Processed: ${total:,.2f}")

        if total > 0:
            conversion_rate = (confirmed / total) * 100
            logger.info(f"  Conversion Rate: {conversion_rate:.1f}%")

        # Inventario
        logger.info("\n📊 INVENTORY STATUS:")
        if self.metrics['inventory']:
            for product_id, data in sorted(self.metrics['inventory'].items()):
                logger.info(f"  {product_id}:")
                logger.info(f"    Stock: {data['stock']} | Reserved: {data['reserved']} | Available: {data['available']}")
        else:
            logger.info("  No inventory data")

        # Notificaciones
        logger.info("\n🔔 NOTIFICATIONS:")
        sent = self.metrics['notifications'].get('NOTIFICATION_SENT', 0)
        failed = self.metrics['notifications'].get('NOTIFICATION_FAILED', 0)
        total_notif = sent + failed

        if total_notif > 0:
            success_rate = (sent / total_notif) * 100
            logger.info(f"  Sent: {sent}")
            logger.info(f"  Failed: {failed}")
            logger.info(f"  Success Rate: {success_rate:.1f}%")
        else:
            logger.info("  No notifications processed")

        logger.info("\n" + "="*70 + "\n")

    def _print_final_report(self):
        """Imprimir reporte final al cerrar el servicio"""
        self._generate_window_report()

        logger.info("\n" + "="*70)
        logger.info("📊 FINAL ANALYTICS REPORT")
        logger.info("="*70)

        # Eventos por hora
        logger.info("\n⏰ EVENTS BY HOUR:")
        for hour in sorted(self.metrics['events_by_hour'].keys()):
            count = self.metrics['events_by_hour'][hour]
            bar = '█' * (count // 5)  # Escala visual
            logger.info(f"  {hour:02d}:00 - {count:3d} events {bar}")

        logger.info("\n" + "="*70)

    def get_metrics_summary(self) -> Dict:
        """Obtener resumen de métricas"""
        return {
            'orders': dict(self.metrics['orders']),
            'revenue': dict(self.metrics['revenue']),
            'inventory': dict(self.metrics['inventory']),
            'notifications': dict(self.metrics['notifications']),
            'events_by_hour': dict(self.metrics['events_by_hour'])
        }

    def close(self):
        """Cerrar conexiones"""
        self.consumer.close()


if __name__ == '__main__':
    service = AnalyticsService(['localhost:9092'])
    service.process_events()
