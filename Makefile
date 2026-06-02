.PHONY: help install install-dev test lint run docker-up docker-down deploy backup restore avatar verify migrate smoke-nlp smoke-stars check-deploy

help:
	@echo "bot_reminder — make targets:"
	@echo "  install-dev  pip install requirements-dev.txt"
	@echo "  test         pytest with coverage gate 65%%"
	@echo "  lint         ruff check"
	@echo "  verify       ops artifacts check"
	@echo "  smoke-nlp    key NLP phrases (post-deploy)"
	@echo "  smoke-stars  Stars tips parse + passthrough"
	@echo "  check-deploy version + GitHub main (+ Telegram if BOT_TOKEN)"
	@echo "  test-count   pytest --collect-only"
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

smoke-nlp:
	python scripts/smoke_nlp.py

smoke-stars:
	python scripts/smoke_stars.py

check-deploy:
	python scripts/check_deploy.py

test-count:
	python -m pytest --collect-only -q

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
