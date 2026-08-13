# Project Specification - School Books Marketplace Bot

## Complete Application Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Telegram Users                           │
└─────────────────────────────┬───────────────────────────────────┘
                              │ HTTPS / Webhook
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      aiogram Bot Application                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Handlers   │  │  Middlewares │  │   Keyboards  │              │
│  │  (Presentation)│  │ (Cross-cutting)│  │   (UI)       │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         ▼                ▼                ▼                      │
│  ┌─────────────────────────────────────────────────┐            │
│  │              Services Layer                      │            │
│  │  Catalog │ Listings │ Search │ AcademicYear │ Notif │        │
│  └──────────────────────┬──────────────────────────┘            │
│                         │                                        │
│         ┌───────────────┼───────────────┐                        │
│         ▼               ▼               ▼                        │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                │
│  │ Repository  │ │ Repository  │ │ Repository  │                │
│  │  (Catalog)  │ │ (Listings)  │ │  (Users)    │                │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘                │
│         │               │               │                         │
│         └───────────────┼───────────────┘                         │
│                         ▼                                         │
│  ┌─────────────────────────────────────────────────┐            │
│  │           SQLAlchemy + SQLite/PostgreSQL         │            │
│  └─────────────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Handlers** | Receive updates, validate input, orchestrate flow, send responses |
| **Services** | Business logic, validation, orchestration, external integrations |
| **Repositories** | Database queries, data mapping, transaction management |
| **Models** | SQLAlchemy ORM models, relationships, constraints |
| **Keyboards** | UI construction, button layouts, pagination |
| **Middlewares** | Logging, auth, throttling, error handling, i18n |
| **States (FSM)** | Multi-step conversation state management |

### Data Flow Example: Create Listing

```
User → /sell → Handler validates → FSM: SELECT_BOOK
  → User selects from catalog → FSM: ENTER_PRICE
  → User enters price → FSM: ENTER_CONDITION
  → User selects condition → FSM: CONFIRM
  → User confirms → ListingService.create_listing()
    → ListingRepository.create()
    → Database INSERT
  → Success message + keyboard
```

## Database Design

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────┐       ┌─────────────────┐
│   academic_years│       │     books       │       │     users       │
├─────────────────┤       ├─────────────────┤       ├─────────────────┤
│ id (PK)         │       │ id (PK)         │       │ id (PK)         │
│ name            │       │ category        │       │ telegram_id (UK)│
│ start_date      │       │ title           │       │ username        │
│ end_date        │       │ author          │       │ first_name      │
│ is_current      │       │ isbn            │       │ last_name       │
│ created_at      │       │ grade_level     │       │ role            │
└────────┬────────┘       │ subject         │       │ is_active       │
         │               │ publisher       │       │ created_at      │
         │               │ year_published  │       └────────┬────────┘
         │               │ catalog_year_id │                │
         │               │ (FK)            │                │
         │               └────────┬────────┘                │
         │                        │                         │
         │         ┌──────────────┴──────────────┐         │
         │         │                             │         │
         ▼         ▼                             ▼         ▼
┌─────────────────┐
│   listings      │
├─────────────────┤
│ id (PK)         │
│ book_id (FK)    │
│ seller_id (FK)  │
│ academic_year_id│
│ (FK)            │
│ price           │
│ condition       │
│ status          │
│ description     │
│ photos          │
│ contact_phone   │  ← Seller's phone for buyers to call
│ created_at      │
│ updated_at      │
│ expires_at      │
└─────────────────┘
```

### Table Definitions

#### `academic_years`
```sql
CREATE TABLE academic_years (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(20) NOT NULL UNIQUE,           -- "2024-2025"
    start_date DATE NOT NULL,                   -- 2024-09-01
    end_date DATE NOT NULL,                     -- 2025-06-30
    is_current BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_dates CHECK (end_date > start_date)
);

CREATE UNIQUE INDEX ix_academic_years_current 
ON academic_years(is_current) WHERE is_current = TRUE;
```

#### `books` (Catalog - imported, read-only for users)
```sql
CREATE TABLE books (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(20) NOT NULL,              -- 'textbook' or 'literature'
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    isbn VARCHAR(13),                           -- ISBN-13
    grade_level VARCHAR(20),                    -- "6ème", "5ème", "Terminale"
    subject VARCHAR(100),                       -- "Mathématiques", "Français"
    publisher VARCHAR(100),
    year_published INTEGER,
    catalog_year_id INTEGER NOT NULL,           -- FK to academic_years
    cover_image_url VARCHAR(500),
    metadata JSON,                              -- Flexible extra fields
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (catalog_year_id) REFERENCES academic_years(id)
);

CREATE INDEX ix_books_category ON books(category);
CREATE INDEX ix_books_grade_subject ON books(grade_level, subject);
CREATE INDEX ix_books_title_search ON books(title);
CREATE INDEX ix_books_isbn ON books(isbn);
```

#### `users`
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT NOT NULL UNIQUE,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    language_code VARCHAR(10) DEFAULT 'fr',
    role VARCHAR(20) DEFAULT 'user',            -- 'user', 'admin', 'moderator'
    is_active BOOLEAN DEFAULT TRUE,
    is_banned BOOLEAN DEFAULT FALSE,
    ban_reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_users_telegram_id ON users(telegram_id);
```

#### `listings`
```sql
CREATE TABLE listings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    book_id INTEGER NOT NULL,
    seller_id INTEGER NOT NULL,
    academic_year_id INTEGER NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    condition VARCHAR(20) NOT NULL,             -- 'new', 'like_new', 'good', 'fair', 'poor'
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- 'active', 'reserved', 'sold', 'archived', 'expired'
    description TEXT,
    photos JSON,                                -- Array of Telegram file_ids
    contact_phone VARCHAR(20),                  -- Seller's phone number for buyers
    view_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    reserved_at TIMESTAMP,
    sold_at TIMESTAMP,
    archived_at TIMESTAMP,
    
    FOREIGN KEY (book_id) REFERENCES books(id),
    FOREIGN KEY (seller_id) REFERENCES users(id),
    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id)
);

CREATE INDEX ix_listings_active_search 
ON listings(academic_year_id, status) WHERE status = 'active';
CREATE INDEX ix_listings_seller ON listings(seller_id, status);
CREATE INDEX ix_listings_book ON listings(book_id, status);
CREATE INDEX ix_listings_expires ON listings(expires_at) WHERE status = 'active';
```

**Note for MVP**: The `conversations` and `messages` tables are not included in the MVP. Buyers see the seller's `contact_phone` directly on the listing and contact them outside the bot (call/SMS/WhatsApp).

### Future Features (Backlog)

#### Messaging (Post-MVP)
- Internal buyer/seller messaging system
- Conversation model for message threading
- Message notifications
- "Mes conversations" section in main menu

### Key Design Decisions

1. **Books are immutable catalog entries** - Imported once, referenced by listings. Never modified by users.
2. **Academic year on listings** - Each listing belongs to an academic year for easy archiving.
3. **Soft deletes via status** - Listings never deleted, only status changed (`archived`, `expired`).
4. **Seller contact phone on listing** - Buyers see phone number directly, contact seller outside bot.
5. **JSON for flexible fields** - Photos array, book metadata extensible without migrations.
6. **Denormalized academic_year on listings** - Avoids join for common "current year active listings" query.

## User Flow

### Main Menu (First Interaction)
```
┌─────────────────────────────────┐
│  📚 Bienvenue sur LivreÉcole    │
│                                 │
│  Année scolaire: 2024-2025      │
│                                 │
│  [🔍 Acheter un livre]          │
│  [📝 Mettre en vente]           │
│  [📋 Mes annonces]              │
│  [❓ Aide]                      │
└─────────────────────────────────┘
```

### Flow 1: Buy a Book (Browse & Find)

```
Main Menu → [🔍 Acheter un livre]
    │
    ├─→ Step 1: Choose Category
    │   ├─→ [📚 Manuel scolaire]     (School textbooks)
    │   └─→ [📖 Livre de littérature] (Literature books)
    │
    ├─→ Step 2: Choose Class/Grade
    │   ├─→ [6ème] [5ème] [4ème] [3ème]
    │   ├─→ [2nde] [1ère] [Terminale]
    │   └─→ [⬅️ Retour]
    │
    ├─→ Step 3: Choose Subject (filtered by category + class)
    │   ├─→ [Mathématiques] [Français] [Histoire-Géo]
    │   ├─→ [Physique-Chimie] [SVT] [Anglais]
    │   └─→ [⬅️ Retour]
    │
    ├─→ Step 4: Select Book from list (paginated)
    │   ├─→ Book title, author
    │   └─→ [⬅️ Retour]
    │
    └─→ Step 5: View Active Listings for this Book
        │
        ├─→ Listing Card (for each active listing):
        │   ├─→ Prix: 15,00 €
        │   ├─→ État: Bon
        │   ├─→ Description: "Livre utilisé un trimestre"
        │   ├─→ 📞 Téléphone: 06 12 34 56 78
        │   └─→ [⬅️ Retour aux résultats]
        │
        └─→ Buyer calls/SMS/WhatsApp the seller directly
```

### Flow 2: Sell a Book (Create Listing)

```
Main Menu → [📝 Mettre en vente]
    │
    ├─→ Step 1: Choose Category
    │   ├─→ [📚 Manuel scolaire]
    │   └─→ [📖 Livre de littérature]
    │
    ├─→ Step 2: Choose Class/Grade
    │   └─→ [6ème] [5ème] [4ème] [3ème] [2nde] [1ère] [Terminale]
    │
    ├─→ Step 3: Choose Subject
    │   └─→ [Mathématiques] [Français] [Histoire-Géo] ...
    │
    ├─→ Step 4: Select Book from catalog
    │   └─→ [Select] → Next step
    │
    ├─→ Step 5: Set Price
    │   ├─→ Numeric input with validation
    │   └─→ [Next]
    │
    ├─→ Step 6: Condition
    │   ├─→ [🆕 Neuf] [✨ Comme neuf] [👍 Bon] [👌 Correct] [📦 Usagé]
    │   └─→ [Next]
    │
    ├─→ Step 7: Contact Phone Number (REQUIRED)
    │   ├─→ "Entrez votre numéro de téléphone:"
    │   ├─→ Validates format (French phone: 06/07 XX XX XX XX)
    │   └─→ [Next]
    │
    ├─→ Step 8: Photos (Optional)
    │   ├─→ Send up to 5 photos
    │   ├─→ [⏭️ Ignorer] or [✅ Terminé]
    │
    ├─→ Step 9: Description (Optional)
    │   ├─→ Text input (max 500 chars)
    │   └─→ [⏭️ Ignorer] or [✅ Terminé]
    │
    └─→ Step 10: Confirmation
        ├─→ Summary: Book, Price, Condition, Phone
        ├─→ [✅ Publier] [✏️ Modifier] [❌ Annuler]
        └─→ Success → Returns to "Mes annonces"
```

### Flow 3: Manage Listings (My Listings)

```
Main Menu → [📋 Mes annonces]
    │
    ├─→ Active Listings (tabs: En vente / Réservées / Vendues / Archivées)
    │   │
    │   ├─→ Listing Card: Title, Price, Status badge, Views
    │   │
    │   ├─→ [Select] → Listing Management Menu
    │   │   │
    │   │   ├─→ [✏️ Modifier prix] → New price input
    │   │   ├─→ [🔄 Marquer réservée] → Confirm → Status: reserved
    │   │   ├─→ [✅ Marquer vendue] → Confirm → Status: sold
    │   │   ├─→ [📝 Modifier description] → Edit text
    │   │   ├─→ [🖼️ Gérer photos] → Add/remove photos
    │   │   ├─→ [📞 Modifier téléphone] → Update phone
    │   │   └─→ [🗑️ Supprimer] → Confirm → Status: archived
    │   │
    │   └─→ [➕ Nouvelle annonce] → Create flow
    │
    └─→ Expired Listings (auto-archived after 180 days)
        └─→ [🔄 Republier] → Creates new listing with same data
```

### Flow 4: Academic Year Transition (Admin)

```
Admin Panel → [📅 Gestion année scolaire]
    │
    ├─→ Current: 2024-2025 (Active)
    ├─→ Previous: 2023-2024 (Archived)
    │
    ├─→ [➕ Créer nouvelle année] → 2025-2026
    │   ├─→ Name: "2025-2026"
    │   ├─→ Start: 2025-09-01
    │   ├─→ End: 2026-06-30
    │   └─→ [Créer]
    │
    ├─→ [🔄 Activer nouvelle année]
    │   ├─→ Archives all active listings from old year
    │   ├─→ Marks old year as not current
    │   ├─→ Sets new year as current
    │   ├─→ Notifies users with active listings
    │   └─→ [Confirmer]
    │
    └─→ [📥 Importer catalogue] → Upload Excel/CSV for new year
```

## Project Roadmap

### Milestone 1: Foundation (Week 1-2) ✅ Current
- [x] Project documentation (README, RULES, PROJECT)
- [ ] Project structure setup
- [ ] Database models + Alembic migrations
- [ ] Configuration management (.env, Pydantic Settings)
- [ ] Basic bot scaffolding (aiogram, middlewares, logging)
- [ ] French locale system

### Milestone 2: Catalog & Search (Week 2-3)
- [ ] Catalog import service (Excel/CSV)
- [ ] Validation & deduplication
- [ ] Search service (full-text, filters)
- [ ] Catalog browsing handlers
- [ ] Pagination keyboard system

### Milestone 3: Listings Core (Week 3-4)
- [ ] Create listing FSM (multi-step)
- [ ] Listing repository & service
- [ ] My listings management
- [ ] Status transitions (active → reserved → sold)
- [ ] Photo upload handling

### Milestone 4: Notifications & Polish (Week 4-5)
- [ ] Notification service (listing status changes)
- [ ] Admin notifications for important events
- [ ] Inline keyboards for quick actions
- [ ] Error handling and edge cases

### Milestone 5: Academic Year & Admin (Week 5-6)
- [ ] Academic year management
- [ ] Year transition script (archive + notify)
- [ ] Admin panel (catalog import, year management, user moderation)
- [ ] Automated expiry job (background task)

### Milestone 6: Polish & Deploy (Week 6-7)
- [ ] Comprehensive testing (unit + integration)
- [ ] Docker configuration
- [ ] CI/CD pipeline
- [ ] Documentation completion
- [ ] Production deployment guide
- [ ] Load testing

### Post-Launch (Continuous)
- [ ] User feedback collection
- [ ] Performance optimization
- [ ] Feature requests prioritization
- [ ] Mobile app consideration

## Future Features (Backlog)

### High Priority
1. **Wishlist / Want-to-Buy** - Users post what they need, sellers notified
2. **Price History** - Show price trends for each book
3. **Seller Ratings** - Post-transaction ratings
4. **Proximity Filter** - Location-based search (school-based)

### Medium Priority
5. **Bulk Import for Schools** - Admin uploads entire curriculum
6. **Teacher Verification** - Badge for verified teachers
7. **Automated Price Suggestion** - ML-based on condition/year
8. **Export My Data** - GDPR compliance

### Low Priority / Nice to Have
9. **Web Dashboard** - React admin panel
10. **API for School Systems** - Integration with school management software
11. **OCR Book Recognition** - Scan cover to identify book
12. **Multi-language UI** - English, Spanish, Arabic

## Important Implementation Decisions

### 1. Catalog Import Strategy
**Decision**: Separate import script + service, not part of bot runtime.
**Rationale**: 
- Import is admin operation, not user-facing
- Can run independently, validate before committing
- Supports large files without blocking bot
- Allows dry-run mode

**Implementation**:
```bash
# Import catalog via CLI
python -m bot.import_catalog catalog.xlsx
python -m bot.import_catalog catalog.xlsx --year-id 2
```

### 2. Academic Year Transition
**Decision**: Explicit admin action with automatic archiving.
**Rationale**:
- Predictable, controlled transition
- Preserves all historical data
- Notifies affected users
- Can be tested in staging first

**Process**:
1. Admin creates new academic year
2. Admin imports new catalog (optional, can reuse)
3. Admin triggers "Activate New Year"
4. System:
   - Archives all `active`/`reserved` listings from old year
   - Sets `archived_at` timestamp
   - Sends notification to sellers
   - Switches `is_current` flag
5. Bot now shows new year's catalog and listings

### 3. Listing Status Machine
```
active → reserved → sold
  │         │
  │         └→ active (if buyer cancels)
  │
  ├→ expired (auto after 180 days)
  │
  └→ archived (manual by seller or admin)
```
**Decision**: Explicit status enum, no deleted listings.
**Rationale**: Full audit trail, analytics, dispute resolution.

### 4. FSM for Multi-Step Flows
**Decision**: aiogram's built-in FSM with in-memory storage for MVP.
**Rationale**:
- Handles user dropping out mid-flow
- Simple to implement, no external dependencies
- Clear state visualization
- Easy to test
- Can upgrade to Redis/SQLite later if needed

### 5. Search Implementation
**Decision**: SQLite FTS5 for development, PostgreSQL `tsvector` for production.
**Rationale**: 
- No external dependencies (Elasticsearch) for MVP
- Good enough for catalog size (< 5000 books)
- Easy migration path

### 6. Photo Handling
**Decision**: Store Telegram `file_id` only, not download files.
**Rationale**:
- No storage costs
- Telegram CDN handles delivery
- `file_id` permanent for bot lifetime
- Max 5 photos per listing (Telegram limit)

### 7. Rate Limiting
**Decision**: Per-user sliding window (30 req/min for read, 10 req/min for write).
**Rationale**: Prevents spam, allows normal usage, configurable.

### 8. Error Handling Strategy
**Decision**: Custom exception hierarchy + global error middleware.
**Rationale**: 
- User-friendly French messages
- Structured logging for debugging
- Admin alerts for critical errors
- No stack traces to users

### 9. Testing Strategy
**Decision**: 
- Unit tests for services/repositories (mocked DB)
- Integration tests for handlers (test DB)
- Fixtures for catalog data
- Property-based testing for import validation

---

## Appendix: Key French Terminology

| English | French (UI) |
|---------|-------------|
| Listing | Annonce |
| Active | En vente |
| Reserved | Réservée |
| Sold | Vendue |
| Archived | Archivée |
| Expired | Expirée |
| Condition | État |
| New | Neuf |
| Like New | Comme neuf |
| Good | Bon |
| Fair | Correct |
| Poor | Usagé |
| Academic Year | Année scolaire |
| Category | Catégorie |
| Catalog | Catalogue |
| Grade Level | Niveau / Classe |
| Subject | Matière |
| Seller | Vendeur |
| Buyer | Acheteur |
| Phone | Téléphone |
| Price | Prix |
| Search | Rechercher |
| Filter | Filtrer |
| My Listings | Mes annonces |
| Create Listing | Mettre en vente |