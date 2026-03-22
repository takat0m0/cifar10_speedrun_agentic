# Repository Guidelines

## Project Structure & Module Organization
This repository is a minimal Python package scaffold.
- Source code lives in `src/cifar10_speedrun_agentic/`.
- Package markers: `__init__.py` and `py.typed`.
- Project metadata and dependencies are in `pyproject.toml`.
- Locked dependency resolution is in `uv.lock`.

When adding new functionality, keep importable code under `src/cifar10_speedrun_agentic/` and group modules by feature (for example, `data.py`, `train.py`, `models/`).

## Build, Test, and Development Commands
Use `uv` for environment and command execution.
- `uv sync` installs/updates dependencies from `pyproject.toml` and `uv.lock`.
- `uv run python -m cifar10_speedrun_agentic` runs the package module entry path (after you add one).
- `uv build` creates distribution artifacts using the configured `uv_build` backend.

Example workflow:
```bash
uv sync
uv run python -c "import cifar10_speedrun_agentic; print('ok')"
uv build
```

## Coding Style & Naming Conventions
- Target Python `>=3.11`.
- Follow PEP 8 with 4-space indentation and explicit type hints for public APIs.
- Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; `UPPER_SNAKE_CASE` for constants.
- Keep modules focused; avoid large, mixed-responsibility files.

If you add formatting/lint tooling (for example `ruff`), configure it in `pyproject.toml` and run it through `uv run`.

## Testing Guidelines
No test framework is configured yet. Add tests under a top-level `tests/` directory.
- Name files `test_*.py`.
- Name tests descriptively, e.g., `test_dataloader_shapes()`.
- Prefer deterministic tests with fixed seeds for ML code.

Recommended command once tests are added:
- `uv run pytest`

## Commit & Pull Request Guidelines
There is no existing commit history yet, so no enforced message convention is present.
Use clear, imperative commit subjects (<=72 chars), for example:
- `Add CIFAR-10 dataloader utilities`
- `Implement baseline training loop`

For pull requests:
- Summarize what changed and why.
- Link related issues/tasks.
- Include validation evidence (test output, benchmark numbers, or repro steps).
- Keep PR scope focused and reviewable.

## Language
日本語でやりとりをしてください．
skill などの作成についても日本語で行ってください．
