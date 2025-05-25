# Easy MCP Makefile
# Provides convenient shortcuts for common Docker operations

.PHONY: help build deploy start stop restart logs status health clean backup restore

# Default database type
DB_TYPE ?= sqlite

# Help target
help:
	@echo "Easy MCP Docker Management"
	@echo ""
	@echo "Usage: make [target] [DB_TYPE=sqlite|postgres|mysql]"
	@echo ""
	@echo "Targets:"
	@echo "  build     Build Docker images"
	@echo "  deploy    Deploy services (build + start)"
	@echo "  start     Start services"
	@echo "  stop      Stop services"
	@echo "  restart   Restart services"
	@echo "  logs      Show service logs"
	@echo "  status    Show service status"
	@echo "  health    Run health checks"
	@echo "  clean     Clean up containers and volumes"
	@echo "  backup    Backup database (SQLite only)"
	@echo "  restore   Restore database (SQLite only)"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy                    # Deploy with SQLite"
	@echo "  make deploy DB_TYPE=postgres   # Deploy with PostgreSQL"
	@echo "  make logs DB_TYPE=mysql        # Show logs for MySQL deployment"

# Build images
build:
	./easy-mcp.sh -d $(DB_TYPE) build

# Deploy services
deploy:
	./easy-mcp.sh -d $(DB_TYPE) deploy

# Start services
start:
	./easy-mcp.sh -d $(DB_TYPE) start

# Stop services
stop:
	./easy-mcp.sh -d $(DB_TYPE) stop

# Restart services
restart:
	./easy-mcp.sh -d $(DB_TYPE) restart

# Show logs
logs:
	./easy-mcp.sh -d $(DB_TYPE) logs

# Show status
status:
	./easy-mcp.sh -d $(DB_TYPE) status

# Run health checks
health:
	./easy-mcp.sh -d $(DB_TYPE) health

# Clean up
clean:
	./easy-mcp.sh -d $(DB_TYPE) clean

# Backup database (SQLite only)
backup:
	./easy-mcp.sh -d $(DB_TYPE) backup

# Restore database (SQLite only)
restore:
	./easy-mcp.sh -d $(DB_TYPE) restore

# Development shortcuts
dev-sqlite:
	make deploy DB_TYPE=sqlite

dev-postgres:
	make deploy DB_TYPE=postgres

dev-mysql:
	make deploy DB_TYPE=mysql
