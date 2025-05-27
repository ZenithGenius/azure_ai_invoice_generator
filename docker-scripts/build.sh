#!/bin/bash

# Azure AI Foundry Invoice Management System - Docker Build Script
# Professional deployment automation with comprehensive error handling

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly WHITE='\033[1;37m'
readonly NC='\033[0m' # No Color

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly COMPOSE_FILE="$PROJECT_ROOT/docker-compose.yml"
readonly COMPOSE_PROD_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
readonly ENV_FILE="$PROJECT_ROOT/.env"
readonly LOG_FILE="$PROJECT_ROOT/logs/docker-build.log"

# Service ports
readonly APP_PORT=8501
readonly REDIS_PORT=6380  # Updated from 6379 to 6380
readonly REDIS_GUI_PORT=8081
readonly PROMETHEUS_PORT=9090
readonly GRAFANA_PORT=3000

# Ensure logs directory exists
mkdir -p "$(dirname "$LOG_FILE")"

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

# Print colored output
print_status() {
    local color="$1"
    local message="$2"
    echo -e "${color}${message}${NC}"
}

print_header() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                    Azure AI Foundry Invoice Management                      ║"
    echo "║                         Docker Deployment System                            ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

print_success() {
    print_status "$GREEN" "[SUCCESS] $1"
    log "INFO" "$1"
}

print_error() {
    print_status "$RED" "[ERROR] $1"
    log "ERROR" "$1"
}

print_warning() {
    print_status "$YELLOW" "[WARNING] $1"
    log "WARN" "$1"
}

print_info() {
    print_status "$BLUE" "[INFO] $1"
    log "INFO" "$1"
}

# Check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_success "Docker is running"
}

# Check if docker-compose is available
check_docker_compose() {
    if ! command -v docker-compose >/dev/null 2>&1; then
        print_error "docker-compose is not installed. Please install docker-compose and try again."
        exit 1
    fi
    print_success "docker-compose is available"
}

# Check if .env file exists
check_env_file() {
    if [[ ! -f "$ENV_FILE" ]]; then
        print_warning ".env file not found. Creating from env.example..."
        if [[ -f "$PROJECT_ROOT/env.example" ]]; then
            cp "$PROJECT_ROOT/env.example" "$ENV_FILE"
            print_info "Please edit .env file with your Azure credentials before starting services"
        else
            print_error "env.example file not found. Cannot create .env file."
            exit 1
        fi
    else
        print_success ".env file found"
    fi
}

# Check if required ports are available
check_ports() {
    local ports=("$APP_PORT" "$REDIS_PORT" "$REDIS_GUI_PORT" "$PROMETHEUS_PORT" "$GRAFANA_PORT")
    local unavailable_ports=()
    
    for port in "${ports[@]}"; do
        if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            unavailable_ports+=("$port")
        fi
    done
    
    if [[ ${#unavailable_ports[@]} -gt 0 ]]; then
        print_warning "The following ports are in use: ${unavailable_ports[*]}"
        print_info "Services using these ports may conflict with the application"
        print_info "Redis is configured to use port $REDIS_PORT (external) to avoid conflicts"
    else
        print_success "All required ports are available"
    fi
}

# Build Docker images
build_images() {
    print_info "Building Docker images..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose -f "$COMPOSE_FILE" build --no-cache; then
        print_success "Docker images built successfully"
    else
        print_error "Failed to build Docker images"
        exit 1
    fi
}

# Build with docker-compose
build_compose() {
    print_info "Building with docker-compose..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose -f "$COMPOSE_FILE" build; then
        print_success "Docker Compose build completed successfully"
    else
        print_error "Docker Compose build failed"
        exit 1
    fi
}

# Start services
start_services() {
    print_info "Starting services..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose -f "$COMPOSE_FILE" up -d; then
        print_success "Services started successfully"
        show_service_urls
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Start services with monitoring
start_with_monitoring() {
    print_info "Starting services with full monitoring stack..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose -f "$COMPOSE_FILE" --profile monitoring up -d; then
        print_success "Services with monitoring started successfully"
        show_service_urls_with_monitoring
    else
        print_error "Failed to start services with monitoring"
        exit 1
    fi
}

# Stop services
stop_services() {
    print_info "Stopping services..."
    
    cd "$PROJECT_ROOT"
    
    if docker-compose -f "$COMPOSE_FILE" down; then
        print_success "Services stopped successfully"
    else
        print_error "Failed to stop services"
        exit 1
    fi
}

# Restart services
restart_services() {
    print_info "Restarting services..."
    stop_services
    start_services
}

# Show logs
show_logs() {
    local service="$1"
    
    cd "$PROJECT_ROOT"
    
    if [[ -n "$service" ]]; then
        print_info "Showing logs for service: $service"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        print_info "Showing logs for all services"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Health check
health_check() {
    print_info "Performing health check..."
    
    cd "$PROJECT_ROOT"
    
    # Check if containers are running
    local containers=(
        "azure-invoice-app"
        "azure-invoice-redis"
    )
    
    local healthy=true
    
    for container in "${containers[@]}"; do
        if docker ps --filter "name=$container" --filter "status=running" | grep -q "$container"; then
            print_success "Container $container is running"
        else
            print_error "Container $container is not running"
            healthy=false
        fi
    done
    
    # Check application health endpoint
    if curl -f http://localhost:$APP_PORT/_stcore/health >/dev/null 2>&1; then
        print_success "Application health check passed"
    else
        print_warning "Application health check failed (may still be starting)"
        healthy=false
    fi
    
    # Check Redis connectivity
    if docker exec azure-invoice-redis redis-cli ping >/dev/null 2>&1; then
        print_success "Redis connectivity check passed"
    else
        print_error "Redis connectivity check failed"
        healthy=false
    fi
    
    if $healthy; then
        print_success "All health checks passed"
    else
        print_warning "Some health checks failed"
    fi
}

# Cleanup
cleanup() {
    print_info "Cleaning up Docker resources..."
    
    cd "$PROJECT_ROOT"
    
    # Stop and remove containers, networks, volumes
    docker-compose -f "$COMPOSE_FILE" down -v --remove-orphans
    
    # Remove unused images
    docker image prune -f
    
    # Remove unused volumes
    docker volume prune -f
    
    # Remove unused networks
    docker network prune -f
    
    print_success "Cleanup completed"
}

# Show service URLs
show_service_urls() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                              Service URLs                                    ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║ 🚀 Main Application:    http://localhost:$APP_PORT                                ║"
    echo "║ 📊 Redis (Internal):    redis://localhost:$REDIS_PORT                             ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Show service URLs with monitoring
show_service_urls_with_monitoring() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════════════════════════════╗"
    echo "║                              Service URLs                                    ║"
    echo "╠══════════════════════════════════════════════════════════════════════════════╣"
    echo "║ 🚀 Main Application:    http://localhost:$APP_PORT                                ║"
    echo "║ 📊 Redis GUI:           http://localhost:$REDIS_GUI_PORT                          ║"
    echo "║ 📈 Prometheus:          http://localhost:$PROMETHEUS_PORT                         ║"
    echo "║ 📊 Grafana:             http://localhost:$GRAFANA_PORT                            ║"
    echo "║ 🔧 Redis (Internal):    redis://localhost:$REDIS_PORT                             ║"
    echo "╚══════════════════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}Default Credentials:${NC}"
    echo -e "  Grafana:        admin / admin123"
    echo -e "  Redis GUI:      admin / admin123"
}

# Show usage
show_usage() {
    echo -e "${WHITE}"
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build                 Build Docker images only"
    echo "  build-compose         Build with docker-compose"
    echo "  start                 Start basic services (app + redis)"
    echo "  start-monitoring      Start with full monitoring stack"
    echo "  stop                  Stop all services"
    echo "  restart               Restart all services"
    echo "  logs [service]        Show logs (optionally for specific service)"
    echo "  health                Check service health"
    echo "  cleanup               Clean up Docker resources"
    echo "  help                  Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start                    # Start basic services"
    echo "  $0 start-monitoring         # Start with monitoring"
    echo "  $0 logs invoice-app         # Show app logs"
    echo "  $0 logs                     # Show all logs"
    echo -e "${NC}"
}

# Main function
main() {
    print_header
    
    # Pre-flight checks
    check_docker
    check_docker_compose
    check_env_file
    check_ports
    
    # Handle commands
    case "${1:-help}" in
        "build")
            build_images
            ;;
        "build-compose")
            build_compose
            ;;
        "start")
            start_services
            ;;
        "start-monitoring")
            start_with_monitoring
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "logs")
            show_logs "${2:-}"
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"--help"|"-h")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@" 