# Descripción para GitHub

## 📝 Descripción Corta (para la descripción del repositorio)

```
Curso básico de Apache Kafka con Python - Ejemplos prácticos con Docker, productores, consumidores y Kafka UI. Perfecto para aprender Kafka desde cero con código muy comentado y guía paso a paso.
```

## 🏷️ Topics/Tags Sugeridos

```
kafka
apache-kafka
python
docker
docker-compose
kafka-python
tutorial
curso
spanish
kafka-tutorial
message-queue
streaming
producers
consumers
kafka-ui
ejemplos
didactico
educational
```

## 📋 Descripción Completa (para README principal)

```markdown
# 🎓 Curso Básico de Apache Kafka con Python

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![Kafka](https://img.shields.io/badge/Kafka-7.5.0-black.svg)](https://kafka.apache.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docs.docker.com/compose/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Aprende Apache Kafka desde cero con ejemplos prácticos, código muy comentado y una guía paso a paso en español.

## ✨ Características

- 🐳 **Docker Compose** - Kafka, Zookeeper y Kafka UI preconfigurados
- 🎯 **Ejemplos Progresivos** - Desde básico hasta avanzado
- 📝 **Código Comentado** - Cada línea explicada en español
- 🛠️ **Makefile** - Comandos simples para gestionar el proyecto
- 🎨 **Interfaz Web** - Kafka UI para visualizar topics y mensajes
- 📚 **Guía Completa** - Tutorial paso a paso con ejercicios prácticos
- 🚀 **Listo para Usar** - Solo necesitas Docker y Python

## 🚀 Inicio Rápido

```bash
# 1. Clonar el repositorio
git clone https://github.com/TU_USUARIO/kafka-presentacion.git
cd kafka-presentacion

# 2. Instalar dependencias Python
make install

# 3. Iniciar Kafka
make start

# 4. Ejecutar el productor (en una terminal)
make producer

# 5. Ejecutar el consumidor (en otra terminal)
make consumer

# 6. Abrir Kafka UI en el navegador
make ui
```

## 📖 Contenido del Curso

### Ejemplos Básicos
- **producer.py** - Envía mensajes a Kafka
- **consumer.py** - Lee mensajes de Kafka

### Ejemplos Avanzados
- **producer_avanzado.py** - Claves, callbacks, compresión, métricas
- **consumer_avanzado.py** - Commits manuales, rebalanceo, particiones específicas

## 🎯 ¿Qué Aprenderás?

- Conceptos fundamentales de Kafka (Topics, Producers, Consumers, Partitions, Offsets)
- Cómo enviar y recibir mensajes
- Consumer Groups y paralelismo
- Particionamiento y claves
- Manejo de offsets y commits
- Callbacks y procesamiento asíncrono
- Métricas y monitoreo

## 📋 Requisitos

- Docker y Docker Compose
- Python 3.7+
- Make (opcional pero recomendado)

## 🛠️ Comandos Disponibles

```bash
make help              # Ver todos los comandos
make start             # Iniciar Kafka
make stop              # Detener Kafka
make producer          # Ejecutar productor
make consumer          # Ejecutar consumidor
make test              # Test rápido
make list-topics       # Listar topics
make ui                # Abrir Kafka UI
```

## 📚 Documentación

Consulta el [README completo](README.md) para:
- Tutorial paso a paso
- Explicación de conceptos
- Ejercicios prácticos
- Resolución de problemas
- Diagramas y ejemplos

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:
1. Haz fork del proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es de código abierto y está disponible bajo la Licencia MIT.

## 👨‍💻 Autor

Rafael López Molina - [@Rlopezmolina](https://x.com/Rlopezmolina)

## ⭐ ¿Te Gusta el Proyecto?

Si este proyecto te ha sido útil, ¡dale una estrella! ⭐

## 📧 Contacto

¿Preguntas? Abre un [issue](https://github.com/TU_USUARIO/kafka-presentacion/issues)