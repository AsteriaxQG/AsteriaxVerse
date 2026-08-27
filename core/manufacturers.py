"""Canonical, player-facing manufacturer names for Star Citizen vehicles."""

from __future__ import annotations

import html


# UEX often returns the legal company name while CIG presents the short brand
# beside a ship. Keeping the labels here makes filters, lists and detail pages
# agree, and also repairs HTML entities found in some source rows.
SOURCE_TO_BRAND = {
    "Aegis Dynamics": "Aegis",
    "Anvil Aerospace": "Anvil",
    "Aopoa": "Aopoa",
    "Argo Astronautics": "ARGO",
    "Banu Souli": "Banu",
    "Consolidated Outland": "CNOU",
    "Crusader Industries": "Crusader",
    "Drake Interplanetary": "Drake",
    "Esperia Incorporation": "Esperia",
    "Gatac Manufacture": "Gatac",
    "Grey&apos;s Market": "Grey's Market",
    "Grey's Market": "Grey's Market",
    "Greycat Industrial": "Greycat",
    "Kruger Intergalactic": "Kruger",
    "Mirai": "Mirai",
    "Musashi Industrial and Starflight Concern": "MISC",
    "Origin Jumpworks": "Origin",
    "Roberts Space Industries": "RSI",
    "Tumbril Land Systems": "Tumbril",
    "Vanduul Clans": "Vanduul",
}

NAME_PREFIX_TO_BRAND = {
    "aegis ": "Aegis",
    "anvil ": "Anvil",
    "aopoa ": "Aopoa",
    "argo ": "ARGO",
    "banu ": "Banu",
    "c.o. ": "CNOU",
    "cnou ": "CNOU",
    "crusader ": "Crusader",
    "drake ": "Drake",
    "esperia ": "Esperia",
    "gatac ": "Gatac",
    "grey's market ": "Grey's Market",
    "greycat ": "Greycat",
    "kruger ": "Kruger",
    "mirai ": "Mirai",
    "misc ": "MISC",
    "origin ": "Origin",
    "rsi ": "RSI",
    "tumbril ": "Tumbril",
    "vanduul ": "Vanduul",
}


# Explicit checks for recent or easily confused models, recouped against CIG's
# manufacturer schedules and official ship/Q&A pages.
OFFICIAL_VEHICLE_BRANDS = {
    "asgard": "Anvil",
    "paladin": "Anvil",
    "moth": "ARGO",
    "mdc": "Greycat",
    "mtc": "Greycat",
    "utv": "Greycat",
    "prowler utility": "Esperia",
    "stinger": "Esperia",
    "shiv": "Grey's Market",
    "l-21 wolf": "Kruger",
    "l-22 alpha wolf": "Kruger",
    "hull b": "MISC",
    "clipper": "Drake",
    "golem": "Drake",
    "golem ox": "Drake",
    "aurora mk ii": "RSI",
    "hermes": "RSI",
    "meteor": "RSI",
    "salvation": "RSI",
}


def vehicle_manufacturer_label(
    source: object,
    *,
    vehicle_name: object = "",
    name_full: object = "",
) -> str:
    """Return the canonical short brand shown to players."""

    name_key = str(vehicle_name or "").strip().casefold()
    if name_key in OFFICIAL_VEHICLE_BRANDS:
        return OFFICIAL_VEHICLE_BRANDS[name_key]

    full_name = html.unescape(str(name_full or "")).strip().casefold()
    for prefix, brand in NAME_PREFIX_TO_BRAND.items():
        if full_name.startswith(prefix):
            return brand

    raw = str(source or "").strip()
    decoded = html.unescape(raw)
    aliases = {key.casefold(): value for key, value in SOURCE_TO_BRAND.items()}
    return aliases.get(raw.casefold()) or aliases.get(decoded.casefold()) or decoded


def vehicle_manufacturer_sources(display_name: str) -> list[str]:
    """Return stored source values matching a canonical filter label."""

    target = str(display_name or "").strip().casefold()
    values = {str(display_name or "").strip()}
    for source, brand in SOURCE_TO_BRAND.items():
        if brand.casefold() == target:
            values.add(source)
            values.add(html.unescape(source))
    return sorted(value for value in values if value)


def official_vehicle_names(display_name: str) -> list[str]:
    """Return audited vehicle names belonging to a canonical brand."""

    target = str(display_name or "").strip().casefold()
    return sorted(name for name, brand in OFFICIAL_VEHICLE_BRANDS.items() if brand.casefold() == target)
