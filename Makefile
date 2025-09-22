COMPOSE = docker compose -f compose.yaml

.PHONY: build up down logs migrate createsuperuser shell test ps

build:
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
