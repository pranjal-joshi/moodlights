# Contributing to MoodLights

Thank you for your interest in contributing to MoodLights!

This document provides guidelines for contributing to this project. Please read through these guidelines before submitting issues or pull requests.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to Contribute](#ways-to-contribute)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

By participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to Contribute

- **Report bugs** - Help us identify issues
- **Suggest features** - Share your ideas for improvement
- **Write code** - Fix bugs or implement features
- **Improve documentation** - Fix typos, add examples
- **Test** - Verify changes work correctly

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a feature branch for your changes

```bash
git clone https://github.com/YOUR_USERNAME/moodlights.git
cd moodlights
git checkout -b feature/your-feature-name
```

## Development Environment

### Prerequisites

- Python 3.12+
- Home Assistant development environment
- Git

### Setup

1. Install development dependencies:

```bash
pip install -e .[dev]
```

Or with uv:

```bash
uv sync --extra dev
```

2. Set up pre-commit hooks:

```bash
pre-commit install
```

## Coding Standards

This project follows Home Assistant coding standards:

### Python

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use [Black](https://github.com/psf/black) for code formatting (88 character line length)
- Use [Ruff](https://docs.astral.sh/ruff/) for linting
- Type hints are encouraged

### Code Style

- Maximum line length: 88 characters
- Use double quotes for strings
- Sort imports with Ruff: `ruff check --select I --fix`

### Home Assistant Specific

- Use async/await for all Home Assistant operations
- Follow [Home Assistant developer guidelines](https://developers.home-assistant.io/)
- All integrations must have proper type hints
- Use const.py for constants

## Testing

### Running Tests

Run all tests:

```bash
pytest tests/
```

Run with coverage:

```bash
pytest --cov=custom_components --cov-report=html tests/
```

### Writing Tests

- Write tests for new features
- Ensure existing tests pass before submitting
- Aim for meaningful test coverage

### Test Structure

```
tests/
├── __init__.py
├── conftest.py           # Shared fixtures
├── test_config_flow.py  # Config flow tests
├── test_mood.py         # Mood entity tests
├── test_state.py        # State manager tests
└── test_exclusion.py    # Exclusion engine tests
```

## Submitting Changes

### Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Run linting:

```bash
black --check custom_components/
ruff check custom_components/
```

5. Commit with clear, descriptive messages
6. Push to your fork
7. Open a Pull Request against the `main` branch
8. Fill out the PR template completely

### Commit Messages

- Use clear, descriptive commit messages
- Reference issues: "Fixes #123" or "Closes #456"
- Keep commits atomic (one change per commit)

### PR Description

Include:
- Summary of changes
- Related issue number
- Testing performed
- Screenshots (if UI changes)

## Issue Reporting

### Bug Reports

Use the [issue tracker](https://github.com/pranjal-joshi/moodlights/issues) to report bugs.

Include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Home Assistant version
- MoodLights version
- Relevant logs

### Feature Requests

Open an issue with:
- Clear description of the feature
- Use case / why it's needed
- Possible implementation approach

## Development Workflow

```
1. Issue → 
2. Branch → 
3. Code → 
4. Test → 
5. Lint → 
6. Commit → 
7. Push → 
8. PR → 
9. Review → 
10. Merge
```

## Questions?

- Open a [discussion](https://github.com/pranjal-joshi/moodlights/discussions)
- Check existing issues and discussions

---

Thank you for contributing to MoodLights!
