.PHONY: help build up down start stop restart logs clean demo create-topics status shell test

# Variables
DOCKER_COMPOSE = docker-compose
PYTHON = python3

# Colores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostrar esta ayuda
	@echo "$(GREEN)Kafka Advanced Example - E-Commerce System$(NC)"
	@echo "=============================================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

build: ## Construir imágenes Docker
	@echo "$(YELLOW)🔨 Building Docker images...$(NC)"
	$(DOCKER_COMPOSE) build

up: ## Levantar todos los servicios
	@echo "$(YELLOW)🚀 Starting all services...$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✅ Services started!$(NC)"
	@$(MAKE) status

down: ## Detener todos los servicios
	@echo "$(YELLOW)🛑 Stopping all services...$(NC)"
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)✅ Services stopped!$(NC)"

start: up ## Alias para 'up'

stop: down ## Alias para 'down'

restart: ## Reiniciar todos los servicios
	@echo "$(YELLOW)🔄 Restarting services...$(NC)"
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)✅ Services restarted!$(NC)"

logs: ## Ver logs de todos los servicios
	$(DOCKER_COMPOSE) logs -f

logs-order: ## Ver logs del servicio de órdenes
	$(DOCKER_COMPOSE) logs -f order-service

logs-inventory: ## Ver logs del servicio de inventario
	$(DOCKER_COMPOSE) logs -f inventory-service

logs-notification: ## Ver logs del servicio de notificaciones
	$(DOCKER_COMPOSE) logs -f notification-service

logs-analytics: ## Ver logs del servicio de analytics
	$(DOCKER_COMPOSE) logs -f analytics-service

logs-kafka: ## Ver logs de Kafka
	$(DOCKER_COMPOSE) logs -f kafka

status: ## Ver estado de los servicios
	@echo "$(YELLOW)📊 Service Status:$(NC)"
	@$(DOCKER_COMPOSE) ps

clean: ## Limpiar contenedores, volúmenes e imágenes
	@echo "$(RED)🧹 Cleaning up...$(NC)"
	$(DOCKER_COMPOSE) down -v --remove-orphans
	@echo "$(GREEN)✅ Cleanup complete!$(NC)"

demo: ## Ejecutar demostración completa
	@bash scripts/run_demo.sh

create-topics: ## Crear topics de Kafka
	@echo "$(YELLOW)📋 Creating Kafka topics...$(NC)"
	$(PYTHON) scripts/create_topics.py
	@echo "$(GREEN)✅ Topics created!$(NC)"

list-topics: ## Listar topics de Kafka
	@echo "$(YELLOW)📋 Listing Kafka topics...$(NC)"
	$(PYTHON) scripts/create_topics.py --list

create-order: ## Crear una orden de prueba
	@echo "$(YELLOW)📦 Creating test order...$(NC)"
	$(PYTHON) services/order_service.py

shell-order: ## Abrir shell en el contenedor de órdenes
	$(DOCKER_COMPOSE) exec order-service /bin/bash

shell-inventory: ## Abrir shell en el contenedor de inventario
	$(DOCKER_COMPOSE) exec inventory-service /bin/bash

shell-kafka: ## Abrir shell en el contenedor de Kafka
	$(DOCKER_COMPOSE) exec kafka /bin/bash

kafka-ui: ## Abrir Kafka UI en el navegador
	@echo "$(GREEN)🌐 Opening Kafka UI...$(NC)"
	@echo "$(YELLOW)Visit: http://localhost:8080$(NC)"
	@command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8080 || \
	 command -v open >/dev/null 2>&1 && open http://localhost:8080 || \
	 echo "Please open http://localhost:8080 in your browser"

test-flow: ## Probar flujo completo de E-Commerce
	@echo "$(YELLOW)🧪 Testing complete flow...$(NC)"
	@echo ""
	@echo "$(GREEN)1. Creating order...$(NC)"
	@$(PYTHON) services/order_service.py
	@echo ""
	@echo "$(GREEN)2. Check logs in analytics service to see processing$(NC)"
	@sleep 3
	@$(MAKE) logs-analytics

install-deps: ## Instalar dependencias Python localmente
	@echo "$(YELLOW)📦 Installing Python dependencies...$(NC)"
	pip install -r requirements.txt
	@echo "$(GREEN)✅ Dependencies installed!$(NC)"

health: ## Verificar salud de los servicios
	@echo "$(YELLOW)🏥 Checking service health...$(NC)"
	@echo ""
	@echo "Kafka:"
	@docker exec adv-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1 && \
		echo "  $(GREEN)✅ Kafka is healthy$(NC)" || echo "  $(RED)❌ Kafka is unhealthy$(NC)"
	@echo ""
	@echo "Services:"
	@docker ps --filter "name=adv-" --format "table {{.Names}}\t{{.Status}}" | tail -n +2 | while read name status; do \
		if echo "$$status" | grep -q "Up"; then \
			echo "  $(GREEN)✅ $$name$(NC)"; \
		else \
			echo "  $(RED)❌ $$name$(NC)"; \
		fi; \
	done

setup: build create-topics ## Configuración inicial completa
	@echo "$(GREEN)✅ Setup complete! Run 'make demo' to start.$(NC)"

# Target por defecto
.DEFAULT_GOAL := help
