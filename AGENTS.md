# Repo Guidelines

## Development
- Target Python 3.11+.
- Run `ruff .` and `pytest -q` before every commit.
- Format code with `black --line-length 88`.

## Documentation
- Update `README.md` for user-facing changes.
- New features should have accompanying tests under `tests/`.

## Notes
- The canonical package source is `src/` at the repository root. Ignore the duplicate `hardware/` directory unless otherwise specified.
