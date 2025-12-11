#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRODUCTOR BÁSICO DE KAFKA
=========================
Este script envía mensajes a un topic de Kafka.
Un productor es quien GENERA y ENVÍA mensajes al broker de Kafka.

Conceptos clave:
- Topic: Es como un canal o categoría donde se publican los mensajes
- Broker: El servidor de Kafka que recibe y almacena los mensajes
- Producer: La aplicación que envía mensajes al broker
"""

# Importamos las librerías necesarias
from kafka import KafkaProducer
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

# Inicializamos colorama para mostrar colores en la terminal
init(autoreset=True)


def crear_productor():
    """
    Crea y configura un productor de Kafka.

    Parámetros importantes:
    - bootstrap_servers: Dirección del broker de Kafka (localhost:9092)
    - value_serializer: Función que convierte nuestros datos Python a bytes
                       Kafka solo entiende bytes, así que convertimos a JSON y luego a bytes
    - acks: Configuración de confirmación
            'all' = espera confirmación de todos los brokers (más seguro pero más lento)
            '1' = espera confirmación del broker líder (balance)
            '0' = no espera confirmación (más rápido pero menos seguro)
    """
    print(f"{Fore.BLUE}{'='*60}")
    print(f"{Fore.CYAN}🚀 PRODUCTOR DE KAFKA - INICIANDO")
    print(f"{Fore.BLUE}{'='*60}\n")

    try:
        # Creamos el productor con la configuración
        producer = KafkaProducer(
            # Dirección del broker de Kafka
            bootstrap_servers=['localhost:9092'],

            # Serialización: convierte diccionarios Python a JSON y luego a bytes
            value_serializer=lambda mensaje: json.dumps(mensaje).encode('utf-8'),

            # Esperamos confirmación de que el mensaje fue recibido
            acks='all',

            # Reintentos en caso de fallo
            retries=3,

            # Tiempo máximo de espera para recibir confirmación (en ms)
            request_timeout_ms=10000
        )

        print(f"{Fore.GREEN}✓ Productor creado exitosamente")
        print(f"{Fore.YELLOW}📍 Conectado a: localhost:9092\n")
        return producer

    except Exception as error:
        print(f"{Fore.RED}✗ Error al crear el productor: {error}")
        return None


def enviar_mensaje(producer, topic, mensaje):
    """
    Envía un mensaje al topic especificado.

    Args:
        producer: El objeto productor de Kafka
        topic: Nombre del topic donde enviar el mensaje
        mensaje: Diccionario con los datos a enviar
    """
    try:
        # Agregamos timestamp al mensaje
        mensaje['timestamp'] = datetime.now().isoformat()

        # Enviamos el mensaje al topic
        # send() es asíncrono, retorna un objeto Future
        future = producer.send(topic, mensaje)

        # get() espera la confirmación del broker (bloquea hasta recibir respuesta)
        # timeout especifica cuánto tiempo esperar máximo
        record_metadata = future.get(timeout=10)

        # Si llegamos aquí, el mensaje fue enviado exitosamente
        print(f"{Fore.GREEN}✓ Mensaje enviado correctamente")
        print(f"{Fore.CYAN}  Topic: {record_metadata.topic}")
        print(f"{Fore.CYAN}  Partición: {record_metadata.partition}")
        print(f"{Fore.CYAN}  Offset: {record_metadata.offset}")
        print(f"{Fore.YELLOW}  Contenido: {mensaje}\n")

        return True

    except Exception as error:
        print(f"{Fore.RED}✗ Error al enviar mensaje: {error}\n")
        return False


def main():
    """
    Función principal que ejecuta el productor.
    """
    # Nombre del topic donde enviaremos los mensajes
    # Si el topic no existe, Kafka lo creará automáticamente
    TOPIC_NAME = 'mensajes-curso'

    # Creamos el productor
    producer = crear_productor()

    if producer is None:
        print(f"{Fore.RED}No se pudo crear el productor. Verifica que Kafka esté ejecutándose.")
        return

    try:
        print(f"{Fore.MAGENTA}{'='*60}")
        print(f"{Fore.MAGENTA}📤 ENVIANDO MENSAJES AL TOPIC: '{TOPIC_NAME}'")
        print(f"{Fore.MAGENTA}{'='*60}\n")

        # Enviamos 10 mensajes de ejemplo
        for i in range(1, 11):
            # Creamos un mensaje con diferentes tipos de datos
            mensaje = {
                'id': i,
                'tipo': 'mensaje_ejemplo',
                'contenido': f'Este es el mensaje número {i}',
                'prioridad': 'alta' if i % 3 == 0 else 'normal',
                'datos': {
                    'temperatura': 20 + i,
                    'humedad': 60 + (i * 2)
                }
            }

            print(f"{Fore.WHITE}[{i}/10] Enviando mensaje {i}...")
            enviar_mensaje(producer, TOPIC_NAME, mensaje)

            # Esperamos 2 segundos entre mensajes
            # Esto es solo para el ejemplo, en producción no es necesario
            time.sleep(2)

        print(f"{Fore.GREEN}{'='*60}")
        print(f"{Fore.GREEN}✓ TODOS LOS MENSAJES ENVIADOS EXITOSAMENTE")
        print(f"{Fore.GREEN}{'='*60}\n")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Productor interrumpido por el usuario")

    finally:
        # Aseguramos que todos los mensajes pendientes se envíen
        print(f"{Fore.CYAN}🔄 Finalizando productor...")
        producer.flush()  # Envía todos los mensajes en buffer
        producer.close()  # Cierra la conexión
        print(f"{Fore.GREEN}✓ Productor cerrado correctamente\n")


if __name__ == '__main__':
    """
    Este bloque se ejecuta solo cuando corremos el script directamente.
    No se ejecuta si importamos este archivo como módulo.
    """
    main()
