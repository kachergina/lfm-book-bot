"""Listing service for business logic."""

import re
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from bot.database.models import Listing
from bot.database.repository import (
    AcademicYearRepository,
    BookRepository,
    ListingRepository,
    UserRepository,
)

VALID_STATUSES = {"active", "reserved", "sold", "archived", "expired"}

VALID_TRANSITIONS: dict[str, set[str]] = {
    "active": {"reserved", "sold", "archived", "expired"},
    "reserved": {"active", "sold", "archived"},
    "sold": set(),
    "archived": set(),
    "expired": set(),
}

VALID_CONDITIONS = {"new", "like_new", "good", "fair", "poor"}

PHONE_PATTERN = re.compile(r"^\+[1-9]\d{6,14}$")
TELEGRAM_PATTERN = re.compile(r"^@[A-Za-z0-9_]{5,32}$")

MAX_PHOTOS = 5
MAX_DESCRIPTION_LENGTH = 500
MAX_TITLE_LENGTH = 255
MAX_PRICE = Decimal("99999.99")
MIN_PRICE = Decimal("0.01")


class ListingValidationError(Exception):
    """Raised when listing validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class ListingOwnershipError(Exception):
    """Raised when user tries to manage a listing they don't own."""


class InvalidTransitionError(Exception):
    """Raised when an invalid status transition is attempted."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"Cannot transition from '{from_status}' to '{to_status}'")
        self.from_status = from_status
        self.to_status = to_status


class ListingService:
    """Service for listing business logic."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize listing service.

        Args:
            session: Database session.
        """
        self.session = session
        self.listing_repo = ListingRepository(session)
        self.book_repo = BookRepository(session)
        self.user_repo = UserRepository(session)
        self.year_repo = AcademicYearRepository(session)

    @staticmethod
    def validate_price(price: str) -> Decimal:
        """Validate and convert price string to Decimal.

        Args:
            price: Price string.

        Returns:
            Validated price as Decimal.

        Raises:
            ListingValidationError: If price is invalid.
        """
        try:
            price_decimal = Decimal(price)
        except Exception as e:
            raise ListingValidationError("Le prix doit être un nombre valide.") from e

        if price_decimal < MIN_PRICE:
            raise ListingValidationError(f"Le prix minimum est {MIN_PRICE} ₽.")

        if price_decimal > MAX_PRICE:
            raise ListingValidationError(f"Le prix maximum est {MAX_PRICE} ₽.")

        # Round to 2 decimal places
        return price_decimal.quantize(Decimal("0.01"))

    @staticmethod
    def validate_condition(condition: str) -> str:
        """Validate condition value.

        Args:
            condition: Condition string.

        Returns:
            Validated condition.

        Raises:
            ListingValidationError: If condition is invalid.
        """
        if condition not in VALID_CONDITIONS:
            raise ListingValidationError(
                f"État invalide. Valeurs acceptées : {', '.join(VALID_CONDITIONS)}"
            )
        return condition

    @staticmethod
    def validate_phone(phone: str) -> str:
        """Validate international phone number format.

        Args:
            phone: Phone number string.

        Returns:
            Validated phone number.

        Raises:
            ListingValidationError: If phone is invalid.
        """
        cleaned = phone.replace(" ", "").replace("-", "").strip()
        if not PHONE_PATTERN.match(cleaned):
            raise ListingValidationError(
                "Numéro de téléphone invalide.\n"
                "Entrez votre numéro avec l'indicatif du pays.\n"
                "Exemple : +7 999 123 45 67"
            )
        return cleaned

    @staticmethod
    def validate_telegram_username(username: str) -> str:
        """Validate Telegram username format.

        Args:
            username: Telegram username string.

        Returns:
            Validated username.

        Raises:
            ListingValidationError: If username is invalid.
        """
        cleaned = username.strip()
        if not TELEGRAM_PATTERN.match(cleaned):
            raise ListingValidationError(
                "Nom d'utilisateur Telegram invalide.\n"
                "Format attendu : @username\n"
                "5 à 32 caractères, lettres, chiffres et underscores."
            )
        return cleaned

    @staticmethod
    def validate_book_title(title: str) -> str:
        """Validate a custom book title.

        Args:
            title: Book title entered by the seller.

        Returns:
            Validated title.

        Raises:
            ListingValidationError: If title is empty or too long.
        """
        trimmed = title.strip()
        if not trimmed:
            raise ListingValidationError("Le titre du livre est obligatoire.")
        if len(trimmed) > MAX_TITLE_LENGTH:
            raise ListingValidationError(
                f"Le titre ne peut pas dépasser {MAX_TITLE_LENGTH} caractères."
            )
        return trimmed

    @staticmethod
    def validate_description(description: str | None) -> str | None:
        """Validate description length.

        Args:
            description: Description text.

        Returns:
            Validated description.

        Raises:
            ListingValidationError: If description is too long.
        """
        if description is None:
            return None
        trimmed = description.strip()
        if len(trimmed) > MAX_DESCRIPTION_LENGTH:
            raise ListingValidationError(
                f"La description ne peut pas dépasser {MAX_DESCRIPTION_LENGTH} caractères."
            )
        return trimmed if trimmed else None

    @staticmethod
    def validate_photos(photos: list[str] | None) -> list[str] | None:
        """Validate photos list.

        Args:
            photos: List of Telegram file_ids.

        Returns:
            Validated photos list.

        Raises:
            ListingValidationError: If photos are invalid.
        """
        if photos is None:
            return None
        if len(photos) > MAX_PHOTOS:
            raise ListingValidationError(f"Vous ne pouvez pas ajouter plus de {MAX_PHOTOS} photos.")
        # Filter out empty strings
        cleaned = [p for p in photos if p.strip()]
        return cleaned if cleaned else None

    async def create_listing(
        self,
        book_id: int,
        seller_id: int,
        price: Decimal,
        condition: str,
        phone: str,
        contact_method: str = "phone",
        description: str | None = None,
        photos: list[str] | None = None,
    ) -> Listing:
        """Create a new listing.

        Args:
            book_id: Book ID from catalog.
            seller_id: User (seller) ID.
            price: Listing price.
            condition: Book condition.
            phone: Seller's contact value (phone or telegram).
            contact_method: Contact method ('phone' or 'telegram').
            description: Optional description.
            photos: Optional list of Telegram file_ids.

        Returns:
            Created listing.

        Raises:
            ListingValidationError: If validation fails.
        """
        # Verify book exists
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise ListingValidationError("Livre non trouvé dans le catalogue.")

        # Get current academic year
        year = await self.year_repo.get_current()
        if year is None:
            raise ListingValidationError("Aucune année scolaire configurée.")

        # Check user listing limit
        from bot.config import get_settings

        settings = get_settings()
        active_count = await self.listing_repo.count_active_by_user(seller_id)
        if active_count >= settings.max_listings_per_user:
            raise ListingValidationError(
                f"Vous avez atteint la limite de {settings.max_listings_per_user} annonces actives."
            )

        return await self.listing_repo.create_listing(
            book_id=book_id,
            seller_id=seller_id,
            academic_year_id=year.id,
            price=float(price),
            condition=condition,
            contact_phone=phone,
            contact_method=contact_method,
            description=description,
            photos=photos,
        )

    async def get_user_listing(
        self,
        listing_id: int,
        seller_id: int,
    ) -> Listing:
        """Get a listing owned by a specific user.

        Args:
            listing_id: Listing ID.
            seller_id: User (seller) ID.

        Returns:
            The listing.

        Raises:
            ListingValidationError: If listing not found.
            ListingOwnershipError: If user doesn't own the listing.
        """
        listing = await self.listing_repo.get_user_listing_by_id(listing_id, seller_id)
        if listing is None:
            # Check if listing exists at all
            exists = await self.listing_repo.get_by_id(listing_id)
            if exists is None:
                raise ListingValidationError("Annonce non trouvée.")
            raise ListingOwnershipError
        return listing

    async def get_user_listings(
        self,
        seller_id: int,
        status: str | None = None,
    ) -> list[Listing]:
        """Get listings for a user.

        Args:
            seller_id: User (seller) ID.
            status: Optional status filter.

        Returns:
            List of listings.
        """
        return await self.listing_repo.get_user_listings(seller_id, status)

    async def update_status(
        self,
        listing_id: int,
        seller_id: int,
        new_status: str,
    ) -> Listing:
        """Update listing status with transition validation.

        Args:
            listing_id: Listing ID.
            seller_id: User (seller) ID.
            new_status: New status.

        Returns:
            Updated listing.

        Raises:
            ListingValidationError: If listing not found.
            ListingOwnershipError: If user doesn't own the listing.
            InvalidTransitionError: If transition is not allowed.
        """
        listing = await self.get_user_listing(listing_id, seller_id)

        if new_status not in VALID_STATUSES:
            raise ListingValidationError(f"Statut invalide : {new_status}")

        allowed = VALID_TRANSITIONS.get(listing.status, set())
        if new_status not in allowed:
            raise InvalidTransitionError(listing.status, new_status)

        result = await self.listing_repo.update_status(listing_id, new_status)
        if result is None:
            raise ListingValidationError("Erreur lors de la mise à jour du statut.")
        return result

    async def update_field(
        self,
        listing_id: int,
        seller_id: int,
        field: str,
        value: object,
    ) -> Listing:
        """Update a listing field with validation.

        Args:
            listing_id: Listing ID.
            seller_id: User (seller) ID.
            field: Field name to update.
            value: New value.

        Returns:
            Updated listing.

        Raises:
            ListingValidationError: If validation fails.
            ListingOwnershipError: If user doesn't own the listing.
        """
        await self.get_user_listing(listing_id, seller_id)

        # Validate field-specific rules
        updated: Listing | None = None
        if field == "price":
            validated_price = self.validate_price(str(value))
            updated = await self.listing_repo.update_field(
                listing_id, field, float(validated_price)
            )
        elif field == "condition":
            validated_condition = self.validate_condition(str(value))
            updated = await self.listing_repo.update_field(listing_id, field, validated_condition)
        elif field == "contact_phone":
            # Accept both phone and telegram username
            updated = await self.listing_repo.update_field(listing_id, field, str(value))
        elif field == "contact_method":
            if value not in ("phone", "telegram"):
                raise ListingValidationError("Méthode de contact invalide.")
            updated = await self.listing_repo.update_field(listing_id, field, str(value))
        elif field == "description":
            desc_value = value if isinstance(value, str) else str(value)
            validated_desc = self.validate_description(desc_value)
            updated = await self.listing_repo.update_field(listing_id, field, validated_desc)
        elif field == "photos":
            validated_photos = self.validate_photos(value) if isinstance(value, list) else None
            updated = await self.listing_repo.update_field(listing_id, field, validated_photos)
        else:
            raise ListingValidationError(f"Champ non modifiable : {field}")

        if updated is None:
            raise ListingValidationError("Erreur lors de la mise à jour.")

        return updated

    async def expire_listings(
        self,
        expiry_days: int | None = None,
    ) -> list[Listing]:
        """Expire listings that have passed their expiry date.

        This method is idempotent: running it multiple times with the same
        data will not modify already-expired listings.

        Args:
            expiry_days: Number of days for expiry. If None, uses config value.

        Returns:
            List of listings that were expired.
        """
        if expiry_days is None:
            from bot.config import get_settings

            settings = get_settings()
            expiry_days = settings.listing_expiry_days

        # Find expired candidates
        expired_candidates = await self.listing_repo.get_expired_listings(
            expiry_days,
        )

        if not expired_candidates:
            return []

        # Collect IDs and expire them
        listing_ids = [listing.id for listing in expired_candidates]
        await self.listing_repo.bulk_expire(listing_ids)

        # Return the listings that were actually expired
        return expired_candidates
