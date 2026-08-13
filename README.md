# School Books Marketplace Bot

A Telegram bot that allows students and parents to buy and sell school textbooks and literature books in a simple, organized way. Replaces chaotic Telegram group chats with a searchable, structured marketplace.

## Project Goals (MVP)

- **Simplicity**: Intuitive interface usable by students and parents with minimal technical experience
- **Structured Browsing**: Category → Class → Subject → Book → Available Listings flow
- **Seller Contact**: Buyers see seller's phone number directly on listing
- **Academic Year Management**: Automatic handling of yearly textbook cycles with archiving
- **Maintainability**: Clean, modular architecture that can be maintained for years
- **Catalog Independence**: Book catalog imported from external files (Excel/CSV), replaceable without code changes

## MVP Scope

The first version focuses exclusively on the core use case:

1. **Find a book** via structured browsing (Category → Class → Subject → Book)
2. **See available listings** for that book (active listings only)
3. **See seller's contact information** (phone number)
4. **Contact seller** outside Telegram (phone call / SMS / WhatsApp)
5. **Seller manages listings**: mark as Active / Reserved / Sold
6. **Sold/Reserved listings** immediately disappear from active search results

**NOT in MVP:**
- Seller ratings / reputation systems
- Price history / analytics
- Wishlist / want-to-buy listings
- Built-in messaging / negotiation system
- Price offers inside the bot
- Recommendation engine
- OCR / book cover recognition
- Mobile app / web dashboard
- School administration API
- Multi-school support
- Advanced search (fuzzy matching, proximity filters)

## Folder Structure

```
school_books_bot/
├── alembic/                    # Database migrations
│   ├── versions/
│   │   ├── e13edef28b08_initial_migration.py
│   │   └── f1a2b3c4d5e6_add_photos_to_listings.py
│   ├── env.py
│   └── script.py.mako
├── bot/
│   ├── __init__.py
│   ├── main.py                 # Application entry point
│   ├── config.py               # Configuration management
│   ├── import_catalog.py       # CLI catalog import tool
│   ├── database/
│   │   ├── __init__.py
│   │   ├── base.py             # SQLAlchemy engine and session
│   │   ├── models.py           # Database models (AcademicYear, User, Book, Listing)
│   │   └── repository.py       # Data access layer
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── start.py            # Start and help commands
│   │   ├── catalog.py          # Catalog browsing and buy flow
│   │   ├── sell.py             # Sell flow (create listing)
│   │   ├── listings.py         # My listings management
│   │   └── admin.py            # Admin panel
│   ├── keyboards/
│   │   ├── __init__.py
│   │   ├── common.py           # Main menu keyboards
│   │   ├── catalog.py          # Catalog navigation keyboards
│   │   ├── listings.py         # Listing management keyboards
│   │   └── admin.py            # Admin panel keyboards
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── bot_injection.py    # Bot instance injection
│   │   ├── db_session.py       # Database session injection
│   │   ├── error_handler.py    # Global error handling
│   │   ├── banned_user.py      # Banned user restriction
│   │   └── admin_auth.py       # Admin authorization (defined, not registered)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── browsing.py         # Catalog navigation service
│   │   ├── listing.py          # Listing CRUD and validation
│   │   ├── academic_year.py    # Academic year management
│   │   ├── notification.py     # Telegram notifications
│   │   ├── admin.py            # User moderation
│   │   └── catalog/
│   │       ├── __init__.py
│   │       ├── importer.py     # Catalog import orchestrator
│   │       ├── parser.py       # Excel/CSV parser
│   │       └── validator.py    # Catalog data validation
│   ├── states/
│   │   ├── __init__.py
│   │   └── fsm.py              # Finite state machines
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py          # Shared helper functions
│   └── locale/
│       ├── __init__.py
│       └── fr.py               # French translations (all user-facing text)
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Shared test fixtures
│   ├── test_buying_handlers.py
│   ├── test_sell_handlers.py
│   ├── test_sell_edge_cases.py
│   ├── test_my_listings_handlers.py
│   ├── test_listings_additional.py
│   ├── test_listings_edge_cases.py
│   ├── test_browsing_service.py
│   ├── test_browsing_repository.py
│   ├── test_book_repository.py
│   ├── test_listing_service.py
│   ├── test_listing_repository.py
│   ├── test_listing_keyboards.py
│   ├── test_catalog_importer.py
│   ├── test_catalog_parser.py
│   ├── test_catalog_validator.py
│   ├── test_catalog_keyboards.py
│   ├── test_notification_service.py
│   ├── test_error_handler.py
│   ├── test_db_session_middleware.py
│   ├── test_milestone5.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_locale.py
│   │   ├── test_handlers.py
│   │   └── test_keyboards.py
│   └── integration/
│       └── __init__.py
├── docker/
│   └── docker-compose.yml
├── .env.example
├── .gitignore
├── Dockerfile
├── alembic.ini
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── RULES.md
├── PROJECT.md
└── README.md
```

## Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | 3.13+ |
| Bot Framework | aiogram | 3.x |
| Database | SQLite (dev) / PostgreSQL (prod) | - |
| ORM | SQLAlchemy | 2.x (async) |
| Migrations | Alembic | Latest |
| Validation | Pydantic | 2.x |
| Config | pydantic-settings | Latest |
| Testing | pytest | Latest |
| Linting | Ruff | Latest |
| Type Checking | mypy | Latest |
| Containerization | Docker | Latest |
| Excel Support | openpyxl | Latest |
| CSV Support | Python stdlib | - |

## Installation

### Prerequisites

- Python 3.13+
- Docker (optional, for containerized deployment)
- Git

### Local Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd school_books_bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env

# Edit .env with your configuration
# Required: TELEGRAM_BOT_TOKEN from @BotFather
# Required: BOT_ADMIN_IDS with your Telegram user ID

# Run database migrations
alembic upgrade head

# Start the bot
python -m bot.main
```

### Docker Deployment

```bash
# Build and start services
cd docker
docker-compose up -d --build

# View logs
docker-compose logs -f bot

# Run migrations
docker-compose exec bot alembic upgrade head
```

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Telegram Bot Token (required)
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather

# Environment: development | production
ENVIRONMENT=development

# Database URL
DATABASE_URL=sqlite+aiosqlite:///./data/bot.db
# For PostgreSQL: postgresql+asyncpg://user:pass@host:5432/dbname

# Admin Telegram IDs (comma-separated)
BOT_ADMIN_IDS=123456789,987654321

# Logging level
LOG_LEVEL=INFO

# Listing configuration
MAX_LISTINGS_PER_USER=50
LISTING_EXPIRY_DAYS=180
```

## Admin Features

- `/admin` - Access admin panel (admin IDs only)
- Academic year management (create, set current, transition)
- Catalog import from Excel/CSV files
- User management (list, search, ban/unban)

## User Flows

### Buyer Flow
/start → Menu principal → Acheter un livre → Catégorie → Classe → Matière → Livre → Annonces disponibles → Voir les informations du vendeur

### Seller Flow
/start → Mettre en vente → Catégorie → Classe → Matière → Livre → Prix → État → Téléphone → Photos → Description → Confirmation → Annonce créée

### Listing Management
/start → Mes annonces → En vente / Réservées / Vendues / Archivées → Modifier / Réserver / Vendre / Remettre en vente / Archiver

## License

This project is licensed under the MIT License.
