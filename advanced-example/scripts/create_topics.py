#!/usr/bin/env python3
"""
Script para crear los topics de Kafka con configuración específica
"""
import json
import sys
from kafka.admin import KafkaAdminClient, NewTopic
from kafka.errors import TopicAlreadyExistsError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_topics_config(config_file='config/topics.json'):
    """Cargar configuración de topics desde archivo JSON"""
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config['topics']
    except FileNotFoundError:
        logger.error(f"Config file not found: {config_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in config file: {e}")
        sys.exit(1)


def create_topics(bootstrap_servers=['localhost:9092']):
    """Crear topics de Kafka basados en configuración"""

    # Conectar al cluster de Kafka
    admin_client = KafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id='topic-creator'
    )

    # Cargar configuración de topics
    topics_config = load_topics_config()

    # Crear lista de NewTopic
    topics_to_create = []
    for topic_config in topics_config:
        new_topic = NewTopic(
            name=topic_config['name'],
            num_partitions=topic_config['partitions'],
            replication_factor=topic_config['replication_factor'],
            topic_configs=topic_config.get('config', {})
        )
        topics_to_create.append(new_topic)

    # Crear topics
    logger.info(f"Creating {len(topics_to_create)} topics...")

    try:
        result = admin_client.create_topics(
            new_topics=topics_to_create,
            validate_only=False
        )

        for topic, future in result.items():
            try:
                future.result()  # Esperar resultado
                topic_info = next(t for t in topics_config if t['name'] == topic)
                logger.info(f"✅ Created topic: {topic}")
                logger.info(f"   Description: {topic_info.get('description', 'N/A')}")
                logger.info(f"   Partitions: {topic_info['partitions']}")
                logger.info(f"   Replication: {topic_info['replication_factor']}")
            except TopicAlreadyExistsError:
                logger.warning(f"⚠️  Topic already exists: {topic}")
            except Exception as e:
                logger.error(f"❌ Failed to create topic {topic}: {e}")

    except Exception as e:
        logger.error(f"❌ Error creating topics: {e}")
        sys.exit(1)
    finally:
        admin_client.close()

    logger.info("\n✅ Topic creation completed!")


def list_topics(bootstrap_servers=['localhost:9092']):
    """Listar todos los topics existentes"""
    admin_client = KafkaAdminClient(
        bootstrap_servers=bootstrap_servers,
        client_id='topic-lister'
    )

    try:
        topics = admin_client.list_topics()
        logger.info(f"\n📋 Existing topics ({len(topics)}):")
        for topic in sorted(topics):
            if not topic.startswith('__'):  # Filtrar topics internos
                logger.info(f"  - {topic}")
    finally:
        admin_client.close()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Kafka Topic Management')
    parser.add_argument(
        '--bootstrap-servers',
        default='localhost:9092',
        help='Kafka bootstrap servers (default: localhost:9092)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List existing topics'
    )

    args = parser.parse_args()
    bootstrap_servers = args.bootstrap_servers.split(',')

    if args.list:
        list_topics(bootstrap_servers)
    else:
        create_topics(bootstrap_servers)
        list_topics(bootstrap_servers)
