.PHONY: install dev test deploy clean

install:
	pip install -r requirements-dev.txt
	python -m playwright install chromium
	pre-commit install

dev:
	python run_local.py

test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

format:
	black app/ tests/
	flake8 app/ tests/

deploy:
	vercel --prod

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/

setup-db:
	python scripts/init_db.py

# Additional helpful commands
lint:
	pre-commit run --all-files

update-deps:
	pip install --upgrade -r requirements-dev.txt

check:
	python -m pytest
	python -m flake8 app tests
	python -m black --check app tests
