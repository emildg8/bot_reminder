.PHONY: install install-dev test lint run docker-up docker-down deploy backup restore

install:
	pip install -r requirements.txt

backup:
	python scripts/backup_db.py

restore:
	python scripts/restore_db.py

install-dev:
	pip install -r requirements-dev.txt

test:
	python -m pytest -v

lint:
	ruff check bot tests

run:
	python -m bot.main

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

deploy:
	git pull origin main
	pip install -r requirements.txt -q
	@echo "Restart bot process manually or via panel"

avatar:
	python scripts/set_bot_avatar.py
