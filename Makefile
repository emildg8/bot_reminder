.PHONY: help install install-dev test lint run docker-up docker-down deploy backup restore avatar verify migrate

help:
	@echo "bot_reminder — make targets:"
	@echo "  install-dev  pip install requirements-dev.txt"
	@echo "  test         pytest with coverage gate 65%%"
	@echo "  lint         ruff check"
	@echo "  verify       ops artifacts check"
	@echo "  migrate      alembic upgrade head"
	@echo "  run          python -m bot.main"
	@echo "  backup       DB backup to data/backups/"
	@echo "  restore      restore latest backup"
	@echo "  deploy       hint for GitHub secrets setup"
	@echo "  docker-up    docker compose up -d --build"

install:
	pip install -r requirements.txt

backup:
	python scripts/backup_db.py

restore:
	python scripts/restore_db.py

install-dev:
	pip install -r requirements-dev.txt

test:
	python -m pytest -v --cov=bot --cov-fail-under=65

lint:
	ruff check bot tests

run:
	python -m bot.main

verify:
	python scripts/verify_ops.py

migrate:
	python scripts/migrate_db.py

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down

deploy:
	@echo "One-time: copy .env.deploy.local.example → .env.deploy.local, then:"
	@echo "  .\\scripts\\setup_github_deploy.ps1"
	@echo "Push to main triggers CI deploy (see .github/DEPLOY.md)"

avatar:
	python scripts/set_bot_avatar.py
