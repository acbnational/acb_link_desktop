# Contributing to ACB Link Desktop

Thank you for your interest in contributing to ACB Link Desktop! This document provides guidelines and information for contributors.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before contributing.

## How to Contribute

### Reporting Bugs

Before creating a bug report, please check the existing issues to avoid duplicates.

**When reporting a bug, include:**

1. **Environment Information**
   - Windows version (e.g., Windows 11 23H2)
   - Python version (e.g., Python 3.11.5)
   - Screen reader and version (e.g., NVDA 2024.1)
   - ACB Link version

2. **Steps to Reproduce**
   - Clear, numbered steps to reproduce the issue
   - What you expected to happen
   - What actually happened

3. **Additional Context**
   - Screenshots (if applicable and you can provide them)
   - Error messages or logs
   - Any workarounds you've found

### Suggesting Features

Feature suggestions are welcome! Please check existing issues first.

**When suggesting a feature, include:**

1. **Use Case**: Why is this feature needed?
2. **Description**: What should the feature do?
3. **Accessibility Impact**: How does this affect accessibility?
4. **Alternatives**: Have you considered any alternatives?

### Pull Requests

1. **Fork the repository** and create your branch from `main`
2. **Follow the code style** (see below)
3. **Add tests** for any new functionality
4. **Update documentation** if needed
5. **Ensure all tests pass** before submitting
6. **Write a clear PR description** explaining your changes

## Development Setup

### Prerequisites

- Python 3.9 or higher
- Git
- Windows 10/11 (for testing)
- A screen reader for accessibility testing (NVDA recommended)

### Setting Up Your Environment

```powershell
# Clone your fork
git clone https://github.com/YOUR-USERNAME/acb_link_desktop.git
cd acb_link_desktop

# Add upstream remote
git remote add upstream https://github.com/acbnational/acb_link_desktop.git

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Application

```powershell
# Run normally
python -m acb_link

# Run with debug logging
python -m acb_link --debug
```

### Running Tests

```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=acb_link --cov-report=html

# Run specific test file
pytest tests/test_accessibility.py

# Run with verbose output
pytest -v
```

## Code Style

### Python Style Guidelines

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [type hints](https://docs.python.org/3/library/typing.html) for all function signatures
- Maximum line length: 100 characters
- Use meaningful variable and function names

### Formatting

We use [Black](https://black.readthedocs.io/) for code formatting:

```powershell
# Format code
black acb_link/

# Check formatting
black --check acb_link/
```

#### Pre-commit, formatting, and Markdown → HTML

We use `pre-commit` to enforce formatting and run linters locally and in CI. The repository also automatically converts changed Markdown files to HTML during pre-commit checks.

Local setup (one-time per developer):

```powershell
# create and activate a venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# install development dependencies (includes pypandoc)
pip install -r requirements-dev.txt

# install and enable pre-commit hook
pre-commit install
# run once to format and convert all files
pre-commit run --all-files
```

What happens:
- `black`, `isort`, and `ruff` auto-format/fix Python files where possible.
- `mdformat` formats Markdown files.
- A small local hook runs `scripts/convert_md_to_html.py` to create/update `.html` files alongside changed `.md` files (CI requires `pandoc` or `pypandoc`).

CI behavior:
- The `Lint & Format` workflow runs `pre-commit run --all-files` on PRs and pushes to `main`.
- If formatting or lint checks fail, the workflow will fail and block merging until fixed.

Guidance for contributors:
- Run `pre-commit run --all-files` before opening a PR to avoid CI failures.
- If many files change purely due to formatting, prefer a dedicated "formatting" PR so maintainers can review it separately.
- The generated `.html` files are committed to the repository to make docs easily viewable; if you prefer not to include an output HTML file for a given Markdown change, note that in your PR description.


### Linting

We use [flake8](https://flake8.pycqa.org/) for linting:

```powershell
# Run linter
flake8 acb_link/
```

### Type Checking

We use [mypy](https://mypy.readthedocs.io/) for type checking:

```powershell
# Run type checker
mypy acb_link/
```

### Example Code Style

```python
"""
Module description.
WCAG 2.2 AA compliant.
"""

from typing import Optional, List, Callable
import wx

from .accessibility import announce, make_accessible


class ExamplePanel(wx.Panel):
    """
    Example panel demonstrating code style.

    This panel follows WCAG 2.2 AA guidelines for accessibility.

    Attributes:
        on_action: Callback function when action is triggered.
    """

    def __init__(
        self,
        parent: wx.Window,
        on_action: Callable[[str], None]
    ) -> None:
        """
        Initialize the example panel.

        Args:
            parent: Parent window.
            on_action: Callback for action events.
        """
        super().__init__(parent)
        self.on_action = on_action
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the panel UI with accessibility support."""
        sizer = wx.BoxSizer(wx.VERTICAL)

        # Create button with accessible name
        self.btn_action = wx.Button(self, label="Perform Action")
        make_accessible(
            self.btn_action,
            "Perform Action",
            "Triggers the example action"
        )
        self.btn_action.Bind(wx.EVT_BUTTON, self._on_action_click)
        sizer.Add(self.btn_action, 0, wx.ALL, 10)

        self.SetSizer(sizer)

    def _on_action_click(self, event: wx.CommandEvent) -> None:
        """Handle action button click."""
        announce("Action performed")
        self.on_action("example")
```

## Accessibility Guidelines

**Accessibility is not optional.** All contributions must maintain or improve accessibility.

### Required for All UI Changes

1. **Accessible Names**: All interactive elements must have accessible names
2. **Keyboard Navigation**: All functionality must be keyboard-accessible
3. **Screen Reader Announcements**: Status changes must be announced
4. **Focus Management**: Focus must be logical and visible
5. **Contrast**: Text must meet WCAG 2.2 AA contrast requirements

### Testing Accessibility

1. **Screen Reader Testing**: Test with NVDA (free) or JAWS
2. **Keyboard-Only Testing**: Navigate using only keyboard
3. **High Contrast Testing**: Test with high contrast themes
4. **Zoom Testing**: Test at 200% zoom

### Accessibility Checklist

Before submitting a PR with UI changes:

- [ ] All controls have accessible names (`make_accessible()`)
- [ ] All lists have accessible descriptions (`make_list_accessible()`)
- [ ] Status changes are announced (`announce()`)
- [ ] Keyboard navigation works correctly
- [ ] Tab order is logical
- [ ] Focus is visible
- [ ] Colors meet contrast requirements
- [ ] Works with screen reader

## Documentation

### Code Documentation

- All modules must have docstrings
- All public functions must have docstrings
- Use Google-style docstrings

### User Documentation

When adding features, update:

- `README.md` if it's a major feature
- `docs/USER_GUIDE.md` for usage instructions
- `docs/FEATURES.md` for feature documentation

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks
- `a11y`: Accessibility improvements

### Examples

```
feat(podcasts): add episode download feature

Adds ability to download podcast episodes for offline listening.
Includes progress indicator and download queue management.

Closes #123
```

```
fix(a11y): add accessible names to stream buttons

Stream play/record/browser buttons now have proper accessible
names for screen reader users.

Fixes #456
```

```
a11y(panels): improve keyboard navigation in podcasts panel

- Add arrow key navigation in episode list
- Announce selected episode on focus
- Fix tab order in button group
```

## Release Process

Releases are managed by maintainers. The process:

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Create release branch
4. Run full test suite
5. Create GitHub release with changelog
6. Build and publish installers

## Questions?

- Open a [Discussion](https://github.com/acbnational/acb_link_desktop/discussions)
- Email: [bits@acb.org](mailto:bits@acb.org)

Thank you for contributing to making technology more accessible! 🎉
