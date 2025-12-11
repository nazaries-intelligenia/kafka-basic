# Arquitectura del Sistema E-Commerce

## Visión General

Este documento describe en detalle la arquitectura, decisiones de diseño y patrones implementados en el sistema de e-commerce basado en Kafka.

## Principios de Diseño

### 1. Eventual Consistency
El sistema prioriza disponibilidad y tolerancia a particiones sobre consistencia inmediata (CAP Theorem).

### 2. Event-Driven Architecture
Todos los servicios se comunican mediante eventos asíncronos a través de Kafka.

### 3. Single Responsibility
Cada microservicio tiene una única responsabilidad bien definida.

### 4. Failure Resilience
El sistema está diseñado para manejar fallos de manera elegante con reintentos y compensación.

## Flujos de Datos Detallados

### Flujo 1: Creación Exitosa de Orden

```
┌──────────┐
│ Cliente  │
└────┬─────┘
     │ 1. POST /orders
     ▼
┌─────────────────┐
│ Order Service   │
│                 │
│ BEGIN TX        │ <── Transacción Kafka iniciada
│                 │
│ ├─ Crea orden  │ 2. Estado: PENDING
│ │   (en memoria)│    Total: $1,059.97
│ │               │
│ ├─ Publica     │ 3. → orders.events
│ │   ORDER_      │    Key: order_id
│ │   CREATED     │    Value: {order_data}
│ │               │
│ └─ Envía       │ 4. → inventory.requests
│     RESERVE     │    Key: order_id
│     request     │    Value: {items, action: RESERVE}
│                 │
│ COMMIT TX       │ <── Transacción confirmada
└─────────────────┘
     │
     │ Topic: inventory.requests
     ▼
┌─────────────────┐
│ Inventory Svc   │
│                 │
│ ├─ Consume     │ 5. Lee solicitud RESERVE
│ │   request     │
│ │               │
│ ├─ Verifica    │ 6. Stock disponible?
│ │   stock       │    LAPTOP-001: 50 > 1 ✓
│ │               │    MOUSE-001: 200 > 2 ✓
│ │               │
│ ├─ Reserva     │ 7. Incrementa 'reserved'
│ │   inventario  │    LAPTOP-001: reserved += 1
│ │               │    MOUSE-001: reserved += 2
│ │               │
│ ├─ Publica     │ 8. → inventory.responses
│ │   respuesta   │    Status: RESERVED
│ │               │
│ └─ Publica     │ 9. → inventory.events
│     evento      │    Event: INVENTORY_RESERVED
│                 │
│ COMMIT OFFSET   │ <── Offset confirmado
└─────────────────┘
     │
     │ Topic: inventory.responses
     ▼
┌─────────────────┐
│ Order Service   │
│ (processor)     │
│                 │
│ BEGIN TX        │
│                 │
│ ├─ Consume     │ 10. Lee respuesta RESERVED
│ │   response    │
│ │               │
│ ├─ Actualiza   │ 11. Estado: CONFIRMED
│ │   orden       │
│ │               │
│ ├─ Publica     │ 12. → orders.events
│ │   ORDER_      │     Event: ORDER_CONFIRMED
│ │   CONFIRMED   │
│ │               │
│ └─ Envía       │ 13. → notifications.requests
│     notificación│     Type: ORDER_CONFIRMED
│                 │
│ COMMIT TX       │
└─────────────────┘
     │
     │ Topic: notifications.requests
     ▼
┌─────────────────┐
│ Notification    │
│ Service         │
│                 │
│ ├─ Consume     │ 14. Lee solicitud
│ │   request     │
│ │               │
│ ├─ Intenta     │ 15. Envía email (attempt 1)
│ │   enviar      │     → Success!
│ │               │
│ ├─ Publica     │ 16. → notifications.events
│ │   evento      │     Event: NOTIFICATION_SENT
│ │               │
│ └─ COMMIT       │ 17. Confirma offset
│     OFFSET      │
└─────────────────┘
     │
     │ Topics: orders.events, inventory.events, notifications.events
     ▼
┌─────────────────┐
│ Analytics Svc   │ 18. Agrega métricas:
│                 │     • orders.created += 1
│                 │     • orders.confirmed += 1
│                 │     • revenue.confirmed += $1,059.97
│                 │     • notifications.sent += 1
└─────────────────┘
```

**Resultado Final:**
- ✅ Orden creada y confirmada
- ✅ Inventario reservado
- ✅ Cliente notificado
- ✅ Métricas actualizadas
- ✅ **Consistencia eventual alcanzada**

---

### Flujo 2: Orden Fallida (Inventario Insuficiente)

```
┌──────────┐
│ Cliente  │
└────┬─────┘
     │ 1. POST /orders (100 laptops)
     ▼
┌─────────────────┐
│ Order Service   │
│                 │
│ BEGIN TX        │
│ ├─ Crea orden  │ 2. Estado: PENDING
│ ├─ Publica     │ 3. → orders.events (ORDER_CREATED)
│ └─ Envía       │ 4. → inventory.requests (RESERVE 100 units)
│ COMMIT TX       │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Inventory Svc   │
│                 │
│ ├─ Consume     │ 5. Lee solicitud RESERVE
│ │               │
│ ├─ Verifica    │ 6. Stock disponible?
│ │   stock       │    LAPTOP-001: 50 < 100 ✗
│ │               │    ❌ INSUFICIENTE
│ │               │
│ ├─ NO reserva  │ 7. No modifica inventario
│ │               │
│ └─ Publica     │ 8. → inventory.responses
│     respuesta   │    Status: INSUFFICIENT_STOCK
│     NEGATIVA    │    Reason: "Not enough stock"
│                 │    Available: 50, Requested: 100
│ COMMIT OFFSET   │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Order Service   │
│ (processor)     │
│                 │
│ BEGIN TX        │
│                 │
│ ├─ Consume     │ 9. Lee respuesta INSUFFICIENT_STOCK
│ │   response    │
│ │               │
│ ├─ Cancela     │ 10. Estado: CANCELLED
│ │   orden       │     Reason: "Not enough stock"
│ │               │
│ ├─ Publica     │ 11. → orders.events
│ │   ORDER_      │     Event: ORDER_CANCELLED
│ │   CANCELLED   │
│ │               │
│ └─ Envía       │ 12. → notifications.requests
│     notificación│     Type: ORDER_CANCELLED
│                 │
│ COMMIT TX       │
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Notification    │
│ Service         │
│                 │
│ ├─ Envía       │ 13. Email: "Order cancelled:
│ │   email       │     Not enough stock"
│ │               │
│ └─ Publica     │ 14. → notifications.events
│     evento      │     Event: NOTIFICATION_SENT
└─────────────────┘
     │
     ▼
┌─────────────────┐
│ Analytics Svc   │ 15. Agrega métricas:
│                 │     • orders.created += 1
│                 │     • orders.cancelled += 1
│                 │     • revenue.lost += $99,999.00
│                 │     • cancellation_reasons["stock"] += 1
└─────────────────┘
```

**Resultado Final:**
- ✅ Orden cancelada gracefully
- ✅ Inventario sin cambios
- ✅ Cliente notificado del problema
- ✅ Métricas de pérdida registradas

---

### Flujo 3: Fallo de Notificación → Dead Letter Queue

```
┌─────────────────┐
│ Order Confirmed │ (Orden ya confirmada exitosamente)
└────────┬────────┘
         │
         │ notification.requests
         ▼
┌─────────────────────────────────────┐
│ Notification Service                │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Attempt 1                       │ │
│ │ ├─ Intenta enviar email         │ │ 1. Timeout (5s)
│ │ └─ ❌ Fallo: Connection timeout  │ │
│ │                                 │ │
│ │ ⏱️ Espera 2 segundos            │ │
│ │                                 │ │
│ │ Attempt 2                       │ │
│ │ ├─ Intenta enviar email         │ │ 2. Error 503
│ │ └─ ❌ Fallo: Service unavailable│ │
│ │                                 │ │
│ │ ⏱️ Espera 4 segundos (backoff)  │ │
│ │                                 │ │
│ │ Attempt 3                       │ │
│ │ ├─ Intenta enviar email         │ │ 3. Error 500
│ │ └─ ❌ Fallo: Internal server err│ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ❌ MAX_RETRIES alcanzado (3)        │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ Enviar a Dead Letter Queue      │ │
│ │                                 │ │
│ │ DLQ Message:                    │ │
│ │ {                               │ │
│ │   "original_notification": {...}│ │ 4. Mensaje original
│ │   "failure_timestamp": "...",   │ │    + metadata
│ │   "retry_count": 3,             │ │
│ │   "reason": "Max retries",      │ │
│ │   "last_error": "500 error"     │ │
│ │ }                               │ │
│ │                                 │ │
│ │ ↓ notifications.dlq             │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ├─ Publica evento                  │ │ 5. Analytics
│ │   NOTIFICATION_FAILED            │ │
│ │                                  │ │
│ └─ COMMIT OFFSET                   │ │ 6. Mensaje procesado
│    (mensaje manejado)              │ │    (no se reintenta)
└─────────────────────────────────────┘
         │
         │ notifications.dlq
         ▼
┌─────────────────────────────────────┐
│ DLQ Processor (Manual/Scheduled)    │
│                                     │
│ ├─ Lee mensajes de DLQ              │ 7. Revisión humana o
│ ├─ Analiza causa de fallo           │    procesamiento batch
│ ├─ Decide acción:                   │
│ │   • Reintentar con corrección     │ 8. Opciones:
│ │   • Alertar equipo ops            │    - Fix y reintento
│ │   • Descartar si no crítico       │    - Alert
│ │   • Usar canal alternativo (SMS)  │    - Fallback
│ └─ Archiva para auditoría           │
└─────────────────────────────────────┘
```

**Características del DLQ:**
- ✅ Evita bloqueo del consumer
- ✅ Preserva mensaje original
- ✅ Metadata de debugging
- ✅ Retención larga (30 días)
- ✅ Permite intervención manual
- ✅ No afecta órdenes confirmadas

---

## Garantías de Entrega

### At-Most-Once (No recomendado)
```python
producer.send(topic, message)
# No espera confirmación
# Puede perder mensajes
```

### At-Least-Once (Implementado)
```python
producer = KafkaProducer(
    acks='all',           # Espera todas las replicas
    retries=3,            # Reintenta en caso de fallo
    enable_idempotence=True  # Evita duplicados en retries
)
consumer = KafkaConsumer(
    enable_auto_commit=False  # Commit manual después de procesar
)
# Procesar mensaje
consumer.commit()  # Commit explícito
```

**Garantía**: Cada mensaje se procesa al menos una vez (puede duplicarse si falla después de procesar pero antes de commit)

### Exactly-Once (Con transacciones)
```python
producer = KafkaProducer(
    transactional_id='unique-id',
    enable_idempotence=True
)
producer.init_transactions()

producer.begin_transaction()
producer.send(topic, message)
consumer.send_offsets_to_transaction(offsets, group_id)
producer.commit_transaction()
```

**Garantía**: Cada mensaje se procesa exactamente una vez (dentro de la transacción)

---

## Particionamiento

### Estrategia por Order ID
```python
producer.send(
    'orders.events',
    key=order_id,  # Mismo order_id → misma partición
    value=order_data
)
```

**Ventajas**:
- Orden de eventos garantizado por orden
- Procesamiento paralelo de diferentes órdenes
- Sticky assignment de particiones

**Distribución con 3 particiones**:
```
order_id: abc-123 → hash(abc-123) % 3 = 0 → Partition 0
order_id: def-456 → hash(def-456) % 3 = 1 → Partition 1
order_id: ghi-789 → hash(ghi-789) % 3 = 2 → Partition 2
```

---

## Manejo de Fallos

### 1. Fallo de Kafka Broker
```
Scenario: Kafka broker se cae durante escritura

Order Service:
├─ begin_transaction()
├─ send() → ❌ Connection error
├─ Retry automático (max 3)
├─ Si falla: abort_transaction()
└─ Excepción propagada al cliente

Cliente recibe error 500
→ Reintentar petición
```

### 2. Fallo de Consumer
```
Scenario: Inventory Service se cae después de reservar pero antes de commit

1. Reserva inventario en memoria ✓
2. Envía respuesta a Kafka ✓
3. ❌ Crash antes de consumer.commit()

Al reiniciar:
4. Kafka reenvía mensaje (offset no confirmado)
5. Procesa nuevamente
6. Detecta reserva duplicada (idempotencia)
7. Reenvía respuesta (idempotente)
8. Commit exitoso
```

### 3. Fallo de Servicio Externo
```
Scenario: API de email está caída

Notification Service:
├─ Attempt 1: send_email() → Timeout (5s)
├─ Wait 2s (backoff)
├─ Attempt 2: send_email() → Error 503
├─ Wait 4s (exponential backoff)
├─ Attempt 3: send_email() → Error 500
└─ Send to DLQ (manual intervention)

Orden sigue confirmada ✓
Cliente puede consultar estado ✓
Notificación se reintentará manualmente
```

---

## Consideraciones de Producción

### Seguridad
```yaml
# Encryption
KAFKA_SECURITY_PROTOCOL: SASL_SSL
KAFKA_SASL_MECHANISM: SCRAM-SHA-512

# Authentication
KAFKA_SASL_USERNAME: order-service
KAFKA_SASL_PASSWORD: ${SECRET}

# Authorization (ACLs)
# order-service puede:
#   - WRITE a orders.events
#   - WRITE a inventory.requests
#   - READ de inventory.responses
```

### Monitoreo
```yaml
Métricas críticas:
  - Consumer Lag: < 1000 mensajes
  - Processing Time: p99 < 500ms
  - Error Rate: < 0.1%
  - DLQ Size: Alertar si > 10

Alertas:
  - Lag > 5000: PagerDuty Critical
  - DLQ > 50: Slack warning
  - Service down: PagerDuty Critical
```

### Escalabilidad
```
Single instance:
  - 100 orders/sec ✓
  - 1 partition/service

Scale to 1000 orders/sec:
  - 3 partitions
  - 3 instances/service
  - Load balancer

Scale to 10,000 orders/sec:
  - 10 partitions
  - 10 instances/service
  - Kubernetes HPA
  - Kafka Cluster (3+ brokers)
```

---

## Trade-offs y Decisiones

### ¿Por qué Kafka y no RabbitMQ?
**Kafka elegido por:**
- Event log persistente (replay events)
- Alta throughput (millones msg/sec)
- Built-in partitioning
- Event sourcing natural

**RabbitMQ mejor para:**
- Request-reply patterns
- Routing complejo
- Guaranteed delivery más simple

### ¿Por qué Event Sourcing?
**Ventajas:**
- Auditoría completa
- Debugging temporal (replay)
- CQRS natural
- Analytics históricas

**Desventajas:**
- Complejidad adicional
- Storage mayor
- Eventual consistency

### ¿Por qué Saga Orchestration?
**vs Choreography:**
- Control centralizado en Order Service
- Más fácil debuggear
- Compensación coordinada

**Trade-off:**
- Order Service es punto de acoplamiento
- En producción considerar Saga Orchestrator dedicado

---

## Próximos Pasos

1. **Schema Registry**: Evolución de schemas sin breaking changes
2. **Kafka Streams**: Agregaciones complejas en tiempo real
3. **Change Data Capture**: Sincronización con BD
4. **Multi-region**: Replicación geográfica
5. **GDPR Compliance**: Right to deletion (log compaction)

---

**Este documento evoluciona con el sistema. Mantener actualizado.**
