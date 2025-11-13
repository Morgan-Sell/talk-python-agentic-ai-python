# Gitty Up

[![CI](https://github.com/yourusername/gittyup/workflows/CI/badge.svg)](https://github.com/yourusername/gittyup/actions)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A professional CLI tool for synchronizing multiple git repositories recursively.

## The Problem

When working on multiple computers or with many team members, and across many projects, it's easy to start working on an existing one and forget to do a `git pull`. Then when it's time to commit the changes, you realize you have merge conflicts and more. This is not fun.

## The Solution

Gitty Up recursively scans a directory tree, identifies all git repositories, and executes pull operations to ensure all projects are up-to-date before development begins. With beautiful colored output and comprehensive error handling, it prevents merge conflicts and saves developer time.

## Features

### Phase 1 (Current - v0.1.0)
- ✅ Recursive directory scanning
- ✅ Configurable depth limits
- ✅ Exclusion pattern support
- ✅ Beautiful colored output with Rich
- ✅ Verbose and quiet modes
- ✅ Dry-run mode
- ✅ Comprehensive test suite
- ✅ Cross-platform support (Linux, macOS, Windows)

### Coming Soon
- 🔄 Git repository detection and pull operations (Phase 2)
- 🔄 Parallel processing (Phase 5)
- 🔄 Configuration file support (Phase 4)
- 🔄 Status-only mode (Phase 2)

## Installation

### From PyPI (Coming Soon)

```bash
pip install gittyup
```

### Development Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/gittyup.git
cd gittyup

# Install in development mode
pip install -e ".[dev]"
```

### Using pipx (Recommended)

```bash
pipx install gittyup
```

## Usage

### Basic Usage

```bash
# Scan current directory
gittyup

# Scan specific directory
gittyup ~/projects

# Scan with depth limit
gittyup --depth 2 ~/projects

# Dry run to see what would be done
gittyup --dry-run ~/projects
```

### Advanced Usage

```bash
# Exclude specific directories
gittyup --exclude node_modules --exclude venv ~/projects

# Verbose mode for detailed output
gittyup --verbose ~/projects

# Quiet mode (only errors)
gittyup --quiet ~/projects

# Disable colored output
gittyup --no-color ~/projects
```

## Command-Line Options

```
gittyup [OPTIONS] [PATH]

Arguments:
  PATH                      Directory to scan (default: current directory)

Options:
  --depth, -d INTEGER       Maximum depth to scan (default: unlimited)
  --exclude, -e TEXT        Patterns to exclude (can be used multiple times)
  --dry-run                 Show what would be done without executing
  --verbose, -v             Show detailed output
  --quiet, -q               Minimal output, only errors
  --no-color                Disable colored output
  --help, -h                Show this message and exit
  --version                 Show version and exit
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/gittyup.git
cd gittyup

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=gittyup --cov-report=html

# Run specific test file
pytest tests/unit/test_scanner.py

# Run with verbose output
pytest -v
```

### Code Quality

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/gittyup

# Run all checks
pre-commit run --all-files
```

## Project Structure

```
gittyup/
├── src/gittyup/          # Source code
│   ├── core/             # Core modules (scanner, executor, reporter)
│   ├── config/           # Configuration handling
│   ├── utils/            # Utility functions
│   └── cli.py            # CLI interface
├── tests/                # Test suite
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   └── conftest.py       # Test fixtures
├── docs/                 # Documentation
├── examples/             # Example configurations
└── plans/                # Project plans and specifications
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](docs/contributing.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linters
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Click](https://click.palletsprojects.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [pytest](https://pytest.org/) for testing

## Roadmap

See [project-plan.md](plans/project-plan.md) for the complete project roadmap and technical specifications.

### Phase Timeline
- ✅ **Phase 1** (Week 1): Foundation - Project structure, basic CLI, directory scanning
- 🔄 **Phase 2** (Week 2): Core Functionality - Git repository detection and operations
- 🔜 **Phase 3** (Week 3): Enhanced Output - Progress bars, formatted reports
- 🔜 **Phase 4** (Week 4): Configuration - Config file support, multiple modes
- 🔜 **Phase 5** (Week 5): Performance - Parallel processing, optimization
- 🔜 **Phase 6** (Week 6): Distribution - Documentation, PyPI release

## Support

- 📖 [Documentation](https://github.com/yourusername/gittyup#readme)
- 🐛 [Issue Tracker](https://github.com/yourusername/gittyup/issues)
- 💬 [Discussions](https://github.com/yourusername/gittyup/discussions)

---

**Status**: Phase 1 Complete ✅  
**Version**: 0.1.0  
**Last Updated**: November 12, 2025
