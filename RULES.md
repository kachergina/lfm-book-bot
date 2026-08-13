# Development Rules - School Books Marketplace Bot

This document serves as the permanent development guide for the project. All contributors must follow these rules.

## Project Architecture Rules

### Modular Architecture
- Each module has a **single responsibility**
- Modules communicate through well-defined interfaces
- No circular dependencies between modules
- Shared code goes in `bot/utils/` or `bot/services/`
- Handlers only handle updates, delegate business logic to services

### Layer Separation
```
Handlers (Presentation) → Services (Business Logic) → Repository (Data Access) → Models (Database)
```
- **Handlers**: Receive updates, validate input, send responses
- **Services**: Contain business logic, orchestrate operations
- **Repository**: Abstract database operations, no business logic
- **Models**: SQLAlchemy models, pure data structures

### Dependency Injection
- Use dependency injection for services and repositories
- Pass dependencies through constructor or aiogram's `DependencyContainer`
- Avoid global state; use context variables for request-scoped data

## Folder Organization

```
bot/
├── handlers/       # One file per feature area
├── services/       # Business logic, one file per domain
├── database/       # Models, repository, base
├── keyboards/      # UI keyboards, grouped by feature
├── middlewares/    # Cross-cutting concerns
├── states/         # FSM definitions
├── utils/          # Pure helper functions
└── locale/         # Translations (French only for UI)
```

### File Naming
- Modules: `snake_case.py` (e.g., `catalog_import.py`)
- Classes: `PascalCase` (e.g., `CatalogImportService`)
- Functions: `snake_case` (e.g., `import_catalog`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_LISTINGS_PER_USER`)
- Private: Prefix with `_` (e.g., `_internal_helper`)

## Naming Conventions

### Database
- Tables: `snake_case`, plural (e.g., `listings`, `academic_years`)
- Columns: `snake_case` (e.g., `created_at`, `book_id`)
- Foreign keys: `<table>_id` (e.g., `book_id`, `seller_id`)
- Indexes: `ix_<table>_<column>` (e.g., `ix_listings_book_id`)

### Code
- **Variables**: Descriptive `snake_case` (`current_user`, `book_title`)
- **Functions**: Verb + noun (`get_user_listings`, `create_listing`)
- **Boolean**: Prefix with `is_`, `has_`, `can_`, `should_` (`is_active`, `has_permission`)
- **Async functions**: Same naming, always `async def`
- **Type hints**: Required for all public functions

### Translation Keys
- Format: `feature.action.context` (e.g., `catalog.search.no_results`, `listing.create.success`)
- Grouped by feature in `bot/locale/fr.py`

## Coding Standards

### Python Version
- Target: **Python 3.13+**
- Use modern syntax: `match/case`, `|` for unions, `type` aliases

### Type Hints
```python
# Required for all public functions
async def get_listing(listing_id: int) -> Listing | None: ...


# Use TypeAlias for complex types
type ListingFilter = dict[str, str | int | list[str]]
```

### Async/Await
- All I/O operations must be async
- Use `async with` for database sessions
- Never block event loop (no `time.sleep`, use `asyncio.sleep`)

### Error Handling
```python
# Custom exceptions in bot/exceptions.py
class ListingNotFoundError(BotError):
    pass


# Handle in handlers, not services
try:
    listing = await listing_service.get(listing_id)
except ListingNotFoundError:
    await message.answer(translate("listing.not_found"))
```

### Imports
```python
# Standard library first
import asyncio
from datetime import datetime

# Third party
from aiogram import Router, F
from sqlalchemy import select

# Local (absolute imports)
from bot.database.models import Listing
from bot.services.catalog_import import CatalogImportService
from bot.keyboards.catalog import catalog_keyboard
```

### Docstrings
```python
async def search_books(query: str, filters: BookFilter) -> list[Book]:
    """Search books in catalog with optional filters.
    
    Args:
        query: Search text (title, author, ISBN)
        filters: Optional filters (grade, subject, condition)
    
    Returns:
        List of matching books, empty if none found.
    
    Raises:
        CatalogNotLoadedError: If catalog hasn't been imported.
    """
```

## Documentation Standards

### Code Documentation
- All public classes/functions have docstrings
- Complex algorithms have inline comments
- Type hints serve as primary documentation

### Architecture Documentation
- `docs/architecture.md`: System overview, component diagram
- `docs/database_design.md`: ER diagram, table descriptions
- `docs/deployment.md`: Production deployment guide
- Update docs with every architectural change

### Commit Documentation
- Every commit has a clear message (see Git Workflow)
- Breaking changes documented in CHANGELOG.md

## Git Workflow

### Branch Strategy
- `main`: Production-ready code, protected
- `develop`: Integration branch for features
- `feature/*`: Feature branches from `develop`
- `hotfix/*`: Urgent fixes from `main`
- `release/*`: Release preparation branches

### Commit Messages
Follow Conventional Commits:
```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

**Examples**:
```
feat(catalog): add structured browsing by category/class/subject
fix(listings): prevent duplicate active listings per user
docs(architecture): update database design document
refactor(services): extract notification logic to separate service
test(import): add test cases for CSV import validation
```

### Pull Requests
- Required for all changes to `main` and `develop`
- Minimum 1 approval required
- CI checks must pass (lint, typecheck, tests)
- Squash and merge preferred

### Versioning
- Semantic Versioning (MAJOR.MINOR.PATCH)
- Tags: `v1.0.0`, `v1.1.0`, etc.
- CHANGELOG.md updated on release

## Testing Standards

### Test Organization
```
tests/
├── unit/           # Fast, isolated tests (no DB, no network)
├── integration/    # Database, bot handler tests
└── fixtures/       # Test data files
```

### Test Naming
- Files: `test_<module>.py`
- Functions: `test_<function>_<scenario>_<expected>`
  - `test_get_listing_returns_none_when_not_found`
  - `test_create_listing_validates_required_fields`

### Coverage Requirements
- Minimum 80% overall coverage
- 100% coverage for critical paths (data integrity, listing status transitions)
- Run: `pytest --cov=bot --cov-fail-under=80`

### Test Principles
- **Arrange, Act, Assert** structure
- One assertion per test (preferred)
- Use fixtures for common setup
- Mock external dependencies
- Test behavior, not implementation

## Logging

### Structured Logging
```python
import structlog

logger = structlog.get_logger()

# Good: structured, searchable
logger.info(
    "listing_created",
    listing_id=listing.id,
    seller_id=user.id,
    book_title=book.title,
    price=listing.price,
)

# Bad: unstructured string
logger.info(f"User {user.id} created listing {listing.id}")
```

### Log Levels
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational events (startup, listing created)
- `WARNING`: Unexpected but handled (rate limit, invalid input)
- `ERROR`: Operation failed (DB error, API failure)
- `CRITICAL`: System unusable (config missing, DB unavailable)

### What to Log
- All user actions (commands, button clicks, form submissions)
- Business events (listing created, sold, reserved)
- Errors with full context (user_id, request_data, traceback)
- Performance metrics (slow queries, API latency)
- Security events (failed auth, rate limits, admin actions)

### Log Format
JSON format for production, human-readable for development.

## Error Handling

### User-Facing Errors
- **Never** expose internal errors (stack traces, SQL errors)
- Always show friendly French messages
- Provide actionable guidance when possible

```python
# Good
await message.answer(
    "Ce livre n'est pas disponible dans le catalogue. "
    "Vérifiez l'orthographe ou contactez l'administrateur."
)

# Bad
await message.answer(f"Database error: {e}")
```

### Exception Hierarchy
```python
class BotError(Exception):
    """Base exception for user-facing errors."""

    user_message: str


class ValidationError(BotError):
    pass


class NotFoundError(BotError):
    pass


class PermissionError(BotError):
    pass
```

### Global Error Handler
- Catch-all middleware logs errors and sends generic message
- Admin notified for CRITICAL errors
- No Sentry in MVP - simple file/console logging sufficient

## Security

### Secrets Management
- **Never** hardcode secrets (tokens, passwords, API keys)
- All secrets in `.env` (not committed)
- `.env.example` documents required variables
- Use Docker secrets in production

### Input Validation
- Validate all user input at handler level
- Use Pydantic models for complex validation
- Sanitize data before database storage
- Limit string lengths, file sizes, numeric ranges

### Rate Limiting
- Throttling middleware on all handlers
- Stricter limits for write operations
- Configurable per-user and global limits
- In-memory implementation for MVP (no Redis)

### Data Protection
- No PII in logs (mask user IDs if needed)
- Phone numbers stored for seller contact - handle with care
- HTTPS only in production
- Database encryption at rest (production)

### Telegram Security
- Validate `webhook_secret` if using webhooks
- Verify `init_data` for Web Apps
- Don't trust `username` for identification (use `user_id`)

## Maintainability Principles

### DRY (Don't Repeat Yourself)
- Extract common logic to services/utils
- Use base classes for similar handlers
- Shared keyboards in `keyboards/common.py`

### KISS (Keep It Simple, Stupid)
- Prefer simple solutions over clever ones
- Avoid premature abstraction
- Maximum 3 levels of indentation

### YAGNI (You Aren't Gonna Need It)
- Don't add features "for later"
- Implement only what's required now
- Refactor when need arises

### SOLID Principles
- **S**: Single Responsibility - each class/module does one thing
- **O**: Open/Closed - extend via composition, not modification
- **L**: Liskov Substitution - subtypes work as base types
- **I**: Interface Segregation - small, focused interfaces
- **D**: Dependency Inversion - depend on abstractions

### Code Review Checklist
- [ ] Follows naming conventions
- [ ] Type hints present and correct
- [ ] Error handling for all failure paths
- [ ] Logging for important events
- [ ] Tests for new functionality
- [ ] No hardcoded strings (use locale)
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Documentation updated

## Code Quality Tools

### Pre-commit Hooks
```bash
# Install
pre-commit install

# Run manually
pre-commit run --all-files
```

### Configuration Files
- `ruff.toml`: Linting rules
- `mypy.ini`: Type checking config
- `pytest.ini`: Test configuration
- `pyproject.toml`: Project metadata, tool configs

### CI Pipeline
Every PR must pass:
1. `ruff check .` - Linting
2. `black --check .` - Formatting
3. `mypy bot/` - Type checking
4. `pytest --cov=bot` - Tests with coverage
5. `alembic check` - Migration validity

## Performance Guidelines (MVP)

### Database
- Use indexes on foreign keys and filter columns
- Paginate all list queries (default 20 items)
- Use `selectinload` for relationships, avoid N+1
- SQLite for dev, PostgreSQL for prod (no connection pooling needed for MVP)

### Bot Responsiveness
- Answer callback queries immediately (`await callback.answer()`)
- Use `chat_action` for long operations
- No background tasks in MVP (simple sequential processing)

### Caching
- Cache catalog data in memory (reload on import)
- No Redis in MVP - simple in-memory dict cache

## Accessibility & UX

### French Language
- All user-facing text in `bot/locale/fr.py`
- Natural, professional French (vous form)
- Consistent terminology across bot
- Gender-neutral where possible

### Interface Design
- Buttons over text input
- Clear hierarchy: Main → Category → Class → Subject → Book → Listings
- Maximum 3-4 taps to common actions
- Confirmation for destructive actions
- Loading indicators for async operations

### Error Recovery
- Always provide "Back" / "Menu" options
- Preserve user input on validation errors
- Clear error messages with next steps

## Maintenance

### Dependency Updates
- Monthly security updates
- Quarterly minor version updates
- Major versions tested in branch first
- `pip-audit` in CI for vulnerabilities

### Database Migrations
- One migration per logical change
- Test migrations on copy of production data
- Rollback plan for every migration
- Never modify applied migrations

### Monitoring
- Health check endpoint
- Key metrics: active users, listings, errors
- Alert on error rate > 1%
- Simple file-based logging for MVP

---

**Remember**: These rules exist to keep the project maintainable for years. When in doubt, choose the solution that makes the codebase easier to understand and modify.