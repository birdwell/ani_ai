# Makefile for the Ani_AI project

.PHONY: setup install run generate baseline clean help

help:
	@echo "Available commands:"
	@echo "  make setup    - Create a virtual environment (venv)"
	@echo "  make install  - Install dependencies from requirements.txt"
	@echo "  make run      - Start the FastAPI server with uvicorn"
	@echo "  make generate - Generate embeddings (runs generate_embeddings.py)"
	@echo "  make baseline - Run baseline recommender (runs baseline_recommender.py)"
	@echo "  make clean    - Remove the virtual environment"

setup:
	python -m venv venv
	@echo "Virtual environment created in './venv'."

install:
	venv/bin/pip install --upgrade pip
	venv/bin/pip install -r requirements.txt

run:
	venv/bin/uvicorn main:app --reload

generate:
	venv/bin/python generate_embeddings.py

baseline:
	venv/bin/python baseline_recommender.py

clean:
	rm -rf venv 