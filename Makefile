.PHONY: help start stop down restart restart-full logs status clean install producer consumer ui test-producer test-consumer

# Colores para los mensajes
GREEN  := \033[0;32m
BLUE   := \033[0;34m
YELLOW := \033[0;33m
NC     := \033[0m # No Color

help: ## Muestra esta ayuda
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo "$(GREEN)   Curso Básico de Apache Kafka con Python$(NC)"
	@echo "$(BLUE)═══════════════════════════════════════════════════════$(NC)"
	@echo ""
	@echo "$(YELLOW)Comandos disponibles:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

install: ## Instala las dependencias de Python
	@echo "$(BLUE)📦 Instalando dependencias...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✓ Dependencias instaladas correctamente$(NC)"

start: ## Inicia todos los contenedores de Kafka e instala dependencias
	@echo "$(BLUE)📦 Instalando dependencias de Python...$(NC)"
	@pip install -r requirements.txt > /dev/null 2>&1 || (echo "$(YELLOW)⚠️  Error instalando dependencias, intenta ejecutar: make install$(NC)"; exit 1)
	@echo "$(GREEN)✓ Dependencias instaladas$(NC)"
	@echo ""
	@echo "$(BLUE)🚀 Iniciando Kafka...$(NC)"
	docker compose up -d
	@echo "$(GREEN)✓ Kafka iniciado correctamente$(NC)"
	@echo ""
	@echo "$(YELLOW)Esperando a que Kafka esté listo...$(NC)"
	@sleep 10
	@echo "$(GREEN)✓ Kafka está listo para usar$(NC)"
	@echo ""
	@echo "$(BLUE)📊 Kafka UI disponible en: http://localhost:8080$(NC)"

stop: ## Detiene todos los contenedores sin eliminar volúmenes
	@echo "$(YELLOW)🛑 Deteniendo Kafka...$(NC)"
	docker compose stop
	@echo "$(GREEN)✓ Kafka detenido$(NC)"

down: ## Detiene y elimina todos los contenedores (mantiene volúmenes)
	@echo "$(YELLOW)🛑 Deteniendo y eliminando contenedores Kafka...$(NC)"
	docker compose down --remove-orphans || true
	@echo "$(YELLOW)  Limpiando contenedores residuales...$(NC)"
	@docker rm -f zookeeper kafka kafka-ui 2>/dev/null || true
	@echo "$(GREEN)✓ Contenedores eliminados$(NC)"

restart: ## Reinicia todos los contenedores sin reconstruir
	@echo "$(YELLOW)🔄 Reiniciando Kafka...$(NC)"
	docker compose restart
	@echo "$(GREEN)✓ Kafka reiniciado$(NC)"

restart-full: ## Detiene, elimina y reinicia todos los contenedores desde cero
	@echo "$(YELLOW)🔄 Reinicio completo de Kafka...$(NC)"
	@echo "$(YELLOW)  1. Deteniendo contenedores...$(NC)"
	docker compose down --remove-orphans || true
	@docker rm -f zookeeper kafka kafka-ui 2>/dev/null || true
	@echo "$(YELLOW)  2. Iniciando desde cero...$(NC)"
	docker compose up -d
	@echo "$(YELLOW)  3. Esperando a que Kafka esté listo...$(NC)"
	@sleep 10
	@echo "$(GREEN)✓ Kafka reiniciado completamente y listo$(NC)"
	@echo ""
	@echo "$(BLUE)📊 Kafka UI disponible en: http://localhost:8080$(NC)"

logs: ## Muestra los logs de todos los contenedores
	docker compose logs -f

logs-kafka: ## Muestra solo los logs de Kafka
	docker compose logs -f kafka

logs-zookeeper: ## Muestra solo los logs de Zookeeper
	docker compose logs -f zookeeper

status: ## Muestra el estado de los contenedores
	@echo "$(BLUE)📊 Estado de los contenedores:$(NC)"
	@docker compose ps

clean: ## Detiene y elimina contenedores, volúmenes y datos
	@echo "$(YELLOW)🧹 Limpiando todo...$(NC)"
	docker compose down -v
	@echo "$(GREEN)✓ Todo limpio$(NC)"

ui: ## Abre la interfaz web de Kafka UI
	@echo "$(BLUE)🌐 Abriendo Kafka UI...$(NC)"
	@which xdg-open > /dev/null && xdg-open http://localhost:8080 || which open > /dev/null && open http://localhost:8080 || echo "Abre manualmente: http://localhost:8080"

producer: ## Ejecuta el productor básico
	@echo "$(BLUE)📤 Ejecutando productor...$(NC)"
	python3 producer.py

consumer: ## Ejecuta el consumidor básico
	@echo "$(BLUE)📥 Ejecutando consumidor...$(NC)"
	python3 consumer.py

producer-avanzado: ## Ejecuta el productor avanzado
	@echo "$(BLUE)📤 Ejecutando productor avanzado...$(NC)"
	python3 producer_avanzado.py

consumer-avanzado: ## Ejecuta el consumidor avanzado
	@echo "$(BLUE)📥 Ejecutando consumidor avanzado...$(NC)"
	python3 consumer_avanzado.py

test: ## Ejecuta un test rápido enviando y recibiendo mensajes
	@echo "$(BLUE)🧪 Ejecutando test...$(NC)"
	@echo "Este test enviará 5 mensajes y luego los leerá"
	@echo ""
	@echo "$(YELLOW)1. Enviando mensajes...$(NC)"
	@python3 -c "from kafka import KafkaProducer; import json; p = KafkaProducer(bootstrap_servers='localhost:9092', value_serializer=lambda v: json.dumps(v).encode('utf-8')); [p.send('test-topic', {'test': i, 'mensaje': f'Test {i}'}) for i in range(5)]; p.flush(); print('✓ 5 mensajes enviados')"
	@echo ""
	@echo "$(YELLOW)2. Leyendo mensajes...$(NC)"
	@timeout 5 python3 -c "from kafka import KafkaConsumer; import json; c = KafkaConsumer('test-topic', bootstrap_servers='localhost:9092', auto_offset_reset='earliest', value_deserializer=lambda m: json.loads(m.decode('utf-8')), consumer_timeout_ms=3000); [print(f'  ✓ Recibido: {msg.value}') for msg in c]" || true
	@echo ""
	@echo "$(GREEN)✓ Test completado$(NC)"

create-topic: ## Crea un topic nuevo (uso: make create-topic TOPIC=mi-topic)
	@echo "$(BLUE)📝 Creando topic: $(TOPIC)$(NC)"
	docker exec -it kafka kafka-topics --create --topic $(TOPIC) --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
	@echo "$(GREEN)✓ Topic '$(TOPIC)' creado$(NC)"

list-topics: ## Lista todos los topics
	@echo "$(BLUE)📋 Topics disponibles:$(NC)"
	@docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

describe-topic: ## Describe un topic (uso: make describe-topic TOPIC=mi-topic)
	@echo "$(BLUE)📊 Información del topic: $(TOPIC)$(NC)"
	@docker exec -it kafka kafka-topics --describe --topic $(TOPIC) --bootstrap-server localhost:9092

delete-topic: ## Elimina un topic (uso: make delete-topic TOPIC=mi-topic)
	@echo "$(YELLOW)🗑️  Eliminando topic: $(TOPIC)$(NC)"
	docker exec -it kafka kafka-topics --delete --topic $(TOPIC) --bootstrap-server localhost:9092
	@echo "$(GREEN)✓ Topic '$(TOPIC)' eliminado$(NC)"

shell-kafka: ## Abre una shell en el contenedor de Kafka
	docker exec -it kafka bash

shell-zookeeper: ## Abre una shell en el contenedor de Zookeeper
	docker exec -it zookeeper bash
