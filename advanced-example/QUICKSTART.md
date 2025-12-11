# Quick Start Guide

Guía rápida para ejecutar el ejemplo avanzado de e-commerce con Kafka en 5 minutos.

## Inicio Rápido (1 comando)

```bash
cd advanced-example
make demo
```

Esto iniciará automáticamente:
- Kafka cluster
- Kafka UI (http://localhost:8080)
- 4 microservicios
- Creación de topics
- Órdenes de ejemplo

## Inicio Manual (Paso a Paso)

### 1. Pre-requisitos

```bash
# Verificar Docker
docker --version
# Docker version 20.10.x o superior

# Verificar Docker Compose
docker-compose --version
# docker-compose version 1.29.x o superior

# Verificar Python
python3 --version
# Python 3.11 o superior
```

### 2. Instalación

```bash
# Clonar repositorio (si aún no lo has hecho)
cd kafka-basic/advanced-example

# Instalar dependencias Python localmente (opcional)
pip install -r requirements.txt

# O usar un entorno virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows
pip install -r requirements.txt
```

### 3. Levantar Infraestructura

```bash
# Construir imágenes
make build

# Levantar Kafka y Zookeeper
make up

# Verificar que Kafka está listo
make health
# Debería mostrar: ✅ Kafka is healthy
```

### 4. Crear Topics

```bash
# Crear todos los topics configurados
make create-topics

# Verificar topics creados
make list-topics
```

**Output esperado:**
```
📋 Existing topics (7):
  - inventory.events
  - inventory.requests
  - inventory.responses
  - notifications.dlq
  - notifications.events
  - notifications.requests
  - orders.events
```

### 5. Acceder a Kafka UI

```bash
# Abrir en el navegador
make kafka-ui

# O manualmente: http://localhost:8080
```

En Kafka UI puedes:
- Ver todos los topics
- Explorar mensajes
- Monitorear consumer groups
- Ver configuración del cluster

### 6. Crear Órdenes de Prueba

```bash
# Crear 3 órdenes de ejemplo
make create-order
```

**Output esperado:**
```
📦 Creating sample orders...
✅ Order created: abc-123-456 with 2 items
✅ Order 1 created: abc-123-456
✅ Order 2 created: def-789-012
✅ Order 3 created: ghi-345-678
```

### 7. Ver Servicios en Acción

Abre múltiples terminales para ver los logs:

**Terminal 1 - Analytics (Métricas en tiempo real):**
```bash
make logs-analytics
```

**Terminal 2 - Order Service:**
```bash
make logs-order
```

**Terminal 3 - Inventory Service:**
```bash
make logs-inventory
```

**Terminal 4 - Notification Service:**
```bash
make logs-notification
```

O ver todos juntos:
```bash
make logs
```

## Qué Esperar

### 1. Order Service
```
✅ Order created: abc-123 with 2 items
✅ Order confirmed: abc-123
❌ Order cancelled: def-456 - Not enough stock
```

### 2. Inventory Service
```
📦 Inventory Service started
📊 Current inventory: {...}
✅ Inventory reserved for order abc-123
⚠️  Insufficient inventory for order def-456
```

### 3. Notification Service
```
📬 Processing notification notif-123
✅ Notification sent: notif-123
⚠️  Attempt 2 failed: Connection timeout
❌ Failed to send notification: notif-456
⚠️  Sent to DLQ: notif-456
```

### 4. Analytics Service
```
📊 WINDOW REPORT - 2025-12-11 12:00:00
======================================

📦 ORDERS:
  ORDER_CREATED: 3
  ORDER_CONFIRMED: 2
  ORDER_CANCELLED: 1

💰 REVENUE:
  Confirmed: $2,119.94
  Pending: $0.00
  Lost: $99,999.00
  Conversion Rate: 66.7%

📊 INVENTORY STATUS:
  LAPTOP-001:
    Stock: 48 | Reserved: 0 | Available: 48
  MOUSE-001:
    Stock: 198 | Reserved: 0 | Available: 198
```

## Explorar el Sistema

### Ver Mensajes en Kafka UI

1. Abre http://localhost:8080
2. Click en "Topics"
3. Selecciona "orders.events"
4. Click en "Messages"
5. Verás todos los eventos de órdenes

### Crear Orden Personalizada

```python
# En Python shell
from services.order_service import OrderService

service = OrderService(['localhost:9092'])

order_id = service.create_order(
    customer_id='mi-cliente-001',
    items=[
        {'product_id': 'LAPTOP-001', 'quantity': 1, 'price': 999.99},
        {'product_id': 'KEYBOARD-001', 'quantity': 1, 'price': 79.99}
    ]
)

print(f"Orden creada: {order_id}")
```

### Ver Consumer Groups

```bash
docker exec adv-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list
```

### Ver Lag de Procesamiento

```bash
docker exec adv-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group analytics-service-group \
  --describe
```

## Casos de Uso para Probar

### Caso 1: Orden Exitosa
```bash
# Ya cubierto en make create-order
# Resultado: Orden confirmada, inventario decrementado
```

### Caso 2: Inventario Insuficiente
```python
# Crear orden con cantidad muy alta
service.create_order(
    customer_id='test-002',
    items=[
        {'product_id': 'LAPTOP-001', 'quantity': 1000, 'price': 999.99}
    ]
)
# Resultado: Orden cancelada por falta de stock
```

### Caso 3: Simular Fallos de Notificación
```python
# Editar notification_service.py línea ~42
# Cambiar: self.failure_rate = 0.8  # 80% de fallos

# Reiniciar servicio
docker-compose restart notification-service

# Crear orden
make create-order

# Ver DLQ
make logs-notification
# Verás: "⚠️  Sent to DLQ: notif-xxx"
```

## Comandos Útiles

```bash
# Ver estado de todos los servicios
make status

# Verificar salud del sistema
make health

# Reiniciar un servicio específico
docker-compose restart order-service

# Ver logs de los últimos 5 minutos
docker-compose logs --since 5m

# Seguir logs de múltiples servicios
docker-compose logs -f order-service inventory-service

# Ver uso de recursos
docker stats

# Entrar a un contenedor
docker exec -it order-service bash
```

## Detener el Sistema

```bash
# Detener servicios (mantiene datos)
make stop

# Detener y eliminar todo (incluyendo volúmenes)
make clean
```

## Troubleshooting

### Problema: "Kafka is not healthy"
```bash
# Esperar más tiempo
sleep 30
make health

# Ver logs de Kafka
make logs-kafka

# Reiniciar
make down
make up
```

### Problema: "Topics not found"
```bash
# Recrear topics
make create-topics

# Verificar
make list-topics
```

### Problema: "Service not processing messages"
```bash
# Ver logs del servicio
make logs-order

# Verificar consumer groups
docker exec adv-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Reiniciar servicio
docker-compose restart order-service
```

### Problema: Puerto 8080 ya en uso
```bash
# Cambiar puerto en docker-compose.yml
# kafka-ui:
#   ports:
#     - "8081:8080"  # Usar 8081 en lugar de 8080

# Reiniciar
make restart
```

## Próximos Pasos

1. **Leer la arquitectura**: `cat ARCHITECTURE.md`
2. **Explorar código**: Revisar `services/` para entender implementación
3. **Modificar y experimentar**: Cambiar lógica de negocio
4. **Agregar features**: Nuevos servicios, eventos, patrones

## Recursos Adicionales

- README completo: `advanced-example/README.md`
- Arquitectura detallada: `advanced-example/ARCHITECTURE.md`
- Configuración de topics: `advanced-example/config/topics.json`
- Schemas de eventos: `advanced-example/schemas/events.json`

## ¿Necesitas Ayuda?

```bash
# Ver todos los comandos disponibles
make help
```

---

**Tiempo estimado de setup**: 5-10 minutos
**¡Disfruta explorando el sistema!** 🚀
