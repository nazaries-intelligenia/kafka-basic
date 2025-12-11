#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CONSUMIDOR AVANZADO DE KAFKA
=============================
Este script demuestra características avanzadas de un consumidor:
- Manejo manual de offsets
- Procesamiento por particiones
- Rebalanceo de consumidores
- Control de commits
- Manejo robusto de errores

Conceptos avanzados:
- Manual Offset: Control manual de la posición de lectura
- Partition Assignment: Asignación de particiones a consumidores
- Rebalance: Redistribución de particiones entre consumidores
- Seek: Mover la posición de lectura a un offset específico
"""

from kafka import KafkaConsumer, TopicPartition, ConsumerRebalanceListener
from kafka.errors import KafkaError
import json
import time
from datetime import datetime
from colorama import init, Fore, Style

init(autoreset=True)


class RebalanceListener(ConsumerRebalanceListener):
    """
    Listener para manejar eventos de rebalanceo de particiones.
    """

    def __init__(self, consumer, consumidor_avanzado):
        self.consumer = consumer
        self.consumidor_avanzado = consumidor_avanzado

    def on_partitions_assigned(self, assigned):
        """
        Se ejecuta cuando se asignan particiones al consumidor.
        """
        print(f"{Fore.GREEN}{'─'*70}")
        print(f"{Fore.GREEN}✓ PARTICIONES ASIGNADAS AL CONSUMIDOR")
        print(f"{Fore.GREEN}{'─'*70}")

        for partition in assigned:
            print(f"{Fore.CYAN}  • Topic: {partition.topic}, Partición: {partition.partition}")

        print(f"{Fore.GREEN}{'─'*70}\n")

    def on_partitions_revoked(self, revoked):
        """
        Se ejecuta antes de que se revoquen las particiones.
        """
        print(f"{Fore.YELLOW}{'─'*70}")
        print(f"{Fore.YELLOW}⚠ PARTICIONES REVOCADAS (REBALANCEO)")
        print(f"{Fore.YELLOW}{'─'*70}")

        for partition in revoked:
            print(f"{Fore.YELLOW}  • Topic: {partition.topic}, Partición: {partition.partition}")

        # Hacemos commit antes de perder las particiones
        try:
            self.consumer.commit()
            print(f"{Fore.GREEN}  ✓ Offsets guardados antes del rebalanceo")
        except Exception as error:
            print(f"{Fore.RED}  ✗ Error al guardar offsets: {error}")

        print(f"{Fore.YELLOW}{'─'*70}\n")


class ConsumidorAvanzado:
    """
    Clase que encapsula un consumidor de Kafka con funcionalidades avanzadas.
    """

    def __init__(self, topics, group_id='grupo-avanzado'):
        """
        Inicializa el consumidor con configuración avanzada.
        """
        print(f"{Fore.BLUE}{'='*70}")
        print(f"{Fore.CYAN}📥 CONSUMIDOR AVANZADO DE KAFKA - INICIANDO")
        print(f"{Fore.BLUE}{'='*70}\n")

        self.topics = topics if isinstance(topics, list) else [topics]
        self.mensajes_procesados = 0
        self.errores = 0
        self.tiempo_inicio = time.time()

        try:
            self.consumer = KafkaConsumer(
                *self.topics,
                bootstrap_servers=['localhost:9092'],
                group_id=group_id,

                # Configuración manual de offsets
                # False: Debemos hacer commit manualmente
                enable_auto_commit=False,

                # Desde dónde empezar a leer
                auto_offset_reset='earliest',

                # Deserialización
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                key_deserializer=lambda k: k.decode('utf-8') if k else None,

                # Número máximo de registros por poll
                max_poll_records=100,

                # Timeout del poll
                max_poll_interval_ms=300000,  # 5 minutos

                # Tamaño del buffer de recepción
                fetch_min_bytes=1,
                fetch_max_wait_ms=500,

                # Configuración de sesión
                session_timeout_ms=10000,
                heartbeat_interval_ms=3000
            )

            print(f"{Fore.GREEN}✓ Consumidor avanzado creado")
            print(f"{Fore.YELLOW}📍 Configuración:")
            print(f"{Fore.YELLOW}   • Group ID: {group_id}")
            print(f"{Fore.YELLOW}   • Topics: {', '.join(self.topics) if self.topics else 'Ninguno (asignación manual)'}")
            print(f"{Fore.YELLOW}   • Auto-commit: Desactivado (manual)")
            print(f"{Fore.YELLOW}   • Max poll records: 100\n")

            # Solo nos suscribimos si hay topics
            # Si no hay topics, significa que usaremos assign() manualmente
            if self.topics:
                # Callbacks de rebalanceo
                # Creamos el listener de rebalanceo
                listener = RebalanceListener(self.consumer, self)

                # Nos suscribimos con el listener
                self.consumer.subscribe(self.topics, listener=listener)

        except Exception as error:
            print(f"{Fore.RED}✗ Error al crear el consumidor: {error}")
            raise

    def procesar_mensaje(self, mensaje):
        """
        Procesa un mensaje con manejo robusto de errores.

        Args:
            mensaje: ConsumerRecord con el mensaje
        """
        try:
            print(f"{Fore.CYAN}[{self.mensajes_procesados + 1}] "
                  f"Topic: {mensaje.topic} | "
                  f"Part: {mensaje.partition} | "
                  f"Offset: {mensaje.offset}")

            # Mostramos la clave si existe
            if mensaje.key:
                print(f"{Fore.YELLOW}    🔑 Clave: {mensaje.key}")

            # Mostramos algunos campos del mensaje
            valor = mensaje.value
            if isinstance(valor, dict):
                # Mostramos máximo 3 campos para no saturar la consola
                campos_mostrar = list(valor.items())[:3]
                for clave, contenido in campos_mostrar:
                    print(f"{Fore.WHITE}    • {clave}: {contenido}")

                if len(valor) > 3:
                    print(f"{Fore.WHITE}    • ... ({len(valor) - 3} campos más)")
            else:
                print(f"{Fore.WHITE}    • Valor: {valor}")

            self.mensajes_procesados += 1

            # Aquí iría tu lógica de negocio
            # Por ejemplo: guardar en DB, procesar datos, enviar notificación, etc.

            # Simulamos procesamiento
            time.sleep(0.1)

            return True

        except Exception as error:
            self.errores += 1
            print(f"{Fore.RED}    ✗ Error al procesar: {error}")
            return False

    def consumir_con_commit_manual(self, max_mensajes=None):
        """
        Consume mensajes con control manual de commits.
        Esto nos da más control sobre cuándo se guarda el progreso.

        Args:
            max_mensajes: Número máximo de mensajes a procesar (None = infinito)
        """
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}👂 CONSUMIENDO MENSAJES CON COMMIT MANUAL")
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.WHITE}Presiona Ctrl+C para detener\n")

        try:
            while True:
                # Poll obtiene un batch de mensajes
                # timeout_ms: cuánto tiempo esperar por mensajes
                records = self.consumer.poll(timeout_ms=1000)

                if not records:
                    # No hay mensajes nuevos
                    continue

                # Procesamos cada partición
                for topic_partition, mensajes in records.items():
                    print(f"\n{Fore.BLUE}📦 Batch de {len(mensajes)} mensajes "
                          f"de {topic_partition.topic}:{topic_partition.partition}\n")

                    for mensaje in mensajes:
                        exito = self.procesar_mensaje(mensaje)

                        # Si falla el procesamiento, podemos decidir qué hacer
                        if not exito:
                            print(f"{Fore.RED}    ⚠ Mensaje falló, pero continuamos...")
                            # Opción 1: Continuar con el siguiente
                            # Opción 2: Reintentar
                            # Opción 3: Enviar a un topic de errores

                    # Commit manual después de procesar el batch
                    # Esto guarda el offset del último mensaje procesado
                    try:
                        self.consumer.commit()
                        print(f"{Fore.GREEN}✓ Commit realizado para este batch\n")
                    except Exception as error:
                        print(f"{Fore.RED}✗ Error en commit: {error}\n")

                # Si alcanzamos el máximo de mensajes, salimos
                if max_mensajes and self.mensajes_procesados >= max_mensajes:
                    print(f"\n{Fore.CYAN}✓ Alcanzado el máximo de mensajes: {max_mensajes}")
                    break

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠ Consumidor interrumpido por el usuario")

    def consumir_particiones_especificas(self, particiones_dict):
        """
        Consume de particiones específicas sin usar consumer groups.
        Útil cuando necesitas control total sobre qué particiones leer.

        Args:
            particiones_dict: Dict con {topic: [lista_de_particiones]}
                            Ejemplo: {'mi-topic': [0, 1]}
        """
        print(f"{Fore.MAGENTA}{'='*70}")
        print(f"{Fore.MAGENTA}🎯 CONSUMIENDO PARTICIONES ESPECÍFICAS")
        print(f"{Fore.MAGENTA}{'='*70}\n")

        # Creamos TopicPartition para cada partición especificada
        topic_partitions = []
        for topic, particiones in particiones_dict.items():
            for part in particiones:
                tp = TopicPartition(topic, part)
                topic_partitions.append(tp)
                print(f"{Fore.YELLOW}📌 Asignando {topic}:{part}")

        # Asignamos las particiones manualmente
        self.consumer.assign(topic_partitions)

        # Opcional: mover a un offset específico
        # for tp in topic_partitions:
        #     self.consumer.seek(tp, 0)  # Empezar desde el inicio

        print(f"\n{Fore.GREEN}✓ Particiones asignadas\n")

        # Ahora consumimos normalmente
        try:
            for mensaje in self.consumer:
                self.procesar_mensaje(mensaje)

                # Commit periódico
                if self.mensajes_procesados % 10 == 0:
                    self.consumer.commit()
                    print(f"{Fore.GREEN}  ✓ Checkpoint: {self.mensajes_procesados} mensajes\n")

        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⚠ Consumidor interrumpido")

    def obtener_metricas(self):
        """
        Muestra métricas del consumidor.
        """
        tiempo_total = time.time() - self.tiempo_inicio

        print(f"\n{Fore.BLUE}{'='*70}")
        print(f"{Fore.CYAN}📊 MÉTRICAS DEL CONSUMIDOR")
        print(f"{Fore.BLUE}{'='*70}")
        print(f"{Fore.GREEN}✓ Mensajes procesados: {self.mensajes_procesados}")
        print(f"{Fore.RED}✗ Errores: {self.errores}")
        print(f"{Fore.YELLOW}⏱️  Tiempo total: {tiempo_total:.2f} segundos")

        if tiempo_total > 0:
            tasa = self.mensajes_procesados / tiempo_total
            print(f"{Fore.CYAN}⚡ Tasa de procesamiento: {tasa:.2f} msg/seg")

        if self.mensajes_procesados + self.errores > 0:
            tasa_exito = (self.mensajes_procesados /
                         (self.mensajes_procesados + self.errores)) * 100
            print(f"{Fore.MAGENTA}📈 Tasa de éxito: {tasa_exito:.2f}%")

        print(f"{Fore.BLUE}{'='*70}\n")

    def cerrar(self):
        """
        Cierra el consumidor de forma segura.
        """
        print(f"{Fore.CYAN}🔄 Cerrando consumidor...")

        try:
            # Último commit antes de cerrar
            self.consumer.commit()
            print(f"{Fore.GREEN}✓ Último commit realizado")
        except Exception as error:
            print(f"{Fore.YELLOW}⚠ No se pudo hacer commit final: {error}")

        self.consumer.close()
        print(f"{Fore.GREEN}✓ Consumidor cerrado\n")


def ejemplo_commit_manual():
    """
    Ejemplo de consumo con commit manual.
    """
    consumidor = ConsumidorAvanzado(
        topics=['eventos-sensores', 'eventos-batch'],
        group_id='grupo-commit-manual'
    )

    try:
        # Consumimos hasta 50 mensajes
        consumidor.consumir_con_commit_manual(max_mensajes=50)

    finally:
        consumidor.obtener_metricas()
        consumidor.cerrar()


def ejemplo_particiones_especificas():
    """
    Ejemplo de consumo de particiones específicas.
    """
    consumidor = ConsumidorAvanzado(
        topics=[],  # No necesitamos especificar topics aquí
        group_id='grupo-particiones'
    )

    try:
        # Leemos solo las particiones 0 y 1 del topic 'eventos-sensores'
        particiones = {
            'eventos-sensores': [0, 1]
        }

        consumidor.consumir_particiones_especificas(particiones)

    except KeyboardInterrupt:
        pass
    finally:
        consumidor.obtener_metricas()
        consumidor.cerrar()


def main():
    """
    Menú principal para elegir qué ejemplo ejecutar.
    """
    print(f"{Fore.BLUE}{'='*70}")
    print(f"{Fore.CYAN}🎓 CONSUMIDOR AVANZADO - EJEMPLOS")
    print(f"{Fore.BLUE}{'='*70}\n")

    print(f"{Fore.WHITE}Selecciona un ejemplo:")
    print(f"{Fore.YELLOW}1. Consumo con commit manual (control total)")
    print(f"{Fore.YELLOW}2. Consumo de particiones específicas")
    print(f"{Fore.YELLOW}3. Consumo continuo con métricas en tiempo real\n")

    try:
        opcion = input(f"{Fore.GREEN}Tu elección (1-3): {Fore.WHITE}")

        if opcion == '1':
            ejemplo_commit_manual()
        elif opcion == '2':
            ejemplo_particiones_especificas()
        elif opcion == '3':
            consumidor = ConsumidorAvanzado(
                topics=['eventos-sensores', 'eventos-batch', 'mensajes-curso']
            )
            try:
                consumidor.consumir_con_commit_manual()
            finally:
                consumidor.obtener_metricas()
                consumidor.cerrar()
        else:
            print(f"{Fore.RED}Opción inválida")

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}⚠ Programa interrumpido\n")


if __name__ == '__main__':
    main()
