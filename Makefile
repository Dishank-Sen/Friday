.PHONY: build up down test lint

build:
	docker build -t friday-webtop:local -f docker/Dockerfile .

up:
	python -m friday up

down:
	python -m friday down

test:
	pytest

lint:
	ruff check .
