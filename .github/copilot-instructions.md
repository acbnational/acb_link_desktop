# GitHub Copilot Instructions for ACB Link Desktop

## Project overview
- ACB Link Desktop is a cross-platform desktop app written in Python 3.9+ using wxPython.
- Accessibility is a core requirement (WCAG 2.2 AA). Screen reader support is first-class.
- Primary code lives in `acb_link/`. Tests are in `tests/`. Docs are in `docs/`.

## Coding style and conventions
- Format Python with Black (line length 100).
- Prefer dataclasses for settings/config objects.
- Add type hints for public APIs and new functions.
- Keep changes minimal and consistent with existing patterns.

## Accessibility requirements (non-negotiable)
- Every interactive control must have an accessible name and tooltip.
- Use helpers in `acb_link/accessibility.py`:
  - `make_accessible()` for general controls
  - `make_button_accessible()` for buttons (especially icon-only)
  - `make_list_accessible()` for list controls
- Maintain logical keyboard navigation and focus order.
- Announce important status changes via `announce()` or `LiveRegion`.
- Avoid visual-only cues; ensure text alternatives.
- Preserve or improve contrast; use `ContrastValidator` for color scheme changes.
- If UI structure changes, verify focus visibility and no keyboard traps.

## Platform considerations
- App targets Windows and macOS. Avoid Linux-specific assumptions.
- Screen reader logic differs by platform; follow patterns in `acb_link/accessibility.py`.

## Test and validation
- Run tests with `pytest` (see `pyproject.toml`).
- Accessibility tests live in `tests/test_accessibility.py`.
- Keep CI lint constraints in mind (Black + flake8 + mypy).

## Safe areas
- Do not modify files in `data/s3/` unless explicitly requested.
- Avoid changes to installer scripts unless necessary.

## When updating UI
- Add/update accessible names, tooltips, and keyboard shortcuts.
- Update accessibility docs if user-facing behavior changes.
- Prefer announcing state changes through the accessibility module.
