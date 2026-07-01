.PHONY: up down logs test lint dev deploy

up:
	docker compose up --build -d

down:
	docker compose down -v

logs:
	docker compose logs -f

test:
	python -m pytest tests/ -v --cov=api --cov-fail-under=75

lint:
	python -m flake8 api/ dashboard/ tests/

dev:
	python -m uvicorn api.main:app --reload --port 8000 & python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501

deploy:
	bash scripts/deploy_container_app.sh
