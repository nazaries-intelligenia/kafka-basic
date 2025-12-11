#!/bin/bash

# Script para ejecutar una demostración completa del sistema

set -e

echo "🚀 Starting E-Commerce Kafka Demo"
echo "=================================="

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para esperar a que Kafka esté listo
wait_for_kafka() {
    echo -e "${YELLOW}⏳ Waiting for Kafka to be ready...${NC}"
    for i in {1..30}; do
        if docker exec adv-kafka kafka-broker-api-versions --bootstrap-server localhost:9092 &> /dev/null; then
            echo -e "${GREEN}✅ Kafka is ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    echo -e "\n❌ Kafka failed to start"
    exit 1
}

# Paso 1: Levantar infraestructura
echo -e "\n${YELLOW}Step 1: Starting infrastructure...${NC}"
docker-compose up -d zookeeper kafka kafka-ui

# Esperar a que Kafka esté listo
wait_for_kafka

# Paso 2: Crear topics
echo -e "\n${YELLOW}Step 2: Creating Kafka topics...${NC}"
sleep 5
python3 scripts/create_topics.py

# Paso 3: Levantar servicios
echo -e "\n${YELLOW}Step 3: Starting microservices...${NC}"
docker-compose up -d order-service inventory-service notification-service analytics-service

# Esperar a que los servicios estén listos
echo -e "${YELLOW}⏳ Waiting for services to initialize...${NC}"
sleep 10

# Paso 4: Crear órdenes de prueba
echo -e "\n${YELLOW}Step 4: Creating test orders...${NC}"
echo -e "${GREEN}This will create 3 sample orders${NC}"
python3 services/order_service.py

# Paso 5: Mostrar información útil
echo -e "\n${GREEN}=================================="
echo "✅ Demo is running!"
echo "==================================${NC}"
echo ""
echo "📊 Kafka UI: http://localhost:8080"
echo "   - View topics, messages, and consumer groups"
echo ""
echo "📋 Service logs:"
echo "   docker-compose logs -f order-service"
echo "   docker-compose logs -f inventory-service"
echo "   docker-compose logs -f notification-service"
echo "   docker-compose logs -f analytics-service"
echo ""
echo "🔍 View all logs: docker-compose logs -f"
echo ""
echo "🛑 Stop demo: docker-compose down"
echo ""
echo -e "${YELLOW}⚡ Watch the services process the orders in real-time!${NC}"

# Opcional: seguir logs de analytics
echo -e "\n${YELLOW}Following analytics service logs (Ctrl+C to exit):${NC}"
sleep 2
docker-compose logs -f analytics-service
