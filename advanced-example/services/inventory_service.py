"""
Inventory Service - Gestiona el inventario de productos
Patrón: Saga Pattern + Compensating Transactions
"""
import json
import time
from datetime import datetime
from typing import Dict, Optional
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InventoryService:
    def __init__(self, bootstrap_servers: list):
        self.bootstrap_servers = bootstrap_servers

        # Producer para respuestas
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            enable_idempotence=True
        )

        # Consumer para solicitudes de inventario
        self.consumer = KafkaConsumer(
            'inventory.requests',
            bootstrap_servers=bootstrap_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='inventory-service-group',
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            max_poll_records=10
        )

        # Inventario inicial (en producción sería una BD)
        self.inventory = {
            'LAPTOP-001': {'name': 'Gaming Laptop', 'stock': 50, 'reserved': 0},
            'MOUSE-001': {'name': 'Wireless Mouse', 'stock': 200, 'reserved': 0},
            'KEYBOARD-001': {'name': 'Mechanical Keyboard', 'stock': 150, 'reserved': 0},
            'MONITOR-001': {'name': '27" 4K Monitor', 'stock': 75, 'reserved': 0},
            'HEADSET-001': {'name': 'Gaming Headset', 'stock': 100, 'reserved': 0}
        }

        # Registro de reservas por orden
        self.reservations = {}

    def process_requests(self):
        """Procesar solicitudes de inventario"""
        logger.info("🔄 Listening for inventory requests...")
        logger.info(f"📊 Current inventory: {json.dumps(self.inventory, indent=2)}")

        try:
            for message in self.consumer:
                request = message.value
                action = request.get('action')
                order_id = request.get('order_id')

                logger.info(f"📥 Received request: {action} for order {order_id}")

                if action == 'RESERVE':
                    self._handle_reserve_request(request)
                elif action == 'COMMIT':
                    self._handle_commit_request(request)
                elif action == 'ROLLBACK':
                    self._handle_rollback_request(request)
                else:
                    logger.warning(f"⚠️  Unknown action: {action}")

                # Commit manual del offset
                self.consumer.commit()

        except KeyboardInterrupt:
            logger.info("🛑 Stopping inventory service...")
        finally:
            self.consumer.close()
            self.producer.close()

    def _handle_reserve_request(self, request: Dict):
        """Reservar inventario para una orden"""
        order_id = request['order_id']
        items = request['items']

        # Verificar disponibilidad
        can_reserve = True
        insufficient_items = []

        for item in items:
            product_id = item['product_id']
            quantity = item['quantity']

            if product_id not in self.inventory:
                can_reserve = False
                insufficient_items.append({
                    'product_id': product_id,
                    'reason': 'Product not found'
                })
                continue

            product = self.inventory[product_id]
            available = product['stock'] - product['reserved']

            if available < quantity:
                can_reserve = False
                insufficient_items.append({
                    'product_id': product_id,
                    'requested': quantity,
                    'available': available,
                    'reason': 'Insufficient stock'
                })

        if can_reserve:
            # Reservar inventario
            reserved_items = []
            for item in items:
                product_id = item['product_id']
                quantity = item['quantity']

                self.inventory[product_id]['reserved'] += quantity
                reserved_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'reserved_at': datetime.utcnow().isoformat()
                })

            self.reservations[order_id] = reserved_items

            # Enviar respuesta exitosa
            response = {
                'order_id': order_id,
                'request_id': request['request_id'],
                'status': 'RESERVED',
                'items': reserved_items,
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.info(f"✅ Inventory reserved for order {order_id}")

        else:
            # Enviar respuesta de fallo
            response = {
                'order_id': order_id,
                'request_id': request['request_id'],
                'status': 'INSUFFICIENT_STOCK',
                'insufficient_items': insufficient_items,
                'reason': 'Not enough stock available',
                'timestamp': datetime.utcnow().isoformat()
            }

            logger.warning(f"⚠️  Insufficient inventory for order {order_id}")

        # Publicar respuesta
        self.producer.send(
            'inventory.responses',
            key=order_id,
            value=response
        )
        self.producer.flush()

        # Publicar evento de inventario actualizado
        self._publish_inventory_event(order_id, 'RESERVED' if can_reserve else 'RESERVE_FAILED')

    def _handle_commit_request(self, request: Dict):
        """Confirmar reserva y decrementar stock real"""
        order_id = request['order_id']

        if order_id not in self.reservations:
            logger.warning(f"⚠️  No reservation found for order {order_id}")
            return

        # Confirmar reserva: restar del stock real
        for item in self.reservations[order_id]:
            product_id = item['product_id']
            quantity = item['quantity']

            self.inventory[product_id]['stock'] -= quantity
            self.inventory[product_id]['reserved'] -= quantity

        # Limpiar reserva
        del self.reservations[order_id]

        # Enviar confirmación
        response = {
            'order_id': order_id,
            'request_id': request['request_id'],
            'status': 'COMMITTED',
            'timestamp': datetime.utcnow().isoformat()
        }

        self.producer.send(
            'inventory.responses',
            key=order_id,
            value=response
        )
        self.producer.flush()

        self._publish_inventory_event(order_id, 'COMMITTED')
        logger.info(f"✅ Inventory committed for order {order_id}")

    def _handle_rollback_request(self, request: Dict):
        """Revertir reserva (compensating transaction)"""
        order_id = request['order_id']

        if order_id not in self.reservations:
            logger.warning(f"⚠️  No reservation found for order {order_id}")
            return

        # Revertir reserva
        for item in self.reservations[order_id]:
            product_id = item['product_id']
            quantity = item['quantity']

            self.inventory[product_id]['reserved'] -= quantity

        # Limpiar reserva
        del self.reservations[order_id]

        # Enviar confirmación
        response = {
            'order_id': order_id,
            'request_id': request['request_id'],
            'status': 'ROLLED_BACK',
            'timestamp': datetime.utcnow().isoformat()
        }

        self.producer.send(
            'inventory.responses',
            key=order_id,
            value=response
        )
        self.producer.flush()

        self._publish_inventory_event(order_id, 'ROLLED_BACK')
        logger.info(f"🔄 Inventory reservation rolled back for order {order_id}")

    def _publish_inventory_event(self, order_id: str, event_type: str):
        """Publicar evento de cambio de inventario para analytics"""
        event = {
            'event_type': f'INVENTORY_{event_type}',
            'order_id': order_id,
            'inventory_snapshot': {
                product_id: {
                    'stock': data['stock'],
                    'reserved': data['reserved'],
                    'available': data['stock'] - data['reserved']
                }
                for product_id, data in self.inventory.items()
            },
            'timestamp': datetime.utcnow().isoformat()
        }

        self.producer.send(
            'inventory.events',
            key=order_id,
            value=event
        )

    def get_inventory_status(self):
        """Obtener estado actual del inventario"""
        return {
            product_id: {
                'name': data['name'],
                'stock': data['stock'],
                'reserved': data['reserved'],
                'available': data['stock'] - data['reserved']
            }
            for product_id, data in self.inventory.items()
        }

    def close(self):
        """Cerrar conexiones"""
        self.producer.close()
        self.consumer.close()


if __name__ == '__main__':
    service = InventoryService(['localhost:9092'])

    logger.info("📦 Inventory Service started")
    logger.info("📊 Initial inventory:")
    for product_id, data in service.inventory.items():
        logger.info(f"  - {product_id}: {data['stock']} units ({data['name']})")

    service.process_requests()
