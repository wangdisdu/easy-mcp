#!/bin/bash

# Health check script for Easy MCP services
# This script checks the health of all services and reports their status

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Function to check if a service is running
check_service() {
    local service_name=$1
    local container_name=$2
    
    if docker ps --format "table {{.Names}}" | grep -q "^${container_name}$"; then
        print_success "$service_name is running"
        return 0
    else
        print_error "$service_name is not running"
        return 1
    fi
}

# Function to check HTTP endpoint
check_http_endpoint() {
    local service_name=$1
    local url=$2
    local expected_status=${3:-200}
    
    if command -v curl &> /dev/null; then
        local status_code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
        if [[ "$status_code" == "$expected_status" ]]; then
            print_success "$service_name HTTP endpoint is healthy"
            return 0
        else
            print_error "$service_name HTTP endpoint returned status $status_code (expected $expected_status)"
            return 1
        fi
    else
        print_warning "curl not available, skipping HTTP check for $service_name"
        return 0
    fi
}

# Function to check database connectivity
check_database() {
    local db_type=$1
    
    case $db_type in
        postgres)
            if docker exec easy-mcp-postgres pg_isready -U easy_mcp -d easy_mcp &>/dev/null; then
                print_success "PostgreSQL database is healthy"
                return 0
            else
                print_error "PostgreSQL database is not responding"
                return 1
            fi
            ;;
        mysql)
            if docker exec easy-mcp-mysql mysqladmin ping -h localhost -u easy_mcp -peasy_mcp_password &>/dev/null; then
                print_success "MySQL database is healthy"
                return 0
            else
                print_error "MySQL database is not responding"
                return 1
            fi
            ;;
        sqlite)
            if [[ -f "data/easy_mcp.db" ]]; then
                print_success "SQLite database file exists"
                return 0
            else
                print_error "SQLite database file not found"
                return 1
            fi
            ;;
        *)
            print_warning "Unknown database type: $db_type"
            return 0
            ;;
    esac
}

# Function to check disk space
check_disk_space() {
    local threshold=90
    local usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    
    if [[ $usage -lt $threshold ]]; then
        print_success "Disk space usage: ${usage}% (healthy)"
        return 0
    else
        print_warning "Disk space usage: ${usage}% (above ${threshold}% threshold)"
        return 1
    fi
}

# Function to check memory usage
check_memory() {
    if command -v free &> /dev/null; then
        local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        local threshold=90
        
        if [[ $mem_usage -lt $threshold ]]; then
            print_success "Memory usage: ${mem_usage}% (healthy)"
            return 0
        else
            print_warning "Memory usage: ${mem_usage}% (above ${threshold}% threshold)"
            return 1
        fi
    else
        print_warning "free command not available, skipping memory check"
        return 0
    fi
}

# Function to detect database type from running containers
detect_database_type() {
    if docker ps --format "table {{.Names}}" | grep -q "easy-mcp-postgres"; then
        echo "postgres"
    elif docker ps --format "table {{.Names}}" | grep -q "easy-mcp-mysql"; then
        echo "mysql"
    else
        echo "sqlite"
    fi
}

# Main health check function
main() {
    print_info "Easy MCP Health Check"
    print_info "====================="
    echo
    
    local overall_status=0
    local db_type=$(detect_database_type)
    
    print_info "Detected database type: $db_type"
    echo
    
    # Check Easy MCP application
    print_info "Checking Easy MCP application..."
    if ! check_service "Easy MCP" "easy-mcp-app"; then
        overall_status=1
    fi
    
    if ! check_http_endpoint "Easy MCP API" "http://localhost:8000/api/v1/system"; then
        overall_status=1
    fi
    echo
    
    # Check database
    print_info "Checking database..."
    case $db_type in
        postgres)
            if ! check_service "PostgreSQL" "easy-mcp-postgres"; then
                overall_status=1
            fi
            ;;
        mysql)
            if ! check_service "MySQL" "easy-mcp-mysql"; then
                overall_status=1
            fi
            ;;
    esac
    
    if ! check_database "$db_type"; then
        overall_status=1
    fi
    echo
    
    # Check system resources
    print_info "Checking system resources..."
    if ! check_disk_space; then
        overall_status=1
    fi
    
    if ! check_memory; then
        overall_status=1
    fi
    echo
    
    # Overall status
    if [[ $overall_status -eq 0 ]]; then
        print_success "All health checks passed!"
    else
        print_error "Some health checks failed!"
    fi
    
    return $overall_status
}

# Run main function
main "$@"
