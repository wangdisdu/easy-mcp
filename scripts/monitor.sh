#!/bin/bash

# Monitoring script for Easy MCP services
# This script continuously monitors the health of services and can send alerts

set -e

# Configuration
MONITOR_INTERVAL=60  # Check interval in seconds
LOG_FILE="logs/monitor.log"
ALERT_EMAIL=""  # Set email for alerts
MAX_FAILURES=3  # Maximum consecutive failures before alert

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters for failures
declare -A failure_counts

# Function to print colored output with timestamp
log_message() {
    local level=$1
    local message=$2
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        INFO)
            echo -e "${BLUE}[$timestamp INFO]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        SUCCESS)
            echo -e "${GREEN}[$timestamp SUCCESS]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        WARNING)
            echo -e "${YELLOW}[$timestamp WARNING]${NC} $message" | tee -a "$LOG_FILE"
            ;;
        ERROR)
            echo -e "${RED}[$timestamp ERROR]${NC} $message" | tee -a "$LOG_FILE"
            ;;
    esac
}

# Function to send alert (placeholder - implement based on your needs)
send_alert() {
    local service=$1
    local message=$2
    
    log_message "ERROR" "ALERT: $service - $message"
    
    # Email alert (if configured)
    if [[ -n "$ALERT_EMAIL" ]] && command -v mail &> /dev/null; then
        echo "$message" | mail -s "Easy MCP Alert: $service" "$ALERT_EMAIL"
    fi
    
    # You can add other alert mechanisms here (Slack, Discord, etc.)
}

# Function to check service health
check_service_health() {
    local service_name=$1
    local check_command=$2
    
    if eval "$check_command" &>/dev/null; then
        failure_counts[$service_name]=0
        return 0
    else
        ((failure_counts[$service_name]++))
        
        if [[ ${failure_counts[$service_name]} -ge $MAX_FAILURES ]]; then
            send_alert "$service_name" "Service has failed $MAX_FAILURES consecutive health checks"
            failure_counts[$service_name]=0  # Reset counter after alert
        fi
        
        return 1
    fi
}

# Function to detect database type
detect_database_type() {
    if docker ps --format "table {{.Names}}" | grep -q "easy-mcp-postgres"; then
        echo "postgres"
    elif docker ps --format "table {{.Names}}" | grep -q "easy-mcp-mysql"; then
        echo "mysql"
    else
        echo "sqlite"
    fi
}

# Function to monitor services
monitor_services() {
    local db_type=$(detect_database_type)
    
    log_message "INFO" "Starting monitoring cycle (Database: $db_type)"
    
    # Check Easy MCP application
    if check_service_health "Easy MCP App" "docker ps --format 'table {{.Names}}' | grep -q 'easy-mcp-app'"; then
        log_message "SUCCESS" "Easy MCP App is running"
    else
        log_message "ERROR" "Easy MCP App is not running"
    fi
    
    # Check Easy MCP API endpoint
    if check_service_health "Easy MCP API" "curl -s -f http://localhost:8000/api/v1/system"; then
        log_message "SUCCESS" "Easy MCP API is responding"
    else
        log_message "ERROR" "Easy MCP API is not responding"
    fi
    
    # Check database based on type
    case $db_type in
        postgres)
            if check_service_health "PostgreSQL" "docker ps --format 'table {{.Names}}' | grep -q 'easy-mcp-postgres'"; then
                log_message "SUCCESS" "PostgreSQL container is running"
            else
                log_message "ERROR" "PostgreSQL container is not running"
            fi
            
            if check_service_health "PostgreSQL Connection" "docker exec easy-mcp-postgres pg_isready -U easy_mcp -d easy_mcp"; then
                log_message "SUCCESS" "PostgreSQL is accepting connections"
            else
                log_message "ERROR" "PostgreSQL is not accepting connections"
            fi
            ;;
        mysql)
            if check_service_health "MySQL" "docker ps --format 'table {{.Names}}' | grep -q 'easy-mcp-mysql'"; then
                log_message "SUCCESS" "MySQL container is running"
            else
                log_message "ERROR" "MySQL container is not running"
            fi
            
            if check_service_health "MySQL Connection" "docker exec easy-mcp-mysql mysqladmin ping -h localhost -u easy_mcp -peasy_mcp_password"; then
                log_message "SUCCESS" "MySQL is accepting connections"
            else
                log_message "ERROR" "MySQL is not accepting connections"
            fi
            ;;
        sqlite)
            if check_service_health "SQLite Database" "test -f data/easy_mcp.db"; then
                log_message "SUCCESS" "SQLite database file exists"
            else
                log_message "ERROR" "SQLite database file not found"
            fi
            ;;
    esac
    
    # Check disk space
    local disk_usage=$(df . | tail -1 | awk '{print $5}' | sed 's/%//')
    if [[ $disk_usage -lt 90 ]]; then
        log_message "SUCCESS" "Disk space usage: ${disk_usage}%"
    else
        log_message "WARNING" "High disk space usage: ${disk_usage}%"
        if [[ $disk_usage -gt 95 ]]; then
            send_alert "Disk Space" "Critical disk space usage: ${disk_usage}%"
        fi
    fi
    
    # Check memory usage (if available)
    if command -v free &> /dev/null; then
        local mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
        if [[ $mem_usage -lt 90 ]]; then
            log_message "SUCCESS" "Memory usage: ${mem_usage}%"
        else
            log_message "WARNING" "High memory usage: ${mem_usage}%"
            if [[ $mem_usage -gt 95 ]]; then
                send_alert "Memory" "Critical memory usage: ${mem_usage}%"
            fi
        fi
    fi
}

# Function to show usage
show_usage() {
    cat << EOF
Easy MCP Monitoring Script

Usage: $0 [OPTIONS]

Options:
    -i, --interval SECONDS    Monitoring interval in seconds (default: 60)
    -e, --email EMAIL         Email address for alerts
    -f, --failures COUNT      Max consecutive failures before alert (default: 3)
    -l, --log-file FILE       Log file path (default: logs/monitor.log)
    -h, --help               Show this help message

Examples:
    $0                                    # Start monitoring with defaults
    $0 -i 30 -e admin@example.com        # Monitor every 30 seconds with email alerts
    $0 --interval 120 --failures 5       # Custom interval and failure threshold

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        -e|--email)
            ALERT_EMAIL="$2"
            shift 2
            ;;
        -f|--failures)
            MAX_FAILURES="$2"
            shift 2
            ;;
        -l|--log-file)
            LOG_FILE="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Create logs directory if it doesn't exist
mkdir -p "$(dirname "$LOG_FILE")"

# Initialize failure counters
failure_counts["Easy MCP App"]=0
failure_counts["Easy MCP API"]=0
failure_counts["PostgreSQL"]=0
failure_counts["PostgreSQL Connection"]=0
failure_counts["MySQL"]=0
failure_counts["MySQL Connection"]=0
failure_counts["SQLite Database"]=0

# Main monitoring loop
main() {
    log_message "INFO" "Starting Easy MCP monitoring"
    log_message "INFO" "Monitor interval: ${MONITOR_INTERVAL}s"
    log_message "INFO" "Max failures before alert: $MAX_FAILURES"
    log_message "INFO" "Log file: $LOG_FILE"
    
    if [[ -n "$ALERT_EMAIL" ]]; then
        log_message "INFO" "Alert email: $ALERT_EMAIL"
    fi
    
    echo
    log_message "INFO" "Press Ctrl+C to stop monitoring"
    echo
    
    # Trap SIGINT to gracefully exit
    trap 'log_message "INFO" "Monitoring stopped"; exit 0' SIGINT
    
    while true; do
        monitor_services
        echo
        sleep "$MONITOR_INTERVAL"
    done
}

# Run main function
main
