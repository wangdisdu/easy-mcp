# Frontend Makefile for Easy-MCP

# Variables
NODE_VERSION := $(shell node -v 2>/dev/null || echo "Node.js not installed")
NPM_VERSION := $(shell npm -v 2>/dev/null || echo "npm not installed")
DIST_DIR := dist
NODE_MODULES := node_modules

# Default target
.PHONY: all
all: build

# Check if Node.js and npm are installed
.PHONY: check-deps
check-deps:
	@echo "Checking dependencies..."
	@echo "Node.js version: $(NODE_VERSION)"
	@echo "npm version: $(NPM_VERSION)"
	@if [ "$(NODE_VERSION)" = "Node.js not installed" ]; then \
		echo "Error: Node.js is not installed. Please install Node.js before proceeding."; \
		exit 1; \
	fi
	@if [ "$(NPM_VERSION)" = "npm not installed" ]; then \
		echo "Error: npm is not installed. Please install npm before proceeding."; \
		exit 1; \
	fi
	@echo "All dependencies are installed."

# Install dependencies
.PHONY: install
install: check-deps
	@echo "Installing dependencies..."
	npm install
	@echo "Dependencies installed successfully."

# Development server
.PHONY: dev
dev: install
	@echo "Starting development server..."
	npm run dev

# Build for production
.PHONY: build
build: install
	@echo "Building for production..."
	npm run build
	@echo "Build completed successfully. Output in $(DIST_DIR) directory."

# Preview production build
.PHONY: preview
preview: build
	@echo "Previewing production build..."
	npm run preview

# Clean build artifacts
.PHONY: clean
clean:
	@echo "Cleaning build artifacts..."
	rm -rf $(DIST_DIR)
	@echo "Build artifacts cleaned successfully."

# Deep clean (remove node_modules and build artifacts)
.PHONY: clean-all
clean-all: clean
	@echo "Performing deep clean (removing node_modules)..."
	rm -rf $(NODE_MODULES)
	@echo "Deep clean completed successfully."

# Help target
.PHONY: help
help:
	@echo "Available targets:"
	@echo "  all        - Default target, same as 'build'"
	@echo "  check-deps - Check if Node.js and npm are installed"
	@echo "  install    - Install dependencies"
	@echo "  dev        - Start development server"
	@echo "  build      - Build for production"
	@echo "  preview    - Preview production build"
	@echo "  clean      - Remove build artifacts"
	@echo "  clean-all  - Remove build artifacts and node_modules"
	@echo "  help       - Show this help message"
