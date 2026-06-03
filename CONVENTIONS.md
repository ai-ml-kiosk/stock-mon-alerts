<!-- CONVENTIONS.md -->
# Development Rules
- Use Python 3.12 with strict Pydantic type checking.
- Every plugin file inside `plugins/` must inherit from a common base class.
- Plugins must NEVER import other plugins.
- Keep functions under 30 lines of code; prioritize surgical updates.
