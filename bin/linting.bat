@echo off
echo Running linting tools...
ruff check --fix .
black .
isort .
echo Linting complete!
@echo on