#!/bin/bash
echo "Running linting tools..."
ruff check --fix .
black .
isort .
echo "Linting complete!"
