#!/bin/bash
# Launch script for Personal Monitoring Dashboard MVP
# Usage: ./launch.sh [start|stop|restart|status]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default ports (can be overridden via environment)
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export REDIS_PORT=${REDIS_PORT:-6379}
export BACKEND_PORT=${BACKEND_PORT:-8000}

# Configuration
export POSTGRES_USER=${POSTGRES_USER:-dashy}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-changeme}
export POSTGRES_DB=${POSTGRES_DB:-dashy}
export SECRET_KEY=${SECRET_KEY:-changeme-secret-key-min-32-characters}

COMPOSE_FILE="docker-compose.yml"
PROJECT_NAME="dashy"

print_banner() {
    echo -e "${BLUE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          Personal Monitoring Dashboard - MVP                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

check_docker() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        echo -e "${RED}❌ Docker Compose is not installed${NC}"
        exit 1
    fi
    echo -e "${GREEN}✓ Docker and Docker Compose available${NC}"
}

check_ports() {
    echo -e "${BLUE}Checking ports...${NC}"
    
    local ports=($POSTGRES_PORT $REDIS_PORT $BACKEND_PORT)
    local names=("PostgreSQL" "Redis" "Backend")
    local conflict=false
    
    for i in "${!ports[@]}"; do
        local port=${ports[$i]}
        local name=${names[$i]}
        
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || netstat -tuln 2>/dev/null | grep -q ":$port "; then
            echo -e "${YELLOW}⚠ Port $port is already in use${NC}"
            conflict=true
        else
            echo -e "${GREEN}✓ Port $port available for $name${NC}"
        fi
    done
    
    if [ "$conflict" = true ]; then
        echo ""
        echo -e "${YELLOW}To use different ports, set environment variables:${NC}"
        echo "  POSTGRES_PORT=5433 REDIS_PORT=6380 BACKEND_PORT=8080 ./launch.sh"
        echo ""
    fi
}

start_services() {
    print_banner
    check_docker
    check_ports
    
    echo ""
    echo -e "${BLUE}Starting services...${NC}"
    echo "  PostgreSQL: port $POSTGRES_PORT"
    echo "  Redis:      port $REDIS_PORT"
    echo "  Backend:    port $BACKEND_PORT"
    echo ""
    
    # Build and start
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up --build -d
    
    echo ""
    echo -e "${BLUE}Waiting for services to be healthy...${NC}"
    
    # Wait for backend to be ready
    local retries=30
    local count=0
    while [ $count -lt $retries ]; do
        if curl -s http://localhost:$BACKEND_PORT/health > /dev/null 2>&1; then
            echo ""
            echo -e "${GREEN}✓ All services are ready!${NC}"
            echo ""
            echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
            echo "  Dashboard:    http://localhost:$BACKEND_PORT/dashboard.html"
            echo "  API Docs:     http://localhost:$BACKEND_PORT/docs"
            echo "  Health Check: http://localhost:$BACKEND_PORT/health"
            echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
            echo ""
            echo "To view logs: ./launch.sh logs"
            echo "To stop:      ./launch.sh stop"
            return 0
        fi
        echo -n "."
        sleep 2
        count=$((count + 1))
    done
    
    echo ""
    echo -e "${RED}❌ Services did not become healthy in time${NC}"
    echo "Check logs with: ./launch.sh logs"
    return 1
}

stop_services() {
    echo -e "${BLUE}Stopping services...${NC}"
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down
    echo -e "${GREEN}✓ Services stopped${NC}"
}

show_status() {
    echo -e "${BLUE}Service Status:${NC}"
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE ps
    
    echo ""
    echo -e "${BLUE}Health Check:${NC}"
    if curl -s http://localhost:$BACKEND_PORT/health 2>/dev/null | grep -q "healthy"; then
        echo -e "${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "${YELLOW}⚠ Backend is not responding${NC}"
    fi
}

show_logs() {
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE logs -f
}

reset_data() {
    echo -e "${RED}⚠ This will delete all database data!${NC}"
    read -p "Are you sure? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down -v
        echo -e "${GREEN}✓ Data volumes removed${NC}"
    else
        echo "Cancelled"
    fi
}

# Main command handler
case "${1:-start}" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        stop_services
        sleep 2
        start_services
        ;;
    status)
        show_status
        ;;
    logs)
        show_logs
        ;;
    reset)
        reset_data
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status|logs|reset]"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - View service logs"
        echo "  reset   - Stop and delete all data (DANGER)"
        echo ""
        echo "Environment variables:"
        echo "  POSTGRES_PORT - PostgreSQL port (default: 5432)"
        echo "  REDIS_PORT    - Redis port (default: 6379)"
        echo "  BACKEND_PORT  - Backend API port (default: 8000)"
        exit 1
        ;;
esac
