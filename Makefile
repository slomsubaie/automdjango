COMPOSE = docker compose -f compose.yaml

.PHONY: build up down logs migrate createsuperuser shell test ps clean help build-windows build-macos build-linux

# Main build target - detects OS and calls appropriate build target
build:
ifeq ($(OS),Windows_NT)
	@echo "Detected Windows OS"
	@$(MAKE) build-windows
else
	UNAME_S := $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		@echo "Detected macOS"
		@$(MAKE) build-macos
	else
		@echo "Detected Linux"
		@$(MAKE) build-linux
	endif
endif

# Windows build process
build-windows:
	@echo "Checking Python installation on Windows..."
	@python --version >nul 2>&1 || (echo "Python not found. Installing Python via Chocolatey..." && powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))" && choco install python -y)
	@echo "Creating virtual environment for Windows..."
	python -m venv .venv
	@echo "Activating virtual environment and installing requirements..."
	.venv\Scripts\activate && python -m pip install --upgrade pip && python -m pip install -r requirements.txt
	@echo "Building Docker containers..."
	$(COMPOSE) build --pull

# macOS build process
build-macos:
	@echo "Checking Python installation on macOS..."
	@python3 --version >/dev/null 2>&1 || (echo "Python3 not found. Installing Python via Homebrew..." && /bin/bash -c "$$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew install python)
	@echo "Creating virtual environment for macOS..."
	python3 -m venv .venv
	@echo "Activating virtual environment and installing requirements..."
	.venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
	@echo "Building Docker containers..."
	$(COMPOSE) build --pull

# Linux build process
build-linux:
	@echo "Checking Python installation on Linux..."
	@python3 --version >/dev/null 2>&1 || (echo "Python3 not found. Installing Python via package manager..." && (command -v apt-get >/dev/null 2>&1 && (sudo apt-get update && sudo apt-get install -y python3 python3-pip python3-venv) || (command -v yum >/dev/null 2>&1 && sudo yum install -y python3 python3-pip) || (command -v dnf >/dev/null 2>&1 && sudo dnf install -y python3 python3-pip) || (command -v pacman >/dev/null 2>&1 && sudo pacman -S --noconfirm python python-pip) || echo "Unsupported Linux distribution. Please install Python3 manually."))
	@echo "Creating virtual environment for Linux..."
	python3 -m venv .venv
	@echo "Activating virtual environment and installing requirements..."
	.venv/bin/activate && python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt
	@echo "Building Docker containers..."
	$(COMPOSE) build --pull

up:
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down -v

logs:
	$(COMPOSE) logs -f

migrate:
	$(COMPOSE) run --rm web python manage.py migrate

createsuperuser:
	$(COMPOSE) run --rm web python manage.py createsuperuser

shell:
	$(COMPOSE) run --rm web python manage.py shell

test:
	$(COMPOSE) run --rm web pytest 

ps:
	$(COMPOSE) ps

# Clean up virtual environment and containers
clean:
ifeq ($(OS),Windows_NT)
	if exist .venv rmdir /s /q .venv
else
	rm -rf .venv
endif
	$(COMPOSE) down -v --remove-orphans

# Show help
help:
	@echo "Available targets:"
	@echo "  build         - Detect OS, install Python (if needed), create venv, install requirements, and build Docker containers"
	@echo "  build-windows - Windows-specific build process (installs Python via Chocolatey if needed)"
	@echo "  build-macos   - macOS-specific build process (installs Python via Homebrew if needed)"
	@echo "  build-linux   - Linux-specific build process (installs Python via package manager if needed)"
	@echo "  up            - Start containers"
	@echo "  down          - Stop containers and remove volumes"
	@echo "  logs          - Show container logs"
	@echo "  migrate       - Run database migrations"
	@echo "  createsuperuser - Create Django superuser"
	@echo "  shell         - Open Django shell"
	@echo "  test          - Run tests"
	@echo "  ps            - Show running containers"
	@echo "  clean         - Remove virtual environment and containers"
	@echo "  help          - Show this help message"
	@echo ""
	@echo "Note: The build process will automatically install Python if not found on your system."
	@echo "Windows: Uses Chocolatey package manager"
	@echo "macOS: Uses Homebrew package manager"
	@echo "Linux: Uses apt-get, yum, dnf, or pacman depending on your distribution"
