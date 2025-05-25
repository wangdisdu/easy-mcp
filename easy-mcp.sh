#!/bin/bash

# Easy MCP Docker Compose Management Script
# Version: 1.0.0
# Description: CLI tool for managing Easy MCP deployment with different database backends

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
DB_TYPE="sqlite"
ACTION=""
COMPOSE_FILE=""
ENV_FILE=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    cat << EOF
Easy MCP Docker Compose Management Tool

Usage: $0 [OPTIONS] COMMAND

Commands:
    build       Build Docker images
    deploy      Deploy services
    start       Start services
    stop        Stop services
    restart     Restart services
    logs        Show service logs
    status      Show service status
    health      Run health checks
    clean       Clean up containers and volumes
    backup      Backup database (SQLite only)
    restore     Restore database (SQLite only)

Options:
    -d, --database TYPE    Database type: sqlite, postgres, mysql (default: sqlite)
    -h, --help            Show this help message

Examples:
    $0 build                          # Build with SQLite
    $0 -d postgres deploy             # Deploy with PostgreSQL
    $0 -d mysql start                 # Start with MySQL
    $0 logs                           # Show logs
    $0 clean                          # Clean up everything

EOF
}

# Function to set compose file and env file based on database type
set_compose_files() {
    case $DB_TYPE in
        sqlite)
            COMPOSE_FILE="docker/docker-compose.sqlite.yml"
            ENV_FILE="docker/.env.sqlite"
            ;;
        postgres|postgresql)
            COMPOSE_FILE="docker/docker-compose.postgres.yml"
            ENV_FILE="docker/.env.postgres"
            DB_TYPE="postgres"
            ;;
        mysql)
            COMPOSE_FILE="docker/docker-compose.mysql.yml"
            ENV_FILE="docker/.env.mysql"
            ;;
        *)
            print_error "Unsupported database type: $DB_TYPE"
            print_info "Supported types: sqlite, postgres, mysql"
            exit 1
            ;;
    esac

    if [[ ! -f "$COMPOSE_FILE" ]]; then
        print_error "Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    if [[ ! -f "$ENV_FILE" ]]; then
        print_error "Environment file not found: $ENV_FILE"
        exit 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        print_error "Docker Compose is not installed or not in PATH"
        exit 1
    fi

    # Use docker compose if available, otherwise fall back to docker-compose
    if docker compose version &> /dev/null; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
}

# Function to create necessary directories
create_directories() {
    print_info "Creating necessary directories..."
    mkdir -p data logs scripts

    # Set proper permissions for data directory
    if [[ "$DB_TYPE" == "sqlite" ]]; then
        chmod 755 data
    fi
}

# Function to build images
build_images() {
    print_info "Building Docker images for $DB_TYPE deployment..."

    # Check if static files exist
    if [[ ! -d "static" ]]; then
        print_warning "Static directory not found. Frontend files may not be available."
    else
        print_info "Static files found in static/ directory"
    fi

    # Build Docker image
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build

    print_success "Docker images built successfully"
}

# Function to deploy services
deploy_services() {
    print_info "Deploying Easy MCP with $DB_TYPE database..."

    create_directories

    # Copy environment file to .env for docker-compose
    cp "$ENV_FILE" .env

    # Start services
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d

    print_success "Easy MCP deployed successfully"
    print_info "Application will be available at: http://localhost:8000"

    if [[ "$DB_TYPE" != "sqlite" ]]; then
        print_info "Database will be available at:"
        case $DB_TYPE in
            postgres)
                print_info "  PostgreSQL: localhost:5432"
                ;;
            mysql)
                print_info "  MySQL: localhost:3306"
                ;;
        esac
    fi
}

# Function to start services
start_services() {
    print_info "Starting Easy MCP services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" start
    print_success "Services started"
}

# Function to stop services
stop_services() {
    print_info "Stopping Easy MCP services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop
    print_success "Services stopped"
}

# Function to restart services
restart_services() {
    print_info "Restarting Easy MCP services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" restart
    print_success "Services restarted"
}

# Function to show logs
show_logs() {
    print_info "Showing logs for Easy MCP services..."
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" logs -f
}

# Function to show status
show_status() {
    print_info "Easy MCP service status:"
    $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps
}

# Function to run health checks
run_health_checks() {
    print_info "Running health checks..."
    if [[ -f "scripts/health-check.sh" ]]; then
        bash scripts/health-check.sh
    else
        print_error "Health check script not found: scripts/health-check.sh"
        exit 1
    fi
}

# Function to clean up
clean_up() {
    print_warning "This will remove all containers, networks, and volumes. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Cleaning up Easy MCP deployment..."
        $DOCKER_COMPOSE -f "$COMPOSE_FILE" --env-file "$ENV_FILE" down -v --remove-orphans

        # Remove images
        docker image prune -f

        print_success "Cleanup completed"
    else
        print_info "Cleanup cancelled"
    fi
}

# Function to backup database (SQLite only)
backup_database() {
    if [[ "$DB_TYPE" != "sqlite" ]]; then
        print_error "Backup is only supported for SQLite database"
        exit 1
    fi

    if [[ ! -f "data/easy_mcp.db" ]]; then
        print_error "Database file not found: data/easy_mcp.db"
        exit 1
    fi

    BACKUP_FILE="backup/easy_mcp_$(date +%Y%m%d_%H%M%S).db"
    mkdir -p backup

    print_info "Creating database backup..."
    cp "data/easy_mcp.db" "$BACKUP_FILE"

    print_success "Database backed up to: $BACKUP_FILE"
}

# Function to restore database (SQLite only)
restore_database() {
    if [[ "$DB_TYPE" != "sqlite" ]]; then
        print_error "Restore is only supported for SQLite database"
        exit 1
    fi

    if [[ ! -d "backup" ]]; then
        print_error "Backup directory not found"
        exit 1
    fi

    print_info "Available backups:"
    ls -la backup/*.db 2>/dev/null || {
        print_error "No backup files found"
        exit 1
    }

    echo -n "Enter backup file name: "
    read -r backup_file

    if [[ ! -f "backup/$backup_file" ]]; then
        print_error "Backup file not found: backup/$backup_file"
        exit 1
    fi

    print_warning "This will overwrite the current database. Are you sure? (y/N)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        print_info "Restoring database from backup..."
        cp "backup/$backup_file" "data/easy_mcp.db"
        print_success "Database restored from: backup/$backup_file"
    else
        print_info "Restore cancelled"
    fi
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--database)
            DB_TYPE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        build|deploy|start|stop|restart|logs|status|health|clean|backup|restore)
            ACTION="$1"
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if action is provided
if [[ -z "$ACTION" ]]; then
    print_error "No action specified"
    show_usage
    exit 1
fi

# Main execution
main() {
    print_info "Easy MCP Docker Management Tool"
    print_info "Database: $DB_TYPE"
    print_info "Action: $ACTION"
    echo

    check_prerequisites
    set_compose_files

    case $ACTION in
        build)
            build_images
            ;;
        deploy)
            build_images
            deploy_services
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        health)
            run_health_checks
            ;;
        clean)
            clean_up
            ;;
        backup)
            backup_database
            ;;
        restore)
            restore_database
            ;;
        *)
            print_error "Unknown action: $ACTION"
            show_usage
            exit 1
            ;;
    esac
}

# Run main function
main
