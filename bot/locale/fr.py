"""French translations for the user interface."""

# Main menu
WELCOME_MESSAGE = "Bienvenue sur LFM Bourse aux livres !"
MAIN_MENU_TITLE = "📚 Menu principal"
MAIN_MENU_ACADEMIC_YEAR = "Année scolaire: {year}"

# Main menu buttons
BTN_BUY_BOOK = "🔍 Acheter un livre"
BTN_SELL_BOOK = "📝 Mettre en vente"
BTN_MY_LISTINGS = "📋 Mes annonces"
BTN_HELP = "❓ Aide"

# Placeholder messages for unimplemented features
MSG_BUY_NOT_IMPLEMENTED = "Cette fonctionnalité sera disponible prochainement."
MSG_SELL_NOT_IMPLEMENTED = "Cette fonctionnalité sera disponible prochainement."
MSG_LISTINGS_NOT_IMPLEMENTED = "Cette fonctionnalité sera disponible prochainement."

# Help
HELP_MESSAGE = (
    "Aide - LFM Bourse aux livres\n\n"
    "Ce bot vous permet d'acheter et de vendre des manuels scolaires "
    "et des livres de littérature.\n\n"
    "Commandes disponibles:\n"
    "/start - Afficher le menu principal\n"
    "/help - Afficher cette aide\n\n"
    "Fonctionnalités:\n"
    "- 🔍 Acheter un livre\n"
    "- 📝 Mettre un livre en vente\n"
    "- 📋 Gérer vos annonces"
)

# Error messages
MSG_ERROR = "Une erreur s'est produite. Veuillez réessayer."
MSG_UNEXPECTED_ERROR = "Une erreur inattendue s'est produite."

# Database
MSG_DB_ERROR = "Erreur de base de données. Veuillez réessayer."

# Buying flow - Category selection
BUY_SELECT_CATEGORY = "Choisissez une catégorie :"
CATEGORY_TEXTBOOK = "📚 Manuel scolaire"
CATEGORY_LITERATURE = "📖 Livre de littérature"

# Buying flow - Grade level selection
BUY_SELECT_GRADE = "Choisissez la classe :"

# Buying flow - Subject selection
BUY_SELECT_SUBJECT = "Choisissez la matière :"

# Buying flow - Book selection
BUY_SELECT_BOOK = "Choisissez un livre :"
BUY_BOOK_INFO = "📖 {title}"
BUY_BOOK_AUTHOR = "Auteur: {author}"
BUY_BOOK_PUBLISHER = "Éditeur: {publisher}"

# Buying flow - Listings
BUY_LISTINGS_TITLE = "📋 Annonces disponibles pour : {book_title}"
BUY_LISTING_ITEM = "💰 Prix: {price} ₽\n📦 État: {condition}\n📞 Contact : {contact}"
BUY_LISTING_ITEM_TELEGRAM = "💰 Prix: {price} ₽\n📦 État: {condition}\n💬 Telegram : {contact}"
BUY_LISTING_NO_DESCRIPTION = "Pas de description"
BUY_NO_LISTINGS = "Aucune annonce disponible pour ce livre pour le moment."
BUY_BTN_VIEW_PHOTOS = "📸 Voir les photos"
BUY_PHOTOS_NAV = "Utilisez les boutons ci-dessous pour naviguer :"

# Navigation
BTN_BACK = "⬅️ Retour"
BTN_MAIN_MENU = "🏠 Menu principal"

# Academic year errors
MSG_NO_ACADEMIC_YEAR = (
    "Aucune année scolaire n'est configurée. Veuillez contacter l'administrateur."
)
MSG_NO_BOOKS_IN_CATEGORY = "Aucun livre trouvé dans cette catégorie."

# Condition labels
CONDITION_NEW = "Neuf"
CONDITION_LIKE_NEW = "Comme neuf"
CONDITION_GOOD = "Bon"
CONDITION_FAIR = "Correct"
CONDITION_POOR = "Usagé"

CONDITION_LABELS = {
    "new": CONDITION_NEW,
    "like_new": CONDITION_LIKE_NEW,
    "good": CONDITION_GOOD,
    "fair": CONDITION_FAIR,
    "poor": CONDITION_POOR,
}

# Condition callback values
CONDITION_CALLBACK_LABELS = {
    "new": "🆕 Neuf",
    "like_new": "✨ Comme neuf",
    "good": "👍 Bon",
    "fair": "👌 Correct",
    "poor": "📦 Usagé",
}

# Status labels
STATUS_ACTIVE = "En vente"
STATUS_RESERVED = "Réservée"
STATUS_SOLD = "Vendue"
STATUS_ARCHIVED = "Archivée"
STATUS_EXPIRED = "Expirée"

STATUS_LABELS = {
    "active": STATUS_ACTIVE,
    "reserved": STATUS_RESERVED,
    "sold": STATUS_SOLD,
    "archived": STATUS_ARCHIVED,
    "expired": STATUS_EXPIRED,
}

# ===== SELL FLOW =====

# Sell flow - Category selection (same as buy flow but with sell context)
SELL_SELECT_CATEGORY = "Choisissez la catégorie du livre à vendre :"

# Sell flow - Grade selection
SELL_SELECT_GRADE = "Choisissez la classe :"

# Sell flow - Subject selection
SELL_SELECT_SUBJECT = "Choisissez la matière :"

# Sell flow - Book selection
SELL_SELECT_BOOK = "Sélectionnez le livre dans le catalogue :"
SELL_NO_BOOKS = "Aucun livre trouvé dans cette catégorie. Essayez une autre catégorie."

# Sell flow - Price
SELL_ENTER_PRICE = "💰 Entrez le prix en roubles (₽) :\nExemple : 1500"
SELL_PRICE_INVALID = "Prix invalide. Veuillez entrer un nombre positif (ex : 15.00)."

# Sell flow - Condition
SELL_SELECT_CONDITION = "Choisissez l'état du livre :"

# Sell flow - Phone
SELL_ENTER_PHONE = (
    "📞 Entrez votre numéro de téléphone avec l'indicatif du pays.\nExemple : +7 999 123 45 67"
)
SELL_PHONE_INVALID = (
    "Numéro de téléphone invalide.\n"
    "Entrez votre numéro avec l'indicatif du pays.\n"
    "Exemple : +7 999 123 45 67"
)

# Sell flow - Telegram username
SELL_ENTER_TELEGRAM = "💬 Entrez votre nom d'utilisateur Telegram.\nExemple : @username"
SELL_TELEGRAM_INVALID = (
    "Nom d'utilisateur Telegram invalide.\n"
    "Format attendu : @username\n"
    "5 à 32 caractères, lettres, chiffres et underscores."
)

# Sell flow - Contact method selection
SELL_SELECT_CONTACT_METHOD = "📞 Comment souhaitez-vous être contacté par les acheteurs ?"
SELL_CONTACT_METHOD_PHONE = "📱 Numéro de téléphone"
SELL_CONTACT_METHOD_TELEGRAM = "💬 Nom d'utilisateur Telegram"

# Sell flow - Photos
SELL_UPLOAD_PHOTOS = (
    "📸 Ajoutez jusqu'à 5 photos de votre livre.\n"
    "Vous pouvez envoyer vos photos ou cliquer sur « ⏭️ Ignorer »."
)
SELL_PHOTOS_RECEIVED = (
    "📸 Photo reçue ({count}/{max}).\n"
    "Si vous souhaitez ajouter d'autres photos, envoyez-les. "
    "Sinon, cliquez sur « ✅ Terminer »."
)
SELL_PHOTOS_MAX_REACHED = "Maximum de {max} photos atteint."
SELL_PHOTOS_DONE = "Photos enregistrées."
SELL_PHOTOS_NONE = "Aucune photo ajoutée."

# Sell flow - Description
SELL_ENTER_DESCRIPTION = (
    "📝 Description (optionnel)\n\n"
    "Décrivez votre livre (état, défauts, notes personnelles, etc.).\n"
    "Maximum 500 caractères.\n"
    "Pour passer cette étape, appuyez sur « ⏭️ Ignorer »."
)
SELL_DESCRIPTION_TOO_LONG = "La description ne peut pas dépasser 500 caractères."

# Sell flow - Confirmation
SELL_CONFIRM_TITLE = "📋 Récapitulatif de votre annonce :"
SELL_CONFIRM_BOOK = "📖 Livre : {title}"
SELL_CONFIRM_PRICE = "💰 Prix : {price} ₽"
SELL_CONFIRM_CONDITION = "📦 État : {condition}"
SELL_CONFIRM_PHONE = "📞 Contact : {phone}"
SELL_CONFIRM_DESCRIPTION = "📝 Description : {description}"
SELL_CONFIRM_PHOTOS = "📸 Photos : {count}"

SELL_CONFIRM_ACTIONS = "Voulez-vous publier cette annonce ?"
SELL_PUBLISH_SUCCESS = "✅ Votre annonce a été publiée avec succès !"
SELL_PUBLISH_CANCELLED = "❌ Annonce annulée."

# Sell flow - Edit actions in confirmation
SELL_EDIT_PRICE = "Modifier le prix"
SELL_EDIT_CONDITION = "Modifier l'état"
SELL_EDIT_PHONE = "Modifier le contact"
SELL_EDIT_DESCRIPTION = "Modifier la description"
SELL_EDIT_PHOTOS = "Modifier les photos"

# ===== MY LISTINGS =====

MY_LISTINGS_TITLE = "📋 Vos annonces"
MY_LISTINGS_EMPTY = "Vous n'avez aucune annonce pour le moment."
MY_LISTINGS_TAB_ACTIVE = "En vente ({count})"
MY_LISTINGS_TAB_RESERVED = "Réservées ({count})"
MY_LISTINGS_TAB_SOLD = "Vendues ({count})"
MY_LISTINGS_TAB_ARCHIVED = "Archivées ({count})"

# Listing card
LISTING_CARD_TITLE = "📖 {title}"
LISTING_CARD_PRICE = "💰 {price} ₽"
LISTING_CARD_CONDITION = "📦 État : {condition}"
LISTING_CARD_STATUS = "🏷️ Statut : {status}"
LISTING_CARD_PHONE = "📞 Contact : {phone}"
LISTING_CARD_VIEWS = "👀 Vues : {views}"
LISTING_CARD_DESCRIPTION = "📝 {description}"
LISTING_CARD_PHOTOS = "📸 Photos : {count}"

# Listing management
MANAGE_LISTING_TITLE = "Gestion de l'annonce"
MANAGE_LISTING_ACTIONS = "Choisissez une action :"

BTN_EDIT_PRICE = "✏️ Modifier prix"
BTN_EDIT_CONDITION = "✏️ Modifier état"
BTN_EDIT_PHONE = "✏️ Modifier contact"
BTN_EDIT_DESCRIPTION = "✏️ Modifier description"
BTN_MARK_RESERVED = "🔄 Marquer réservée"
BTN_MARK_SOLD = "✅ Marquer vendue"
BTN_MARK_ACTIVE = "🔄 Remettre en vente"
BTN_ARCHIVE = "🗑️ Supprimer"

# Status change confirmations
CONFIRM_MARK_RESERVED = "Marquer cette annonce comme réservée ?"
CONFIRM_MARK_SOLD = "Marquer cette annonce comme vendue ?"
CONFIRM_MARK_ACTIVE = "Remettre cette annonce en vente ?"
CONFIRM_ARCHIVE = "Supprimer cette annonce ?"
STATUS_CHANGED = "✅ Statut mis à jour : {status}"

# Listing edited
LISTING_EDITED_PRICE = "Prix mis à jour : {price} ₽"
LISTING_EDITED_CONDITION = "État mis à jour : {condition}"
LISTING_EDITED_PHONE = "Contact mis à jour : {phone}"
LISTING_EDITED_DESCRIPTION = "Description mise à jour."
LISTING_EDITED_PHOTOS = "Photos mises à jour."

# Listing management back buttons
BTN_BACK_TO_LISTINGS = "⬅️ Retour à mes annonces"
BTN_BACK_TO_MANAGE = "⬅️ Retour à la gestion"

# Listing selection
SELECT_LISTING_PROMPT = "Sélectionnez une annonce à gérer :"
NO_LISTINGS_IN_CATEGORY = "Aucune annonce dans cette catégorie."

# Listings count
LISTINGS_COUNT = "{total} annonce(s)"

# ===== MILESTONE 4: NOTIFICATIONS =====

# Seller notifications
NOTIF_LISTING_RESERVED = (
    "📢 Annonce réservée\n\n📖 {title}\n💰 {price} ₽\n\nVotre annonce a été marquée comme réservée."
)
NOTIF_LISTING_SOLD = (
    "📢 Annonce vendue\n\n"
    "📖 {title}\n"
    "💰 {price} ₽\n\n"
    "Félicitations ! Votre annonce a été marquée comme vendue."
)
NOTIF_LISTING_ACTIVATED = (
    "📢 Annonce remise en vente\n\n"
    "📖 {title}\n"
    "💰 {price} ₽\n\n"
    "Votre annonce est de nouveau visible par les acheteurs."
)
NOTIF_LISTING_ARCHIVED = (
    "📢 Annonce archivée\n\n📖 {title}\n💰 {price} ₽\n\nVotre annonce a été supprimée."
)

# Notification quick actions
BTN_VIEW_LISTING = "👁️ Voir l'annonce"

# Admin notifications
ADMIN_NOTIF_ERROR = "⚠️ Erreur système"
ADMIN_NOTIF_ERROR_DETAIL = "⚠️ Erreur non gérée\n\nUtilisateur: {user_id}\nErreur: {error}"
ADMIN_NOTIF_LISTING_CREATED = (
    "📝 Nouvelle annonce publiée\n\nVendeur: {seller}\nLivre: {title}\nPrix: {price} ₽"
)

# Error messages for edge cases
MSG_LISTING_NOT_FOUND = "Cette annonce n'existe plus."
MSG_NOT_YOUR_LISTING = "Cette annonce ne vous appartient pas."
MSG_INVALID_ACTION = "Action invalide."
MSG_INVALID_CALLBACK = "Action obsolète. Veuillez recommencer."
MSG_STATUS_TRANSITION_INVALID = "Transition de statut impossible."
MSG_LISTING_EXPIRED = "Cette annonce a expiré."
MSG_LISTING_UNAVAILABLE = "Cette annonce n'est plus disponible."
MSG_SOMETHING_WENT_WRONG = "Une erreur s'est produite. Veuillez réessayer."
MSG_OPERATION_FAILED = "L'opération a échoué. Veuillez réessayer."
MSG_USER_NOT_FOUND = "Utilisateur non trouvé."
MSG_DATA_ERROR = "Données invalides. Veuillez recommencer depuis le menu."

# ===== MILESTONE 5: ADMIN & ACADEMIC YEAR =====

# Admin authorization
MSG_NOT_ADMIN = "⛔ Accès refusé. Vous n'êtes pas administrateur."
MSG_BANNED = "🚫 Votre compte a été suspendu. Contactez un administrateur."

# Admin panel
ADMIN_PANEL_TITLE = "⚙️ Administration"
ADMIN_PANEL_CATALOG = "📚 Importer le catalogue"
ADMIN_PANEL_YEARS = "📅 Années scolaires"
ADMIN_PANEL_USERS = "👤 Gestion des utilisateurs"
ADMIN_PANEL_BACK = "⬅️ Retour"

# Academic year management
ADMIN_YEARS_TITLE = "📅 Années scolaires"
ADMIN_YEARS_CURRENT = "📌 Année courante : {name}"
ADMIN_YEARS_NO_CURRENT = "Aucune année scolaire courante"
ADMIN_YEARS_CREATE = "➕ Créer une année scolaire"
ADMIN_YEARS_SET_CURRENT = "📌 Définir comme courante"
ADMIN_YEARS_YEAR_INFO = "📌 {name}\n📅 Du {start} au {end}\n{current_badge}"

# Academic year creation
ADMIN_YEAR_CREATE_PROMPT = "Entrez le nom de l'année scolaire (ex: 2025-2026) :"
ADMIN_YEAR_CREATE_START = "Entrez la date de début (JJ/MM/AAAA) :"
ADMIN_YEAR_CREATE_END = "Entrez la date de fin (JJ/MM/AAAA) :"
ADMIN_YEAR_CREATE_CONFIRM = "Créer l'année scolaire « {name} » ?\n📅 Du {start} au {end}"
ADMIN_YEAR_CREATED = "✅ Année scolaire « {name} » créée."
ADMIN_YEAR_NAME_INVALID = "Nom invalide. Format attendu : AAAA-AAAA (ex: 2025-2026)"
ADMIN_YEAR_DATE_INVALID = "Date invalide. Format attendu : JJ/MM/AAAA"
ADMIN_YEAR_DATE_ORDER = "La date de fin doit être postérieure à la date de début."
ADMIN_YEAR_ALREADY_EXISTS = "Cette année scolaire existe déjà."
ADMIN_YEAR_IS_CURRENT = "Cette année est déjà l'année courante."

# Year transition
ADMIN_TRANSITION_TITLE = "🔄 Changer d'année scolaire"
ADMIN_TRANSITION_CURRENT = "📌 Année courante : {name}"
ADMIN_TRANSITION_TARGET = "📌 Année cible : {name}"
ADMIN_TRANSITION_CONFIRM = (
    "Changer l'année scolaire courante ?\n\n"
    "📌 De « {old_name} » vers « {new_name} »\n"
    "📦 {archived_count} annonce(s) seront archivées."
)
ADMIN_TRANSITION_SUCCESS = (
    "✅ Année scolaire changée avec succès !\n\n"
    "📌 Nouvelle année courante : {name}\n"
    "📦 {archived_count} annonce(s) archivées."
)
ADMIN_TRANSITION_NO_CURRENT = "Aucune année courante à remplacer."

# Catalog import
ADMIN_IMPORT_TITLE = "📚 Importer le catalogue"
ADMIN_IMPORT_SEND_FILE = (
    "Envoyez un fichier Excel (.xlsx) ou CSV (.csv) pour importer le catalogue.\n"
    "Le fichier sera importé pour l'année scolaire courante."
)
ADMIN_IMPORT_NO_CURRENT_YEAR = (
    "⚠️ Aucune année scolaire courante configurée.\nCréez d'abord une année scolaire."
)
ADMIN_IMPORT_PROCESSING = "⏳ Import en cours..."
ADMIN_IMPORT_SUCCESS = (
    "✅ Import terminé !\n\n"
    "📊 Résultat :\n"
    "• Livres traités : {parsed}\n"
    "• Nouveaux livres : {created}\n"
    "• Livres existants : {existing}"
)
ADMIN_IMPORT_ERRORS = "⚠️ Erreurs lors de l'import :\n{errors}"
ADMIN_IMPORT_INVALID_FILE = "❌ Format de fichier invalide. Envoyez un .xlsx ou .csv."

# User management
ADMIN_USERS_TITLE = "👤 Gestion des utilisateurs"
ADMIN_USERS_SEARCH = "🔍 Rechercher un utilisateur"
ADMIN_USERS_LIST = "📋 Liste des utilisateurs"
ADMIN_USERS_SEARCH_PROMPT = "Entrez un nom d'utilisateur ou un identifiant :"

# User info
ADMIN_USER_INFO = (
    "👤 {name}\n🆔 ID : {telegram_id}\n📛 Rôle : {role}\n{'🚫 Banni' if is_banned else '✅ Actif'}"
)
ADMIN_USER_INFO_BANNED = " Raison : {reason}"

# Ban/unban
ADMIN_USER_BAN = "🚫 Bannir"
ADMIN_USER_UNBAN = "✅ Débannir"
ADMIN_USER_BAN_REASON_PROMPT = "Entrez la raison du bannissement (ou envoyez « - » pour passer) :"
ADMIN_USER_BANNED_SUCCESS = "✅ Utilisateur {username} banni."
ADMIN_USER_UNBANNED_SUCCESS = "✅ Utilisateur {username} débanni."
ADMIN_USER_CANNOT_BAN_SELF = "❌ Vous ne pouvez pas vous bannir vous-même."
ADMIN_USER_CANNOT_BAN_ADMIN = "❌ Impossible de bannir un administrateur."
ADMIN_USER_ALREADY_BANNED = "❌ Cet utilisateur est déjà banni."
ADMIN_USER_NOT_BANNED = "❌ Cet utilisateur n'est pas banni."

# Statistics
ADMIN_PANEL_STATS = "📊 Statistiques d'utilisation"
ADMIN_STATS_TITLE = "📊 Statistiques d'utilisation"
ADMIN_STATS_USERS = "👥 Utilisateurs inscrits : {count}"
ADMIN_STATS_LISTINGS = "📋 Annonces totales : {count}"
ADMIN_STATS_SOLD = "💰 Annonces vendues : {count}"

# Expiry
ADMIN_EXPIRY_TITLE = "⏰ Annonces expirées"
ADMIN_EXPIRY_RESULT = "✅ {count} annonce(s) expirée(s) automatiquement."
ADMIN_EXPIRY_NONE = "Aucune annonce à expirer."
ADMIN_EXPIRY_NOTIFICATION = (
    "⏰ Annonce expirée\n\n📖 {title}\n💰 {price} ₽\n\nVotre annonce a automatiquement expiré."
)

# Admin navigation
ADMIN_BTN_BACK_PANEL = "⬅️ Retour au panneau"
ADMIN_BTN_BACK_YEARS = "⬅️ Retour aux années"
ADMIN_BTN_BACK_USERS = "⬅️ Retour aux utilisateurs"
