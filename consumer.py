#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONSUMIDOR BÁSICO DE KAFKA
===========================
Este script lee mensajes de un topic de Kafka.
Un consumidor es quien RECIBE y PROCESA mensajes del broker de Kafka.

Conceptos clave:
- Consumer: La aplicación que lee mensajes del broker
- Consumer Group: Grupo de consumidores que trabajan juntos
- Offset: Posición de lectura en el topic (como un marcador de libro)
- Auto-commit: Guarda automáticamente la posición de lectura
"""

# Importamos las librerías necesarias
from kafka import KafkaConsumer
import json
from colorama import init, Fore, Style

# Inicializamos colorama para mostrar colores en la terminal
init(autoreset=True)


def crear_consumidor(topic_name):
    """
    Crea y configura un consumidor de Kafka.

    Args:
        topic_name: Nombre del topic del cual leer mensajes

    Parámetros importantes:
    - bootstrap_servers: Dirección del broker de Kafka
    - group_id: Identificador del grupo de consumidores
                Los consumidores del mismo grupo se reparten los mensajes
    - auto_offset_reset: Desde dónde empezar a leer
                        'earliest' = desde el principio
                        'latest' = solo mensajes nuevos
    - enable_auto_commit: Si es True, guarda automáticamente el progreso de lectura
    - value_deserializer: Función que convierte los bytes recibidos a objetos Python
    """
    print(f"{Fore.BLUE}{'='*60}")
    print(f"{Fore.CYAN}📥 CONSUMIDOR DE KAFKA - INICIANDO")
    print(f"{Fore.BLUE}{'='*60}\n")

    try:
        # Creamos el consumidor con la configuración
        consumer = KafkaConsumer(
            # Topic(s) a los que nos suscribimos (puede ser una lista de varios topics)
            topic_name,

            # Dirección del broker de Kafka
            bootstrap_servers=['localhost:9092'],

            # Identificador único de este grupo de consumidores
            # Consumidores con el mismo group_id se reparten los mensajes
            group_id='grupo-curso-basico',

            # Desde dónde empezar a leer si no hay offset guardado
            # 'earliest' = lee todos los mensajes desde el principio
            # 'latest' = solo lee mensajes nuevos desde ahora
            auto_offset_reset='earliest',

            # Guarda automáticamente el progreso de lectura
            enable_auto_commit=True,

            # Cada cuánto tiempo guardar el progreso (en ms)
            auto_commit_interval_ms=1000,

            # Deserialización: convierte bytes a objetos Python
            value_deserializer=lambda mensaje: json.loads(mensaje.decode('utf-8')),

            # Tiempo máximo que esperará por nuevos mensajes antes de retornar
            # Si no hay mensajes nuevos en este tiempo, el bucle se detendrá
            consumer_timeout_ms=60000  # 60 segundos
        )

        print(f"{Fore.GREEN}✓ Consumidor creado exitosamente")
        print(f"{Fore.YELLOW}📍 Conectado a: localhost:9092")
        print(f"{Fore.YELLOW}📌 Group ID: grupo-curso-basico")
        print(f"{Fore.YELLOW}📖 Topic: {topic_name}\n")

        return consumer

    except Exception as error:
        print(f"{Fore.RED}✗ Error al crear el consumidor: {error}")
        return None


def procesar_mensaje(mensaje):
    """
    Procesa un mensaje recibido de Kafka.

    Args:
        mensaje: Objeto ConsumerRecord con información del mensaje

    Un objeto ConsumerRecord contiene:
    - topic: Nombre del topic
    - partition: Número de partición
    - offset: Posición del mensaje en la partición
    - key: Clave del mensaje (opcional)
    - value: Contenido del mensaje (ya deserializado)
    - timestamp: Momento en que se produjo el mensaje
    """
    try:
        print(f"{Fore.GREEN}{'─'*60}")
        print(f"{Fore.GREEN}✓ NUEVO MENSAJE RECIBIDO")
        print(f"{Fore.GREEN}{'─'*60}")

        # Información de Kafka sobre el mensaje
        print(f"{Fore.CYAN}📌 Metadatos:")
        print(f"{Fore.CYAN}   • Topic: {mensaje.topic}")
        print(f"{Fore.CYAN}   • Partición: {mensaje.partition}")
        print(f"{Fore.CYAN}   • Offset: {mensaje.offset}")
        print(f"{Fore.CYAN}   • Timestamp: {mensaje.timestamp}")

        # Contenido del mensaje
        print(f"\n{Fore.YELLOW}📦 Contenido:")
        valor = mensaje.value

        # Mostramos el contenido de forma bonita
        if isinstance(valor, dict):
            for clave, contenido in valor.items():
                if isinstance(contenido, dict):
                    print(f"{Fore.YELLOW}   • {clave}:")
                    for sub_clave, sub_contenido in contenido.items():
                        print(f"{Fore.WHITE}     - {sub_clave}: {sub_contenido}")
                else:
                    print(f"{Fore.YELLOW}   • {clave}: {Fore.WHITE}{contenido}")
        else:
            print(f"{Fore.WHITE}   {valor}")

        print(f"{Fore.GREEN}{'─'*60}\n")

        # Aquí iría tu lógica de negocio para procesar el mensaje
        # Por ejemplo: guardar en base de datos, enviar notificación, etc.

        return True

    except Exception as error:
        print(f"{Fore.RED}✗ Error al procesar mensaje: {error}\n")
        return False


def main():
    """
    Función principal que ejecuta el consumidor.
    """
    # Nombre del topic del cual leeremos mensajes
    TOPIC_NAME = 'mensajes-curso'

    # Creamos el consumidor
    consumer = crear_consumidor(TOPIC_NAME)

    if consumer is None:
        print(f"{Fore.RED}No se pudo crear el consumidor. Verifica que Kafka esté ejecutándose.")
        return

    try:
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}👂 ESCUCHANDO MENSAJES DEL TOPIC: '{TOPIC_NAME}'")
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.WHITE}Presiona Ctrl+C para detener el consumidor\n")

        # Contador de mensajes procesados
        contador = 0

        # Este bucle se ejecuta indefinidamente hasta que lo detengamos
        # o hasta que pase el timeout sin recibir mensajes
        for mensaje in consumer:
            contador += 1
            print(f"{Fore.WHITE}[Mensaje #{contador}]")
            procesar_mensaje(mensaje)

        # Si llegamos aquí, es porque pasó el timeout sin mensajes nuevos
        print(f"{Fore.YELLOW}⏱️  No hay más mensajes nuevos (timeout alcanzado)")
        print(f"{Fore.CYAN}📊 Total de mensajes procesados: {contador}\n")

    except KeyboardInterrupt:
        # El usuario presionó Ctrl+C
        print(f"\n{Fore.YELLOW}⚠ Consumidor interrumpido por el usuario")
        print(f"{Fore.CYAN}📊 Total de mensajes procesados: {contador}\n")

    except Exception as error:
        print(f"\n{Fore.RED}✗ Error inesperado: {error}\n")

    finally:
        # Cerramos el consumidor correctamente
        print(f"{Fore.CYAN}🔄 Finalizando consumidor...")

        # Guarda el offset actual antes de cerrar
        consumer.commit()

        # Cierra la conexión
        consumer.close()

        print(f"{Fore.GREEN}✓ Consumidor cerrado correctamente")
        print(f"{Fore.BLUE}{'='*60}\n")


if __name__ == '__main__':
    """
    Este bloque se ejecuta solo cuando corremos el script directamente.
    """
    main()
