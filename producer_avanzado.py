#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
PRODUCTOR AVANZADO DE KAFKA
============================
Este script demuestra características avanzadas de un productor:
- Uso de claves (keys) para el particionamiento
- Callbacks para manejar éxitos y errores
- Envío asíncrono de mensajes
- Métricas y estadísticas
- Manejo de errores robusto

Conceptos avanzados:
- Key: Clave que determina a qué partición va el mensaje
- Callback: Función que se ejecuta cuando se confirma el envío
- Particionamiento: Distribución de mensajes entre particiones
- Async: Envío no bloqueante de mensajes
"""

from kafka import KafkaProducer
from kafka.errors import KafkaError
import json
import time
import random
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)


class ProductorAvanzado:
    """
    Clase que encapsula un productor de Kafka con funcionalidades avanzadas.
    """

    def __init__(self, bootstrap_servers=['localhost:9092']):
        """
        Inicializa el productor con configuración avanzada.
        """
        print(f"{Fore.BLUE}{'='*70}")
        print(f"{Fore.CYAN}🚀 PRODUCTOR AVANZADO DE KAFKA - INICIANDO")
        print(f"{Fore.BLUE}{'='*70}\n")

        # Estadísticas del productor
        self.mensajes_enviados = 0
        self.mensajes_fallidos = 0
        self.tiempo_inicio = time.time()

        try:
            self.producer = KafkaProducer(
                bootstrap_servers=bootstrap_servers,

                # Serialización de valores a JSON
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),

                # Serialización de claves a string
                # Las claves son importantes para el particionamiento
                key_serializer=lambda k: k.encode('utf-8') if k else None,

                # Configuración de confirmación
                # 'all' o '-1': Espera confirmación de todas las réplicas
                acks='all',

                # Compresión de mensajes (ahorra ancho de banda)
                # Opciones: 'gzip', 'snappy', 'lz4', 'zstd'
                compression_type='gzip',

                # Tamaño del buffer en bytes
                # Mensajes se acumulan aquí antes de enviarse
                buffer_memory=33554432,  # 32 MB

                # Tiempo máximo de espera para llenar un batch
                linger_ms=100,  # 100 milisegundos

                # Tamaño máximo de un batch de mensajes
                batch_size=16384,  # 16 KB

                # Reintentos automáticos
                retries=3,

                # Tiempo entre reintentos
                retry_backoff_ms=100,

                # Timeout de la petición
                request_timeout_ms=30000,

                # Número máximo de peticiones en vuelo por conexión
                # Mantener en 1 para garantizar orden estricto
                max_in_flight_requests_per_connection=5
            )

            print(f"{Fore.GREEN}✓ Productor avanzado creado exitosamente")
            print(f"{Fore.YELLOW}📍 Configuración:")
            print(f"{Fore.YELLOW}   • Servers: {bootstrap_servers}")
            print(f"{Fore.YELLOW}   • Compresión: gzip")
            print(f"{Fore.YELLOW}   • Reintentos: 3")
            print(f"{Fore.YELLOW}   • Confirmación: all\n")

        except Exception as error:
            print(f"{Fore.RED}✗ Error al crear el productor: {error}")
            raise

    def callback_exito(self, metadata):
        """
        Callback ejecutado cuando un mensaje se envía exitosamente.

        Args:
            metadata: Información sobre el mensaje enviado
        """
        self.mensajes_enviados += 1

        print(f"{Fore.GREEN}  ✓ Mensaje #{self.mensajes_enviados} confirmado")
        print(f"{Fore.CYAN}    • Topic: {metadata.topic}")
        print(f"{Fore.CYAN}    • Partición: {metadata.partition}")
        print(f"{Fore.CYAN}    • Offset: {metadata.offset}")

    def callback_error(self, error):
        """
        Callback ejecutado cuando falla el envío de un mensaje.

        Args:
            error: Información del error
        """
        self.mensajes_fallidos += 1

        print(f"{Fore.RED}  ✗ Error al enviar mensaje #{self.mensajes_fallidos}")
        print(f"{Fore.RED}    • Tipo: {type(error).__name__}")
        print(f"{Fore.RED}    • Detalle: {error}")

    def enviar_con_clave(self, topic, clave, mensaje):
        """
        Envía un mensaje con una clave específica.

        La clave determina a qué partición irá el mensaje.
        Mensajes con la misma clave siempre van a la misma partición.
        Esto es útil para mantener el orden de mensajes relacionados.

        Args:
            topic: Nombre del topic
            clave: Clave del mensaje (string)
            mensaje: Contenido del mensaje (dict)
        """
        try:
            # Agregamos timestamp
            mensaje['timestamp'] = datetime.now().isoformat()
            mensaje['key'] = clave

            # Enviamos de forma asíncrona con callbacks
            # add_callback: se ejecuta si el envío es exitoso
            # add_errback: se ejecuta si hay un error
            self.producer.send(
                topic,
                key=clave,
                value=mensaje
            ).add_callback(self.callback_exito).add_errback(self.callback_error)

        except Exception as error:
            print(f"{Fore.RED}✗ Excepción al enviar: {error}")

    def enviar_batch(self, topic, mensajes):
        """
        Envía un lote de mensajes de forma eficiente.

        Args:
            topic: Nombre del topic
            mensajes: Lista de tuplas (clave, mensaje)
        """
        print(f"{Fore.MAGENTA}📦 Enviando batch de {len(mensajes)} mensajes...")

        for clave, mensaje in mensajes:
            self.enviar_con_clave(topic, clave, mensaje)

        # Forzamos el envío de todos los mensajes en buffer
        self.producer.flush()

        print(f"{Fore.GREEN}✓ Batch enviado completamente\n")

    def obtener_metricas(self):
        """
        Obtiene métricas del productor.
        """
        tiempo_total = time.time() - self.tiempo_inicio

        print(f"{Fore.BLUE}{'='*70}")
        print(f"{Fore.CYAN}📊 MÉTRICAS DEL PRODUCTOR")
        print(f"{Fore.BLUE}{'='*70}")
        print(f"{Fore.GREEN}✓ Mensajes enviados: {self.mensajes_enviados}")
        print(f"{Fore.RED}✗ Mensajes fallidos: {self.mensajes_fallidos}")
        print(f"{Fore.YELLOW}⏱️  Tiempo total: {tiempo_total:.2f} segundos")

        if tiempo_total > 0:
            tasa = self.mensajes_enviados / tiempo_total
            print(f"{Fore.CYAN}⚡ Tasa de envío: {tasa:.2f} msg/seg")

        if self.mensajes_enviados + self.mensajes_fallidos > 0:
            tasa_exito = (self.mensajes_enviados /
                         (self.mensajes_enviados + self.mensajes_fallidos)) * 100
            print(f"{Fore.MAGENTA}📈 Tasa de éxito: {tasa_exito:.2f}%")

        print(f"{Fore.BLUE}{'='*70}\n")

    def cerrar(self):
        """
        Cierra el productor de forma segura.
        """
        print(f"{Fore.CYAN}🔄 Cerrando productor...")
        self.producer.flush()
        self.producer.close()
        print(f"{Fore.GREEN}✓ Productor cerrado\n")


def simular_eventos_sensores():
    """
    Simula eventos de diferentes sensores IoT.
    Cada sensor tiene una clave única, lo que garantiza que
    sus mensajes se mantengan en orden en la misma partición.
    """
    TOPIC = 'eventos-sensores'

    # Creamos el productor avanzado
    productor = ProductorAvanzado()

    try:
        # Lista de sensores
        sensores = ['sensor-temp-01', 'sensor-hum-01', 'sensor-pres-01',
                   'sensor-temp-02', 'sensor-hum-02']

        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}🌡️  SIMULACIÓN DE SENSORES IoT")
        print(f"{Fore.MAGENTA}{'='*70}\n")
        print(f"{Fore.WHITE}Enviando 20 eventos de sensores...\n")

        # Enviamos 20 eventos
        for i in range(1, 21):
            # Seleccionamos un sensor aleatorio
            sensor_id = random.choice(sensores)

            # Creamos un evento del sensor
            evento = {
                'id_evento': i,
                'sensor_id': sensor_id,
                'tipo': sensor_id.split('-')[1],
                'valor': round(random.uniform(18.0, 30.0), 2),
                'unidad': 'celsius' if 'temp' in sensor_id else '%',
                'estado': random.choice(['normal', 'alerta', 'critico']),
                'ubicacion': random.choice(['sala-a', 'sala-b', 'exterior'])
            }

            print(f"{Fore.WHITE}[{i}/20] Enviando evento de {sensor_id}...")

            # La clave es el ID del sensor
            # Esto garantiza que todos los eventos del mismo sensor
            # vayan a la misma partición y mantengan el orden
            productor.enviar_con_clave(TOPIC, sensor_id, evento)

            # Pequeña pausa para simular eventos reales
            time.sleep(0.5)

        # Esperamos a que se envíen todos los mensajes
        print(f"\n{Fore.YELLOW}⏳ Esperando confirmaciones...")
        productor.producer.flush()

        # Mostramos las métricas
        productor.obtener_metricas()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Simulación interrumpida")

    finally:
        productor.cerrar()


def enviar_batch_ejemplo():
    """
    Ejemplo de envío en batch para alta performance.
    """
    TOPIC = 'eventos-batch'

    productor = ProductorAvanzado()

    try:
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}📦 EJEMPLO DE ENVÍO EN BATCH")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        # Preparamos un batch de 50 mensajes
        batch = []
        for i in range(1, 51):
            clave = f"usuario-{random.randint(1, 10)}"
            mensaje = {
                'id': i,
                'accion': random.choice(['click', 'view', 'purchase', 'logout']),
                'pagina': random.choice(['home', 'productos', 'carrito', 'perfil']),
                'duracion_seg': random.randint(1, 300)
            }
            batch.append((clave, mensaje))

        # Enviamos todo el batch
        productor.enviar_batch(TOPIC, batch)

        # Mostramos métricas
        productor.obtener_metricas()

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Envío interrumpido")

    finally:
        productor.cerrar()


def main():
    """
    Menú principal para elegir qué ejemplo ejecutar.
    """
    print(f"{Fore.BLUE}{'='*70}")
    print(f"{Fore.CYAN}🎓 PRODUCTOR AVANZADO - EJEMPLOS")
    print(f"{Fore.BLUE}{'='*70}\n")

    print(f"{Fore.WHITE}Selecciona un ejemplo:")
    print(f"{Fore.YELLOW}1. Simular eventos de sensores IoT (con claves)")
    print(f"{Fore.YELLOW}2. Envío en batch de alta performance")
    print(f"{Fore.YELLOW}3. Ejecutar ambos ejemplos\n")

    try:
        opcion = input(f"{Fore.GREEN}Tu elección (1-3): {Fore.WHITE}")

        if opcion == '1':
            simular_eventos_sensores()
        elif opcion == '2':
            enviar_batch_ejemplo()
        elif opcion == '3':
            simular_eventos_sensores()
            print(f"\n{Fore.CYAN}{'─'*70}\n")
            enviar_batch_ejemplo()
        else:
            print(f"{Fore.RED}Opción inválida")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Programa interrumpido\n")


if __name__ == '__main__':
    main()
