# Sistema E-Commerce con Kafka - Ejemplo Avanzado

Sistema completo de e-commerce implementado con microservicios y Apache Kafka, demostrando patrones avanzados de arquitectura distribuida.

## Descripción del Sistema

Este ejemplo implementa un sistema de comercio electrónico realista con 4 microservicios:

- **Order Service**: Gestiona la creación y ciclo de vida de órdenes
- **Inventory Service**: Controla inventario y reservas con compensating transactions
- **Notification Service**: Envía notificaciones con retry logic y Dead Letter Queue
- **Analytics Service**: Procesa eventos en tiempo real para generar métricas

## Arquitectura

```
┌─────────────┐
│   Cliente   │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Order Service                               │
│  • Crea órdenes                                                 │
│  • Event Sourcing + CQRS                                        │
│  • Transacciones Kafka                                          │
└───────┬─────────────────────────────────────────────────────────┘
        │
        │ Publica: orders.events (ORDER_CREATED)
        │ Envía: inventory.requests (RESERVE)
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Kafka Cluster                            │
│  Topics:                                                        │
│    • orders.events            (Eventos de órdenes)              │
│    • inventory.requests       (Solicitudes de inventario)       │
│    • inventory.responses      (Respuestas de inventario)        │
│    • inventory.events         (Eventos de inventario)           │
│    • notifications.requests   (Solicitudes de notificación)     │
│    • notifications.events     (Eventos de notificación)         │
│    • notifications.dlq        (Dead Letter Queue)               │
└───┬─────────┬─────────────┬─────────────┬───────────────────────┘
    │         │             │             │
    ▼         ▼             ▼             ▼
┌────────┐ ┌────────┐ ┌──────────┐ ┌──────────┐
│Inventory│ │ Order  │ │Notificat.│ │Analytics │
│Service  │ │Service │ │Service   │ │Service   │
└────────┘ └────────┘ └──────────┘ └──────────┘
```

## Patrones Implementados

### 1. Event Sourcing + CQRS
**Order Service** almacena todos los cambios de estado como eventos:
- `ORDER_CREATED`
- `ORDER_CONFIRMED`
- `ORDER_CANCELLED`

### 2. Saga Pattern (Orquestación)
**Flujo de creación de orden:**
```
1. Order Service → Crea orden (PENDING)
2. Order Service → Solicita reserva de inventario
3. Inventory Service → Verifica y reserva stock
4. Inventory Service → Responde (RESERVED o INSUFFICIENT_STOCK)
5. Order Service → Confirma o cancela orden
6. Notification Service → Notifica al cliente
```

### 3. Compensating Transactions
Si una orden falla después de reservar inventario, el sistema ejecuta rollback:
```python
# Inventario reservado pero pago falló
inventory_service.handle_rollback_request(order_id)
# -> Libera reserva automáticamente
```

### 4. Dead Letter Queue (DLQ)
Las notificaciones fallidas después de N reintentos van a DLQ:
```
notifications.requests → [Retry 1, 2, 3] → notifications.dlq
                              ↓
                         Intervención manual
```

### 5. Transaccionalidad en Kafka
Order Service usa transacciones para garantizar atomicidad:
```python
producer.begin_transaction()
# Múltiples escrituras
producer.send('orders.events', order_created)
producer.send('inventory.requests', reserve_request)
# Todo o nada
producer.commit_transaction()
```

### 6. Idempotencia
Configuración para evitar duplicados:
```python
enable_idempotence=True
max_in_flight_requests_per_connection=1
acks='all'
```

### 7. Stream Processing
Analytics Service procesa eventos en ventanas temporales:
- Agregación de métricas cada 5 minutos
- Cálculo de tasas de conversión
- Monitoreo de inventario en tiempo real

## Estructura del Proyecto

```
advanced-example/
├── services/                    # Microservicios
│   ├── order_service.py        # Servicio de órdenes
│   ├── inventory_service.py    # Servicio de inventario
│   ├── notification_service.py # Servicio de notificaciones
│   └── analytics_service.py    # Servicio de analytics
├── config/                      # Configuración
│   └── topics.json             # Definición de topics
├── schemas/                     # Schemas de eventos
│   └── events.json             # Estructura de mensajes
├── scripts/                     # Scripts de utilidad
│   ├── create_topics.py        # Creación de topics
│   └── run_demo.sh             # Demo automatizada
├── docker-compose.yml          # Orquestación de servicios
├── Dockerfile                  # Imagen de microservicios
├── Makefile                    # Comandos de gestión
├── requirements.txt            # Dependencias Python
└── README.md                   # Esta documentación
```

## Instalación y Ejecución

### Requisitos Previos

- Docker y Docker Compose
- Python 3.11+
- Make (opcional, para comandos simplificados)

### Inicio Rápido

```bash
# 1. Demo completa automatizada
make demo

# O manualmente:

# 2. Construir imágenes
make build

# 3. Levantar infraestructura
make up

# 4. Crear topics
make create-topics

# 5. Crear órdenes de prueba
make create-order

# 6. Ver logs en tiempo real
make logs-analytics
```

### Acceso a Interfaces

- **Kafka UI**: http://localhost:8080
  - Ver topics, mensajes, consumer groups
  - Explorar configuración del cluster

## Comandos Disponibles

```bash
make help              # Ver todos los comandos disponibles
make build             # Construir imágenes Docker
make up                # Levantar todos los servicios
make down              # Detener todos los servicios
make logs              # Ver logs de todos los servicios
make logs-order        # Ver logs del servicio de órdenes
make logs-inventory    # Ver logs del servicio de inventario
make logs-notification # Ver logs de notificaciones
make logs-analytics    # Ver logs de analytics
make status            # Ver estado de servicios
make create-topics     # Crear topics de Kafka
make list-topics       # Listar topics existentes
make create-order      # Crear orden de prueba
make kafka-ui          # Abrir Kafka UI
make health            # Verificar salud de servicios
make clean             # Limpiar todo (contenedores y volúmenes)
```

## Casos de Uso Implementados

### Caso 1: Orden Exitosa

```
1. Cliente crea orden con 2 productos
2. Order Service publica ORDER_CREATED
3. Order Service solicita reserva de inventario
4. Inventory Service verifica stock disponible
5. Inventory Service reserva productos
6. Inventory Service responde RESERVED
7. Order Service actualiza orden a CONFIRMED
8. Notification Service envía email de confirmación
9. Analytics Service registra venta exitosa
```

**Resultado**: Orden confirmada, inventario decrementado, cliente notificado

### Caso 2: Inventario Insuficiente

```
1. Cliente crea orden de 1000 laptops
2. Order Service publica ORDER_CREATED
3. Order Service solicita reserva de inventario
4. Inventory Service verifica stock (solo 50 disponibles)
5. Inventory Service responde INSUFFICIENT_STOCK
6. Order Service cancela orden
7. Notification Service envía email de cancelación
8. Analytics Service registra venta perdida
```

**Resultado**: Orden cancelada, inventario sin cambios, cliente notificado

### Caso 3: Fallo de Notificación

```
1. Orden confirmada exitosamente
2. Notification Service intenta enviar email
3. Servicio de email falla (timeout, API down, etc.)
4. Notification Service reintenta (backoff exponencial)
5. Después de 3 intentos fallidos
6. Mensaje enviado a Dead Letter Queue (DLQ)
7. Alerta generada para intervención manual
```

**Resultado**: Orden confirmada, notificación en DLQ para procesamiento manual

## Topics de Kafka

| Topic | Particiones | Retención | Compresión | Propósito |
|-------|-------------|-----------|------------|-----------|
| `orders.events` | 3 | 7 días | snappy | Eventos de órdenes |
| `inventory.requests` | 3 | 1 día | lz4 | Solicitudes de inventario |
| `inventory.responses` | 3 | 1 día | lz4 | Respuestas de inventario |
| `inventory.events` | 3 | 7 días | snappy | Cambios de inventario |
| `notifications.requests` | 3 | 2 días | gzip | Solicitudes de notificación |
| `notifications.events` | 3 | 7 días | snappy | Estado de notificaciones |
| `notifications.dlq` | 1 | 30 días | gzip | Notificaciones fallidas |

## Monitoreo y Observabilidad

### Logs de Servicios

Cada servicio genera logs estructurados con emojis para fácil identificación:

```bash
# Order Service
✅ Order created: abc-123 with 3 items
✅ Order confirmed: abc-123

# Inventory Service
📦 Inventory Service started
✅ Inventory reserved for order abc-123
⚠️  Insufficient inventory for order xyz-789

# Notification Service
📬 Processing notification 123
✅ Notification sent: 123
⚠️  Sent to DLQ: 456

# Analytics Service
📊 WINDOW REPORT
💰 Revenue: $1,234.56
📈 Conversion Rate: 85.2%
```

### Métricas en Analytics Service

El servicio de analytics genera reportes cada 5 minutos:

- **Órdenes**: Creadas, confirmadas, canceladas
- **Revenue**: Confirmado, pendiente, perdido
- **Tasa de Conversión**: Porcentaje de órdenes exitosas
- **Estado de Inventario**: Stock, reservado, disponible
- **Notificaciones**: Enviadas, fallidas, tasa de éxito
- **Eventos por Hora**: Distribución temporal de actividad

### Kafka UI

Accede a http://localhost:8080 para:

- Explorar mensajes en cada topic
- Ver consumer groups y lag
- Monitorear particiones y replicas
- Analizar throughput y latencia

## Configuración de Producción

### Replicación y Alta Disponibilidad

Para producción, ajusta estos parámetros:

```yaml
# docker-compose.yml
KAFKA_DEFAULT_REPLICATION_FACTOR: 3
KAFKA_MIN_INSYNC_REPLICAS: 2
KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 3
KAFKA_TRANSACTION_STATE_LOG_REPLICATION_FACTOR: 3
```

### Rendimiento

```yaml
# Aumentar particiones para paralelismo
KAFKA_NUM_PARTITIONS: 10

# Batch size para mejor throughput
KAFKA_PRODUCER_BATCH_SIZE: 32768
KAFKA_LINGER_MS: 10
```

### Retención de Datos

```json
// config/topics.json
{
  "retention.ms": "2592000000",  // 30 días
  "segment.ms": "86400000",       // 1 día por segmento
  "compression.type": "snappy"
}
```

## Pruebas

### Crear Orden Manualmente

```python
from services.order_service import OrderService

service = OrderService(['localhost:9092'])

order_id = service.create_order(
    customer_id='customer-123',
    items=[
        {'product_id': 'LAPTOP-001', 'quantity': 2, 'price': 999.99},
        {'product_id': 'MOUSE-001', 'quantity': 1, 'price': 29.99}
    ]
)

print(f"Order created: {order_id}")
```

### Probar Flujo Completo

```bash
# Terminal 1: Analytics
make logs-analytics

# Terminal 2: Crear orden
make create-order

# Terminal 3: Ver todos los logs
make logs
```

### Simular Fallos

```python
# notification_service.py
# Ajustar tasa de fallo
self.failure_rate = 0.8  # 80% de fallos
```

## Troubleshooting

### Kafka no inicia

```bash
# Verificar logs
make logs-kafka

# Limpiar volúmenes y reiniciar
make clean
make up
```

### Servicios no procesan mensajes

```bash
# Verificar consumer groups
docker exec adv-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --list

# Ver lag de consumer group
docker exec adv-kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --group order-service-group \
  --describe
```

### Topics no existen

```bash
# Listar topics
make list-topics

# Recrear topics
make create-topics
```

## Extensiones Futuras

- [ ] Integración con Schema Registry (Avro/Protobuf)
- [ ] Implementar Kafka Streams para procesamiento complejo
- [ ] Agregar autenticación y autorización (SASL/SSL)
- [ ] Métricas con Prometheus y Grafana
- [ ] Tracing distribuido con Jaeger
- [ ] API Gateway con validación de órdenes
- [ ] Base de datos real (PostgreSQL) para persistencia
- [ ] Circuit Breaker pattern para resiliencia
- [ ] Rate limiting para protección contra sobrecarga

## Recursos Adicionales

- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [Saga Pattern](https://microservices.io/patterns/data/saga.html)

## Licencia

Este proyecto es un ejemplo educativo de uso libre.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o PR para mejoras.

---

**Desarrollado como ejemplo avanzado de arquitectura de microservicios con Apache Kafka**
