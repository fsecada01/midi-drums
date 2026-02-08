# MIDI Drums Generator - Justfile
# Run `just --list` to see all available commands

set shell := ["cmd.exe", "/c"]

# Default recipe - show available commands

default:
    @just --list

# ═══════════════════════════════════════════════════════════════════════════════
# Claude Code
# ═══════════════════════════════════════════════════════════════════════════════

# Start Claude Code with system prompt (supports any args: just claude --continue, just claude -p "task")
claude *ARGS:
    claude --system-prompt .claude/system-prompt.md {{ARGS}}

# Start Claude in continue mode
claude-continue:
    claude --system-prompt .claude/system-prompt.md --continue

# Start Claude in resume mode (resume last conversation)
claude-resume:
    claude --system-prompt .claude/system-prompt.md --resume

# Start Claude with a specific prompt
claude-prompt PROMPT:
    claude --system-prompt .claude/system-prompt.md -p "{{PROMPT}}"

# ═══════════════════════════════════════════════════════════════════════════════
# Development Setup
# ═══════════════════════════════════════════════════════════════════════════════

# Update dependencies from .in files
update:
    uv sync --all-groups

# Update dependencies (Windows batch script)
update-win:
    bin/py_update.bat

# Update dependencies (Unix shell script)
update-unix:
    bin/py_update.sh

# Install core dependencies only
install:
    pip install -r core_requirements.txt

# Install all dependencies including dev and AI
install-all:
    pip install -r core_requirements.txt -r dev_requirements.txt -r ai_requirements.txt

# ═══════════════════════════════════════════════════════════════════════════════
# Code Quality
# ═══════════════════════════════════════════════════════════════════════════════

# Run all linting tools
lint:
    ruff check midi_drums tests
    black --check midi_drums tests
    isort --check-only midi_drums tests

# Run linting (Windows batch script)
lint-win:
    bin/linting.bat

# Run linting (Unix shell script)
lint-unix:
    bin/linting.sh

# Format code with black and isort
format:
    black midi_drums tests
    isort midi_drums tests

# Run ruff linter with auto-fix
fix:
    ruff check --fix midi_drums tests

# ═══════════════════════════════════════════════════════════════════════════════
# Testing
# ═══════════════════════════════════════════════════════════════════════════════

# Run all tests
test:
    pytest

# Run tests with verbose output
test-v:
    pytest -v

# Run unit tests only
test-unit:
    pytest -m unit

# Run integration tests only
test-integration:
    pytest -m integration

# Run AI tests only (requires API key)
test-ai:
    pytest -m ai

# Run tests excluding those requiring API keys
test-no-api:
    pytest -m "not requires_api"

# Run tests in parallel
test-parallel:
    pytest -n auto

# Run tests with coverage report
test-cov:
    pytest --cov=midi_drums --cov-report=html

# Run tests with coverage (terminal output)
test-cov-term:
    pytest --cov=midi_drums --cov-report=term-missing

# Run architecture tests
test-arch:
    python test_new_architecture.py

# Run all drummer plugin tests
test-drummers:
    python test_all_drummer_plugins.py

# Run genre plugin tests
test-genres:
    python test_new_genre_plugins.py

# ═══════════════════════════════════════════════════════════════════════════════
# Generation Examples
# ═══════════════════════════════════════════════════════════════════════════════

# Run basic usage example
example:
    python examples/basic_usage.py

# Compare old vs new architecture
migrate:
    python migrate_from_original.py

# ═══════════════════════════════════════════════════════════════════════════════
# CLI Commands - Generation
# ═══════════════════════════════════════════════════════════════════════════════

# Generate a metal song (default: heavy style, 155 BPM)
gen-metal style="heavy" tempo="155" output="metal_song.mid":
    python -m midi_drums generate --genre metal --style {{style}} --tempo {{tempo}} --output {{output}}

# Generate a rock song (default: classic style, 140 BPM)
gen-rock style="classic" tempo="140" output="rock_song.mid":
    python -m midi_drums generate --genre rock --style {{style}} --tempo {{tempo}} --output {{output}}

# Generate a jazz song (default: swing style, 120 BPM)
gen-jazz style="swing" tempo="120" output="jazz_song.mid":
    python -m midi_drums generate --genre jazz --style {{style}} --tempo {{tempo}} --output {{output}}

# Generate a funk song (default: classic style, 110 BPM)
gen-funk style="classic" tempo="110" output="funk_song.mid":
    python -m midi_drums generate --genre funk --style {{style}} --tempo {{tempo}} --output {{output}}

# Generate with a specific drummer style
gen-drummer genre="rock" style="classic" drummer="bonham" tempo="140" output="drummer_song.mid":
    python -m midi_drums generate --genre {{genre}} --style {{style}} --drummer {{drummer}} --tempo {{tempo}} --output {{output}}

# Generate a pattern for a specific section
gen-pattern genre="metal" section="verse" style="heavy" output="pattern.mid":
    python -m midi_drums pattern --genre {{genre}} --section {{section}} --style {{style}} --output {{output}}

# ═══════════════════════════════════════════════════════════════════════════════
# CLI Commands - Information
# ═══════════════════════════════════════════════════════════════════════════════

# Show system info
info:
    python -m midi_drums info

# List all available genres
list-genres:
    python -m midi_drums list genres

# List styles for a genre
list-styles genre="metal":
    python -m midi_drums list styles --genre {{genre}}

# List all available drummers
list-drummers:
    python -m midi_drums list drummers

# Show CLI help
help:
    python -m midi_drums --help

# Show generate command help
help-generate:
    python -m midi_drums generate --help

# ═══════════════════════════════════════════════════════════════════════════════
# Quick Demos
# ═══════════════════════════════════════════════════════════════════════════════

# Generate demo songs for all genres
demo-all:
    python -m midi_drums generate --genre metal --style death --tempo 180 --output demo_metal.mid
    python -m midi_drums generate --genre rock --style classic --tempo 140 --output demo_rock.mid
    python -m midi_drums generate --genre jazz --style swing --tempo 120 --output demo_jazz.mid
    python -m midi_drums generate --genre funk --style classic --tempo 110 --output demo_funk.mid

# Generate demo songs with drummer styles
demo-drummers:
    python -m midi_drums generate --genre rock --style classic --drummer bonham --tempo 140 --output demo_bonham.mid
    python -m midi_drums generate --genre rock --style blues --drummer porcaro --tempo 95 --output demo_porcaro.mid
    python -m midi_drums generate --genre jazz --style fusion --drummer weckl --tempo 135 --output demo_weckl.mid
    python -m midi_drums generate --genre funk --style classic --drummer chambers --tempo 105 --output demo_chambers.mid

# ═══════════════════════════════════════════════════════════════════════════════
# Maintenance
# ═══════════════════════════════════════════════════════════════════════════════

# Clean generated MIDI files from root directory
clean:
    rm -f *.mid

# Clean Python cache files
clean-cache:
    find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
    find . -type f -name "*.pyc" -delete 2>/dev/null || true
    rm -rf .pytest_cache .ruff_cache .coverage htmlcov 2>/dev/null || true

# Clean all generated and cache files
clean-all: clean clean-cache

# ═══════════════════════════════════════════════════════════════════════════════
# Composite Commands
# ═══════════════════════════════════════════════════════════════════════════════

# Run format, lint, and tests
check: format lint test

# Full CI pipeline: format, lint, all tests with coverage
ci: format lint test-cov

# Quick validation: lint check and unit tests only
quick: lint test-unit

# ═══════════════════════════════════════════════════════════════════════════════
# AI Generation
# ═══════════════════════════════════════════════════════════════════════════════

# List available AI prompts
ai-prompts:
    @echo "Available AI prompts in midi_drums/ai/prompts/:"
    @ls -1 midi_drums/ai/prompts/*.md 2>/dev/null || dir /b midi_drums\ai\prompts\*.md

# Show model routing configuration
ai-models:
    @cat midi_drums/ai/prompts/model_routing.md | head -100

# Run AI pattern generation example
ai-example:
    python -c "from midi_drums.ai import DrumGeneratorAI; print('AI module loaded successfully')"

# Show AI environment configuration
ai-config:
    @echo "AI Environment Variables:"
    @echo "AI_PROVIDER: ${AI_PROVIDER:-not set (default: anthropic)}"
    @echo "AI_MODEL: ${AI_MODEL:-not set (uses provider default)}"
    @echo "AI_TEMPERATURE: ${AI_TEMPERATURE:-not set (default: 0.7)}"
    @echo "AI_MAX_TOKENS: ${AI_MAX_TOKENS:-not set (default: 4096)}"

# ═══════════════════════════════════════════════════════════════════════════════
# Documentation
# ═══════════════════════════════════════════════════════════════════════════════

# Show development system prompt
show-system-prompt:
    @cat .claude/system-prompt.md

# Show pattern analysis prompt
show-prompt-analysis:
    @cat midi_drums/ai/prompts/pattern_analysis.md

# Show song composition prompt
show-prompt-composition:
    @cat midi_drums/ai/prompts/song_composition.md

# Show all available commands grouped by category
commands:
    @echo "=== Claude Code ==="
    @echo "  claude [ARGS]     - Start with system prompt (e.g., just claude --continue)"
    @echo "  claude-continue   - Continue last conversation"
    @echo "  claude-resume     - Resume last session"
    @echo "  claude-prompt     - Start with a specific prompt"
    @echo ""
    @echo "=== Development ==="
    @echo "  update, install, install-all"
    @echo ""
    @echo "=== Code Quality ==="
    @echo "  lint, format, fix"
    @echo ""
    @echo "=== Testing ==="
    @echo "  test, test-unit, test-integration, test-ai, test-cov"
    @echo ""
    @echo "=== Generation ==="
    @echo "  gen-metal, gen-rock, gen-jazz, gen-funk, gen-drummer, gen-pattern"
    @echo ""
    @echo "=== Information ==="
    @echo "  info, list-genres, list-styles, list-drummers, help"
    @echo ""
    @echo "=== Demos ==="
    @echo "  demo-all, demo-drummers"
    @echo ""
    @echo "=== AI ==="
    @echo "  ai-prompts, ai-models, ai-example, ai-config"
    @echo ""
    @echo "=== Maintenance ==="
    @echo "  clean, clean-cache, clean-all"
    @echo ""
    @echo "=== Composite ==="
    @echo "  check, ci, quick"
