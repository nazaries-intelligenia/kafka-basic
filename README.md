# 🎓 Curso Básico de Apache Kafka con Python

Bienvenido al curso básico de Apache Kafka con Python. Este proyecto te enseñará los conceptos fundamentales de Kafka de forma práctica y didáctica.

## 📚 ¿Qué es Apache Kafka?

Apache Kafka es una plataforma de **streaming de datos distribuida** que permite:
- **Publicar y suscribirse** a flujos de mensajes (como un sistema de mensajería)
- **Almacenar** flujos de datos de forma duradera y confiable
- **Procesar** flujos de datos en tiempo real

### 🎯 Conceptos Clave

| Concepto | Descripción | Analogía |
|----------|-------------|----------|
| **Producer** | Aplicación que envía mensajes | Un periódico que publica noticias |
| **Consumer** | Aplicación que lee mensajes | Un suscriptor que lee el periódico |
| **Topic** | Canal o categoría de mensajes | Una sección del periódico (deportes, tecnología) |
| **Broker** | Servidor de Kafka que almacena mensajes | El distribuidor de periódicos |
| **Partition** | Subdivisión de un topic para escalabilidad | Diferentes ediciones regionales |
| **Offset** | Posición de lectura en una partición | Número de página donde dejaste de leer |

## 🏗️ Estructura del Proyecto

```
kafka-basic/
├── docker-compose.yml          # Configuración de Kafka, Zookeeper y UI
├── Makefile                    # Comandos útiles para gestionar el proyecto
├── requirements.txt            # Dependencias Python
│
├── producer.py                 # 📤 Productor básico (envía mensajes)
├── consumer.py                 # 📥 Consumidor básico (lee mensajes)
│
├── producer_avanzado.py        # 🚀 Productor con características avanzadas
├── consumer_avanzado.py        # 🎯 Consumidor con control manual y métricas
│
├── advanced-example/           # 🏢 Sistema completo de e-commerce
│   ├── services/               #    Microservicios (order, inventory, notification, analytics)
│   ├── config/                 #    Configuración de topics
│   ├── schemas/                #    Definición de eventos
│   ├── scripts/                #    Scripts de utilidad
│   ├── docker-compose.yml      #    Orquestación de servicios
│   ├── Makefile                #    Comandos para el ejemplo avanzado
│   ├── README.md               #    Documentación completa del ejemplo
│   ├── ARCHITECTURE.md         #    Arquitectura y patrones detallados
│   └── QUICKSTART.md           #    Guía de inicio rápido
│
└── README.md                   # Esta guía
```

## 🚀 Inicio Rápido

### Prerrequisitos

Asegúrate de tener instalado:
- **Docker** y **Docker Compose** (para ejecutar Kafka)
- **Python 3.7+** (para los scripts)
- **Make** (opcional, para comandos simplificados)

### Paso 1: Clonar o Descargar el Proyecto

```bash
cd kafka-presentacion
```

### Paso 2: Instalar Dependencias Python

```bash
# Con Make (recomendado)
make install

# Sin Make
pip install -r requirements.txt
```

### Paso 3: Iniciar Kafka

```bash
# Con Make (recomendado)
make start

# Sin Make
docker-compose up -d
```

Esto iniciará:
- **Zookeeper** en el puerto `2181`
- **Kafka Broker** en el puerto `9092`
- **Kafka UI** en `http://localhost:8080`

**¡Espera unos 10 segundos!** Kafka necesita un momento para inicializarse completamente.

### Paso 4: Verificar que Kafka Está Funcionando

```bash
# Ver el estado de los contenedores
make status

# Ver los logs
make logs
```

Deberías ver algo como:
```
NAME          IMAGE                               STATUS
kafka         confluentinc/cp-kafka:7.5.0         Up
zookeeper     confluentinc/cp-zookeeper:7.5.0     Up
kafka-ui      provectuslabs/kafka-ui:latest       Up
```

### Paso 5: Abrir Kafka UI (Interfaz Web)

Abre tu navegador en: **http://localhost:8080**

```bash
# Abre automáticamente el navegador
make ui
```

Esta interfaz te permite:
- Ver todos los topics
- Inspeccionar mensajes
- Monitorear el estado del cluster
- Ver consumidores y sus grupos

## 📖 Tutorial Paso a Paso

### 🎯 Ejemplo 1: Productor y Consumidor Básicos

Este ejemplo te enseñará lo más fundamental de Kafka.

#### 1.1 Ejecutar el Productor

Abre una terminal y ejecuta:

```bash
make producer
# o
python3 producer.py
```

**¿Qué hace?**
- Se conecta al broker de Kafka en `localhost:9092`
- Crea automáticamente un topic llamado `mensajes-curso`
- Envía 10 mensajes de ejemplo con datos JSON
- Muestra información de confirmación de cada mensaje

**Salida esperada:**
```
============================================================
🚀 PRODUCTOR DE KAFKA - INICIANDO
============================================================

✓ Productor creado exitosamente
📍 Conectado a: localhost:9092

============================================================
📤 ENVIANDO MENSAJES AL TOPIC: 'mensajes-curso'
============================================================

[1/10] Enviando mensaje 1...
✓ Mensaje enviado correctamente
  Topic: mensajes-curso
  Partición: 0
  Offset: 0
  Contenido: {'id': 1, 'tipo': 'mensaje_ejemplo', ...}
```

#### 1.2 Ver los Mensajes en Kafka UI

1. Abre **http://localhost:8080**
2. Haz clic en **Topics**
3. Busca **mensajes-curso**
4. Haz clic en **Messages** para ver los mensajes

#### 1.3 Ejecutar el Consumidor

Abre **otra terminal** (deja la del productor abierta) y ejecuta:

```bash
make consumer
# o
python3 consumer.py
```

**¿Qué hace?**
- Se conecta al mismo broker
- Se suscribe al topic `mensajes-curso`
- Lee todos los mensajes desde el principio
- Muestra cada mensaje con formato legible

**Salida esperada:**
```
============================================================
📥 CONSUMIDOR DE KAFKA - INICIANDO
============================================================

✓ Consumidor creado exitosamente
📍 Conectado a: localhost:9092
📌 Group ID: grupo-curso-basico
📖 Topic: mensajes-curso

============================================================
👂 ESCUCHANDO MENSAJES DEL TOPIC: 'mensajes-curso'
============================================================

[Mensaje #1]
────────────────────────────────────────────────────────────
✓ NUEVO MENSAJE RECIBIDO
────────────────────────────────────────────────────────────
📌 Metadatos:
   • Topic: mensajes-curso
   • Partición: 0
   • Offset: 0
```

### 🚀 Ejemplo 2: Productor Avanzado

El productor avanzado incluye características más sofisticadas.

```bash
make producer-avanzado
# o
python3 producer_avanzado.py
```

**Características avanzadas:**

1. **Claves de Particionamiento**: Los mensajes con la misma clave van a la misma partición
2. **Callbacks**: Manejo de éxitos y errores de forma asíncrona
3. **Compresión**: Los mensajes se comprimen con gzip
4. **Envío en Batch**: Múltiples mensajes se envían juntos para mejor rendimiento
5. **Métricas**: Estadísticas de envío en tiempo real

**Ejemplos incluidos:**
- Simulación de sensores IoT (cada sensor tiene su propia clave)
- Envío en batch de 50 mensajes para alta performance

### 🎯 Ejemplo 3: Consumidor Avanzado

El consumidor avanzado te da control total sobre el procesamiento.

```bash
make consumer-avanzado
# o
python3 consumer_avanzado.py
```

**Características avanzadas:**

1. **Commit Manual**: Tú decides cuándo guardar el progreso de lectura
2. **Rebalanceo**: Manejo de cuando se agregan/quitan consumidores del grupo
3. **Particiones Específicas**: Leer solo ciertas particiones
4. **Métricas**: Estadísticas detalladas de procesamiento
5. **Manejo de Errores**: Reintentos y recuperación ante fallos

### 🧪 Ejemplo 4: Test Rápido

Para probar que todo funciona correctamente:

```bash
make test
```

Este comando:
1. Envía 5 mensajes de prueba a `test-topic`
2. Los lee inmediatamente
3. Muestra los resultados

## 🎮 Comandos Disponibles (Makefile)

### Comandos Principales

| Comando | Descripción |
|---------|-------------|
| `make help` | Muestra todos los comandos disponibles |
| `make install` | Instala las dependencias Python |
| `make start` | Inicia Kafka, Zookeeper y Kafka UI |
| `make stop` | Detiene todos los contenedores (sin eliminarlos) |
| `make down` | Detiene y elimina contenedores (mantiene datos en volúmenes) |
| `make restart` | Reinicia rápidamente los contenedores existentes |
| `make restart-full` | Reinicio completo: detiene, elimina y reinicia desde cero |
| `make status` | Muestra el estado de los contenedores |
| `make logs` | Muestra los logs de todos los servicios |
| `make clean` | Detiene y elimina todo incluyendo volúmenes (¡cuidado, borra datos!) |

### Comandos de Producción/Consumo

| Comando | Descripción |
|---------|-------------|
| `make producer` | Ejecuta el productor básico |
| `make consumer` | Ejecuta el consumidor básico |
| `make producer-avanzado` | Ejecuta el productor avanzado |
| `make consumer-avanzado` | Ejecuta el consumidor avanzado |
| `make test` | Ejecuta un test rápido de envío/recepción |

### Comandos de Gestión de Topics

| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `make list-topics` | Lista todos los topics | `make list-topics` |
| `make create-topic` | Crea un topic nuevo | `make create-topic TOPIC=mi-topic` |
| `make describe-topic` | Muestra info de un topic | `make describe-topic TOPIC=mi-topic` |
| `make delete-topic` | Elimina un topic | `make delete-topic TOPIC=mi-topic` |

### Comandos de Interfaz

| Comando | Descripción |
|---------|-------------|
| `make ui` | Abre Kafka UI en el navegador |
| `make shell-kafka` | Abre una shell en el contenedor de Kafka |
| `make shell-zookeeper` | Abre una shell en Zookeeper |

## 🔬 Ejercicios Prácticos

### Ejercicio 1: Tu Primer Productor

Modifica `producer.py` para enviar mensajes personalizados:

```python
mensaje = {
    'id': i,
    'tu_nombre': 'Juan',
    'mensaje': f'Mi mensaje personalizado {i}',
    'fecha': datetime.now().isoformat()
}
```

### Ejercicio 2: Crear un Nuevo Topic

```bash
# Crea un topic llamado "ejercicios"
make create-topic TOPIC=ejercicios

# Verifica que se creó
make list-topics

# Describe el topic
make describe-topic TOPIC=ejercicios
```

### Ejercicio 3: Múltiples Consumidores

Abre **3 terminales** diferentes:

**Terminal 1:**
```bash
python3 producer.py
```

**Terminal 2:**
```bash
python3 consumer.py
```

**Terminal 3:**
```bash
python3 consumer.py
```

**¿Qué observas?**
- Los dos consumidores están en el mismo grupo (`grupo-curso-basico`)
- Kafka reparte los mensajes entre ellos
- Cada mensaje lo procesa **solo un consumidor del grupo**

### Ejercicio 4: Consumer Groups Diferentes

Modifica `consumer.py` para cambiar el `group_id`:

```python
consumer = KafkaConsumer(
    topic_name,
    bootstrap_servers=['localhost:9092'],
    group_id='mi-grupo-nuevo',  # ← Cambia esto
    # ... resto de configuración
)
```

Ahora ejecuta el consumidor. ¿Qué pasa? ¡Lee desde el principio porque es un grupo nuevo!

### Ejercicio 5: Simular Sensores IoT

```bash
python3 producer_avanzado.py
# Selecciona opción 1

# En otra terminal
python3 consumer_avanzado.py
# Selecciona opción 1
```

Observa cómo los mensajes del mismo sensor siempre van a la misma partición.

## 🔧 Gestión de Servicios

### Cuándo usar cada comando

#### `make stop` - Pausa temporal
Usa este comando cuando:
- Quieres liberar recursos temporalmente
- Vas a volver a trabajar pronto
- No quieres perder el estado actual

```bash
make stop
# Los contenedores se detienen pero no se eliminan
# Para reanudar: make start
```

#### `make down` - Limpieza de contenedores
Usa este comando cuando:
- Has terminado de trabajar por hoy
- Quieres limpiar contenedores pero mantener los datos
- Necesitas liberar puertos para otros proyectos

```bash
make down
# Elimina contenedores pero mantiene los volúmenes con datos
# Para reiniciar: make start
```

#### `make restart` - Reinicio rápido
Usa este comando cuando:
- Kafka está lento o no responde
- Has cambiado alguna configuración menor
- Quieres aplicar cambios sin perder datos

```bash
make restart
# Reinicia rápidamente sin reconstruir
```

#### `make restart-full` - Reinicio completo
Usa este comando cuando:
- Has actualizado docker-compose.yml
- Kafka está en un estado corrupto
- Quieres asegurarte de empezar limpio (manteniendo datos)

```bash
make restart-full
# Equivalente a: make down && make start
# Reconstruye todo desde cero pero mantiene los volúmenes
```

#### `make clean` - Borrado completo
⚠️ **CUIDADO**: Este comando elimina TODOS los datos

Usa este comando cuando:
- Quieres empezar completamente desde cero
- Tienes problemas graves de corrupción
- Estás haciendo pruebas y quieres resetear todo

```bash
make clean
# Elimina contenedores Y volúmenes (pierdes todos los mensajes)
# Para reiniciar limpio: make start
```

### Flujo de trabajo típico

**Inicio del día:**
```bash
make start          # Inicia todo
make status         # Verifica que todo esté corriendo
```

**Durante el desarrollo:**
```bash
make logs           # Revisa logs si algo falla
make restart        # Reinicia si Kafka se pone lento
make list-topics    # Ve qué topics tienes
```

**Fin del día:**
```bash
make down           # Detiene y limpia contenedores (mantiene datos)
# o
make stop           # Solo detiene (más rápido al día siguiente)
```

**Si algo va mal:**
```bash
make logs           # Primero revisa qué pasó
make restart-full   # Reinicio completo si es necesario
# o en casos extremos:
make clean && make start  # Borra todo y empieza desde cero
```

## 🐛 Resolución de Problemas

### Problema: "No se pudo conectar a Kafka"

**Solución:**
```bash
# Verifica que Kafka esté corriendo
make status

# Si no está corriendo, inícialo
make start

# Espera 10 segundos y revisa los logs
make logs
```

### Problema: "Connection refused" en localhost:9092

**Posibles causas:**
1. Kafka no ha terminado de iniciar (espera 10-15 segundos)
2. El puerto 9092 está ocupado por otra aplicación
3. Docker no está corriendo

**Solución:**
```bash
# Verifica que Docker esté corriendo
docker ps

# Reinicia Kafka completamente
make restart-full

# O si el problema persiste, reinicia desde cero
make clean
make start
```

### Problema: Los consumidores no ven mensajes antiguos

**Explicación:** Por defecto, cuando creas un nuevo consumer group, empieza a leer desde el último mensaje.

**Solución:** Cambia `auto_offset_reset`:
```python
auto_offset_reset='earliest'  # Lee desde el principio
# o
auto_offset_reset='latest'    # Lee solo mensajes nuevos
```

### Problema: "Topic does not exist"

Kafka crea topics automáticamente, pero si está deshabilitado:

```bash
make create-topic TOPIC=nombre-del-topic
```

### Problema: Quiero empezar desde cero

```bash
# Detiene y elimina TODO (incluidos datos)
make clean

# Inicia de nuevo
make start
```

## 📊 Arquitectura del Proyecto

```
┌─────────────────────────────────────────────────────────┐
│                     TU MÁQUINA                          │
│                                                          │
│  ┌──────────────┐                   ┌──────────────┐   │
│  │  producer.py │──────────┐   ┌───│  consumer.py │   │
│  └──────────────┘          │   │    └──────────────┘   │
│                            ▼   ▼                        │
│                       ┌─────────────┐                   │
│                       │   Kafka     │                   │
│                       │  (puerto    │                   │
│                       │   9092)     │                   │
│                       └─────────────┘                   │
│                             ▲                           │
│                             │                           │
│                       ┌─────────────┐                   │
│                       │  Zookeeper  │                   │
│                       │  (puerto    │                   │
│                       │   2181)     │                   │
│                       └─────────────┘                   │
│                                                          │
│                       ┌─────────────┐                   │
│  Navegador Web ───────│  Kafka UI   │                   │
│  (localhost:8080)     │             │                   │
│                       └─────────────┘                   │
└─────────────────────────────────────────────────────────┘
```

## 📖 Conceptos Importantes Explicados

### ¿Qué es un Offset?

Un **offset** es como un marcador de libro. Es un número que indica qué mensaje has leído hasta ahora.

```
Topic: mensajes-curso
Partición 0: [msg0] [msg1] [msg2] [msg3] [msg4]
Offset:        0      1      2      3      4
                                    ↑
                            Tu posición actual
```

### ¿Qué es un Consumer Group?

Un **consumer group** es un conjunto de consumidores que trabajan juntos para procesar mensajes.

**Ventajas:**
- **Escalabilidad**: Puedes agregar más consumidores para procesar más rápido
- **Paralelismo**: Cada consumidor procesa diferentes mensajes
- **Tolerancia a fallos**: Si un consumidor falla, los otros continúan

```
Producer ──► [msg1, msg2, msg3, msg4, msg5, msg6]
                    │
                    ▼
            Consumer Group: "mi-grupo"
            ┌─────────────────────────┐
            │  Consumer A  │ Consumer B │
            │  [msg1,msg3] │ [msg2,msg4]│
            │  [msg5]      │ [msg6]     │
            └─────────────────────────┘
```

### ¿Qué son las Particiones?

Las **particiones** dividen un topic en múltiples "colas" paralelas.

**Beneficios:**
- **Paralelismo**: Múltiples consumidores pueden leer en paralelo
- **Orden garantizado**: Dentro de cada partición, el orden se mantiene
- **Escalabilidad**: Puedes tener más particiones que consumidores

```
Topic: "sensores"

Partición 0: [sensor-1] [sensor-1] [sensor-1]  ───► Consumer A
Partición 1: [sensor-2] [sensor-2] [sensor-2]  ───► Consumer B
Partición 2: [sensor-3] [sensor-3] [sensor-3]  ───► Consumer C
```

## 🎓 Siguientes Pasos

Una vez domines estos ejemplos básicos, puedes explorar:

1. **Kafka Streams**: Procesamiento de flujos de datos en tiempo real
2. **Kafka Connect**: Integración con bases de datos y otros sistemas
3. **Schema Registry**: Validación y evolución de esquemas de datos
4. **KSQL**: SQL para datos en streaming
5. **Producción**: Configuración de clusters multi-broker, replicación, seguridad

## 📚 Recursos Adicionales

- [Documentación Oficial de Kafka](https://kafka.apache.org/documentation/)
- [kafka-python Docs](https://kafka-python.readthedocs.io/)
- [Kafka: The Definitive Guide (libro)](https://www.confluent.io/resources/kafka-the-definitive-guide/)

## 🤝 Contribuir

Si encuentras errores o tienes sugerencias:
1. Abre un issue
2. Envía un pull request
3. Comparte este proyecto con otros estudiantes

## 📝 Licencia

Este proyecto es de código abierto y está disponible para fines educativos.

---

## 🚀 Ejemplo Avanzado: Sistema E-Commerce

Una vez que domines los conceptos básicos, explora nuestro **ejemplo avanzado completo** que implementa un sistema realista de e-commerce con microservicios:

```bash
cd advanced-example
make demo
```

**Características del ejemplo avanzado:**
- 4 microservicios (Order, Inventory, Notification, Analytics)
- Patrones avanzados: Event Sourcing, Saga Pattern, CQRS
- Transacciones Kafka y garantías exactly-once
- Dead Letter Queue (DLQ) para manejo de fallos
- Stream processing con ventanas temporales
- Docker Compose completo con Kafka UI
- Documentación detallada y guía de arquitectura

**Documentación completa:** [`advanced-example/README.md`](./advanced-example/README.md)

---

## 🎉 ¡Felicidades!

Has completado la configuración del curso de Kafka. Ahora estás listo para:
- Enviar tus primeros mensajes
- Crear consumidores que procesen datos en tiempo real
- Construir aplicaciones distribuidas y escalables
- Explorar el ejemplo avanzado de microservicios

**¡Buena suerte en tu viaje con Apache Kafka!** 🚀

---

**¿Tienes preguntas?** Revisa la sección de resolución de problemas o explora los comentarios detallados en cada archivo Python.
