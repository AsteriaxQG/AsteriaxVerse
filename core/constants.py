"""Application-wide constants.

The program deliberately keeps data-source URLs in one place.  This makes the
attribution visible and lets future maintainers update an endpoint without
having to touch the UI or the database layer.
"""

from __future__ import annotations

APP_NAME = "Asteriax Verse"
APP_VERSION = "1.4.0"
APP_AUTHOR = "AsteriaxTTV"
USER_AGENT = f"AsteriaxTTV-StarCitizen-Companion/{APP_VERSION}"

APP_RELEASE_NOTES = (
    "Pagination fluide des grands catalogues au lieu de dessiner des milliers de lignes d’un coup.",
    "Recherches d’objets, de vaisseaux et de boutiques exécutées en arrière-plan.",
    "Cache SQLite accélérant les recherches répétées et nouveaux index de lecture.",
    "Mode performances et barre latérale automatiquement adaptée à la largeur de la fenêtre.",
)

DISCORD_URL = "https://discord.com/invite/YSK3aJwATH"
TWITCH_URL = "https://www.twitch.tv/asteriaxttv/about"

# Official AsteriaxTTV release channel. New executables are downloaded inside
# the application and installed only after their size and SHA-256 fingerprint
# match the values published by the GitHub build workflow.
APP_UPDATE_MANIFEST_URL = (
    "https://raw.githubusercontent.com/AsteriaxQG/AsteriaxVerse/"
    "main/UPDATE_MANIFEST.json"
)

UEX_API_BASE = "https://api.uexcorp.uk/2.0/"
UEX_SITE_URL = "https://uexcorp.space/"
UEX_API_DOCS_URL = "https://uexcorp.space/api/documentation/"

RSI_LIVE_PATCH_URL = (
    "https://robertsspaceindustries.com/en/comm-link/Patch-Notes/"
    "21293-Star-Citizen-Alpha-410"
)
RSI_PATCHES_URL = "https://robertsspaceindustries.com/en/comm-link"
RSI_STATUS_URL = "https://status.robertsspaceindustries.com/"
RSI_KNOWN_ISSUES_URL = "https://support.robertsspaceindustries.com/hc/en-us"
RSI_ROADMAP_URL = "https://robertsspaceindustries.com/roadmap/release-view"
WIKI_SHIPS_URL = "https://starcitizen.tools/Purchasing_ships"

# The bundled offline snapshot was checked against this official LIVE build.
VERIFIED_LIVE_VERSION = "4.10.0-LIVE.12519617"
VERIFIED_LIVE_DATE = "26 août 2026"

# UEX can publish the new LIVE version before its community-maintained ship-shop
# feed is populated. These narrow 4.10 supplements are taken from the official
# patch inventory and price checks made in game. They are only used for 4.10,
# only when the exact UEX offer is still absent, and disappear automatically as
# soon as the provider publishes the corresponding pair.
PATCH_410_RELEASE_TIMESTAMP = 1787702400
PATCH_410_VEHICLE_OFFERS: tuple[dict[str, object], ...] = (
    {"vehicle": "Aurora Mk II", "terminal": "New Deal - Teasa Spaceport - Lorville", "price": 904_932},
    {"vehicle": "Aurora Mk II", "terminal": "Teach's Ship Shop - Levski", "price": 952_560},
    {"vehicle": "Hull B", "terminal": "New Deal - Teasa Spaceport - Lorville", "price": 7_541_100},
    {"vehicle": "Hull B", "terminal": "Teach's Ship Shop - Levski", "price": 7_938_000},
    {"vehicle": "L-22 Alpha Wolf", "terminal": "Astro Armada - Area 18", "price": 4_536_000},
    {"vehicle": "Golem Ox", "terminal": "New Deal - Teasa Spaceport - Lorville", "price": 1_149_120},
    {"vehicle": "Golem Ox", "terminal": "Buy and Fly - Orbituary", "price": 1_209_600},
    {"vehicle": "Golem Ox", "terminal": "Buy and Fly - Checkmate", "price": 1_209_600},
    {"vehicle": "Golem Ox", "terminal": "Buy and Fly - Ruin Station", "price": 1_209_600},
    {"vehicle": "UTV", "terminal": "Astro Armada - Area 18", "price": 75_600},
    {"vehicle": "UTV", "terminal": "Buy and Fly - Orbituary", "price": 75_600},
    {"vehicle": "UTV", "terminal": "Buy and Fly - Checkmate", "price": 75_600},
    {"vehicle": "UTV", "terminal": "Buy and Fly - Ruin Station", "price": 75_600},
)

PATCH_410_CATALOGUE_HIGHLIGHTS: tuple[str, ...] = (
    "5 nouvelles ventes : Aurora Mk II, Hull B, L-22 Alpha Wolf, Golem OX et Greycat UTV.",
    "Modules cargo et missiles de l’Aurora Mk II ajoutés à plusieurs boutiques.",
    "Railguns et chargeurs balistiques Vendetta ajoutés à plusieurs inventaires.",
    "Armure lourde BUL-H4, casque, sac H4-PBF et mitrailleuse Vendetta via Wikelo / Siege of Orison.",
    "Fusil HDGW Arlington et optique associée ajoutés au jeu.",
    "Jump drives exposés chez Dumper’s Depot Area18 et cartes AR disponibles.",
    "Vêtements HDTC chez Makau et Aparelli, avec rééquilibrage des prix carburant et munitions de vaisseau.",
)

COLORS = {
    "background": "#070C12",
    "sidebar": "#0B121B",
    "panel": "#101923",
    "panel_alt": "#13202C",
    "panel_hover": "#182A38",
    "border": "#203342",
    "accent": "#35D0BA",
    "accent_hover": "#57E1CD",
    "accent_dark": "#103E3B",
    "blue": "#4FA8FF",
    "warning": "#F4C15D",
    "danger": "#FF6B7A",
    "text": "#F3F7FA",
    "muted": "#8FA3B4",
    "muted_2": "#627687",
    "success": "#68E0A5",
}

# High-level scopes used by the navigation.  The source categories stay in
# English because those values come directly from the game-data provider; all
# user-facing labels are French.
ITEM_SCOPES: dict[str, dict[str, object]] = {
    "ship_gear": {
        "label": "Équipement de vaisseau",
        "sections": ["Systems", "Avionics", "Propulsion", "Vehicle Weapons", "Utility"],
    },
    "personal_gear": {
        "label": "Équipement personnel",
        "sections": ["Armor", "Undersuits", "Clothing", "Personal Weapons"],
    },
    "all": {"label": "Tous les objets", "sections": []},
}

SECTION_TRANSLATIONS = {
    "Armor": "Armures",
    "Avionics": "Avionique",
    "Clothing": "Vêtements",
    "Commodities": "Marchandises",
    "Consumable": "Consommables",
    "Data": "Données",
    "Decorations": "Décorations",
    "Flair": "Flair",
    "Liveries": "Livrées",
    "Miscellaneous": "Divers",
    "Module": "Modules",
    "Other": "Autres",
    "Personal Weapons": "Armes personnelles",
    "Propulsion": "Propulsion",
    "Systems": "Systèmes",
    "Technology": "Technologie",
    "Undersuits": "Sous-combinaisons",
    "Utility": "Utilitaires",
    "Vehicle Weapons": "Armes de vaisseau",
    "Vehicles": "Véhicules",
}

CATEGORY_TRANSLATIONS = {
    "Arms": "Bras",
    "Attachments": "Accessoires",
    "Backpacks": "Sacs à dos",
    "Batteries": "Batteries",
    "Bomb Racks": "Râteliers à bombes",
    "Bombs": "Bombes",
    "Coolers": "Refroidisseurs",
    "External Fuel Tanks": "Réservoirs externes",
    "Flight Blade": "Lames de vol",
    "Full Set": "Ensembles complets",
    "Guns": "Canons",
    "Helmets": "Casques",
    "Jump Modules": "Modules de saut",
    "Legs": "Jambes",
    "Life Support Generator": "Générateurs de survie",
    "Mining Laser Heads": "Têtes laser de minage",
    "Mining Modules": "Modules de minage",
    "Missile Racks": "Râteliers à missiles",
    "Missiles": "Missiles",
    "Personal Weapons": "Armes personnelles",
    "Point Defense Cannon": "Canons de défense rapprochée",
    "Power Plants": "Centrales électriques",
    "Quantum Drives": "Propulseurs quantiques",
    "Radar": "Radars",
    "Salvage Beams": "Faisceaux de récupération",
    "Scraper Beams": "Faisceaux de raclage",
    "Shield Generators": "Générateurs de bouclier",
    "Torpedo Tubes": "Tubes lance-torpilles",
    "Torso": "Torse",
    "Tractor Beams": "Rayons tracteurs",
    "Turrets": "Tourelles",
    "Undersuits": "Sous-combinaisons",
    "Vehicles": "Véhicules",
}


def translate_section(value: str | None) -> str:
    """Return a friendly French section label."""

    if not value:
        return "—"
    return SECTION_TRANSLATIONS.get(value, value)


def translate_category(value: str | None) -> str:
    """Return a friendly French category label."""

    if not value:
        return "—"
    return CATEGORY_TRANSLATIONS.get(value, value)
