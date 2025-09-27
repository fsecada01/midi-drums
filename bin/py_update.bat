@echo off
echo Running some pip jobs!
uv pip install -U pip setuptools wheel
for %%f in (core_requirements, dev_requirements) do (
    uv pip compile --upgrade %%f.in -o %%f.txt
)
uv add -r core_requirements.in
uv add --dev -r dev_requirements.in
uv sync
echo done!
@echo on