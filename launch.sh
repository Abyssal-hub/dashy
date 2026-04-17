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

find_available_port() {
    local start_port=$1
    local port=$start_port
    
    while [ $port -lt 65535 ]; do
        # Prefer an actual bind test — more reliable than lsof/netstat,
        # especially when Docker Desktop holds stale forwarding entries.
        if command -v python3 &> /dev/null; then
            if python3 -c "import socket, sys; s=socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1); s.bind(('0.0.0.0',$port)); s.close(); sys.exit(0)" 2>/dev/null; then
                echo $port
                return 0
            fi
        else
            if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 && \
               ! netstat -tuln 2>/dev/null | grep -q ":$port "; then
                echo $port
                return 0
            fi
        fi
        port=$((port + 1))
    done
    
    echo -e "${RED}❌ No available ports found starting from $start_port${NC}"
    return 1
}

check_and_assign_ports() {
    echo -e "${BLUE}Checking and assigning ports...${NC}"
    
    # Try to use environment-provided ports first, then defaults
    local requested_postgres=${POSTGRES_PORT:-5432}
    local requested_redis=${REDIS_PORT:-6379}
    local requested_backend=${BACKEND_PORT:-8000}
    
    # Check and find available ports
    export POSTGRES_PORT=$(find_available_port $requested_postgres)
    export BACKEND_PORT=$(find_available_port $requested_backend)
    
    # Show port assignments
    echo ""
    echo -e "${GREEN}Port assignments:${NC}"
    [ "$POSTGRES_PORT" != "$requested_postgres" ] && \
        echo "  PostgreSQL: $requested_postgres → ${GREEN}$POSTGRES_PORT${NC} (auto-assigned)" || \
        echo "  PostgreSQL: ${GREEN}$POSTGRES_PORT${NC}"
    echo "  Redis:      ${GREEN}(internal only)${NC}"
    [ "$BACKEND_PORT" != "$requested_backend" ] && \
        echo "  Backend:    $requested_backend → ${GREEN}$BACKEND_PORT${NC} (auto-assigned)" || \
        echo "  Backend:    ${GREEN}$BACKEND_PORT${NC}"
    echo ""
}

start_services() {
    print_banner
    check_docker
    
    local compose_retries=3
    local compose_attempt=1
    
    while [ $compose_attempt -le $compose_retries ]; do
        check_and_assign_ports
        
        echo -e "${BLUE}Starting services (attempt $compose_attempt/$compose_retries)...${NC}"
        
        # Build and start
        if docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up --build -d; then
            break
        fi
        
        if [ $compose_attempt -lt $compose_retries ]; then
            echo -e "${YELLOW}⚠ Docker Compose startup failed. Retrying with different ports...${NC}"
            docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null || true
            # Bump start ports so the next scan skips current assignments
            export POSTGRES_PORT=$((POSTGRES_PORT + 1))
            export REDIS_PORT=$((REDIS_PORT + 1))
            export BACKEND_PORT=$((BACKEND_PORT + 1))
            compose_attempt=$((compose_attempt + 1))
        else
            echo -e "${RED}❌ Docker Compose failed to start after $compose_retries attempts${NC}"
            return 1
        fi
    done
    
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

rebuild_services() {
    echo -e "${BLUE}Rebuilding services (no cache)...${NC}"
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE down 2>/dev/null || true
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE build --no-cache
    docker-compose -p $PROJECT_NAME -f $COMPOSE_FILE up -d
    echo -e "${GREEN}✓ Services rebuilt and started${NC}"
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
    rebuild)
        rebuild_services
        ;;
    reset)
        reset_data
        ;;
    *)
        echo "Usage: $0 [start|stop|restart|status|logs|rebuild|reset]"
        echo ""
        echo "Commands:"
        echo "  start   - Start all services (default)"
        echo "  stop    - Stop all services"
        echo "  restart - Restart all services"
        echo "  status  - Show service status"
        echo "  logs    - View service logs"
        echo "  rebuild - Rebuild and restart (use after Dockerfile changes)"
        echo "  reset   - Stop and delete all data (DANGER)"
        echo ""
        echo "Environment variables:"
        echo "  POSTGRES_PORT - PostgreSQL port (default: 5432)"
        echo "  REDIS_PORT    - Redis port (default: 6379)"
        echo "  BACKEND_PORT  - Backend API port (default: 8000)"
        exit 1
        ;;
esac
