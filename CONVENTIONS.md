<!-- CONVENTIONS.md -->
# Development Rules
- Use Python 3.12 with strict Pydantic type checking.
- Every plugin file inside `plugins/` must inherit from a common base class.
- Plugins must NEVER import other plugins.
- Keep functions under 30 lines of code; prioritize surgical updates.

# Development Conventions
- UI framework: Streamlit.
- Core operations: Use `yfinance` or clean JSON dictionaries for stock metrics.
- Date logic: Use Python's native `datetime` with strict timezone handling.
- Maximum file size: Under 120 lines. Zero cross-imports between worker files.
