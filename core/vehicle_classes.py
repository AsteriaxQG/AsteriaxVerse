"""Readable Star Citizen vehicle classes used throughout the interface.

Fighter subclasses follow the current Star Citizen Wiki taxonomy. Other
vehicles are classified from the role flags, landing-pad size and cargo
capacity already present in the UEX catalogue.
"""

from __future__ import annotations

from typing import Any, Mapping


SNUB_FIGHTERS = {
    "fury",
    "fury mx",
    "p-52 merlin",
    "p-72 archimedes",
}

LIGHT_FIGHTERS = {
    "125a",
    "300i",
    "325a",
    "350r",
    "arrow",
    "aurora mk i es",
    "aurora mk i ln",
    "aurora mk i lx",
    "aurora mk i mr",
    "aurora mk i se",
    "aurora mk ii",
    "avenger stalker",
    "avenger titan",
    "avenger warlock",
    "basher",
    "blade",
    "buccaneer",
    "gladius",
    "gladius valiant",
    "hawk",
    "khartu-al",
    "l-21 wolf",
    "l-22 alpha wolf",
    "m50",
    "mustang alpha",
    "mustang delta",
    "pitbull",
    "reliant kore",
    "reliant tana",
    "talon",
    "talon shrike",
}

MEDIUM_FIGHTERS = {
    "f7c hornet mk i",
    "f7c hornet mk ii",
    "f7c hornet wildfire mk i",
    "f7c-m super hornet mk i",
    "f7c-r hornet tracker mk i",
    "f7c-r hornet tracker mk ii",
    "f7c-s hornet ghost mk i",
    "f7c-s hornet ghost mk ii",
    "meteor",
    "sabre",
    "sabre comet",
    "sabre firebird",
    "sabre raven",
    "san tok.yāi",
    "san'tok.yāi",
    "scythe",
}

HEAVY_FIGHTERS = {
    "ares inferno starfighter",
    "ares ion starfighter",
    "f8c lightning",
    "glaive",
    "guardian",
    "guardian mx",
    "guardian qi",
    "hurricane",
    "scorpius",
    "scorpius antares",
    "shiv",
    "stinger",
    "vanguard harbinger",
    "vanguard hoplite",
    "vanguard sentinel",
    "vanguard warden",
}


VEHICLE_CLASS_OPTIONS = (
    "Chasseur parasite",
    "Chasseur léger",
    "Chasseur moyen",
    "Chasseur lourd",
    "Bombardier",
    "Combat léger",
    "Combat moyen",
    "Combat lourd",
    "Combat capital",
    "Transport de fret léger",
    "Transport de fret moyen",
    "Transport de fret lourd",
    "Transport de fret très lourd",
    "Transport léger",
    "Transport moyen",
    "Transport lourd",
    "Transport capital",
    "Exploration",
    "Minage",
    "Récupération",
    "Médical",
    "Course",
    "Ravitaillement",
    "Réparation",
    "Données",
    "Science",
    "Industriel",
    "Multirôle",
    "Véhicule de combat",
    "Véhicule de course",
    "Transport terrestre",
    "Véhicule industriel",
    "Véhicule utilitaire",
    "Vaisseau léger",
    "Vaisseau moyen",
    "Vaisseau lourd",
    "Vaisseau capital",
)


def _size_word(pad_type: Any) -> str:
    pad = str(pad_type or "").strip().upper()
    if pad in {"XS", "S"}:
        return "léger"
    if pad == "M":
        return "moyen"
    if pad == "L":
        return "lourd"
    if pad == "XL":
        return "capital"
    return ""


def _freight_class(capacity: Any) -> str:
    try:
        scu = float(capacity or 0)
    except (TypeError, ValueError):
        scu = 0.0
    if scu <= 48:
        return "Transport de fret léger"
    if scu <= 192:
        return "Transport de fret moyen"
    if scu <= 576:
        return "Transport de fret lourd"
    return "Transport de fret très lourd"


def vehicle_class_label(vehicle: Mapping[str, Any]) -> str:
    """Return one concise, non-overlapping class for a vehicle record."""

    name = str(vehicle.get("name") or "").strip().casefold()
    roles = str(vehicle.get("roles") or "").strip()
    role_tokens = {token.strip().casefold() for token in roles.split(",") if token.strip()}

    if bool(vehicle.get("is_ground_vehicle")):
        if "combat" in role_tokens:
            return "Véhicule de combat"
        if "course" in role_tokens:
            return "Véhicule de course"
        if "transport" in role_tokens:
            return "Transport terrestre"
        if "industriel" in role_tokens or "cargo" in role_tokens:
            return "Véhicule industriel"
        return "Véhicule utilitaire"

    if name in SNUB_FIGHTERS:
        return "Chasseur parasite"
    if name in LIGHT_FIGHTERS:
        return "Chasseur léger"
    if name in MEDIUM_FIGHTERS:
        return "Chasseur moyen"
    if name in HEAVY_FIGHTERS:
        return "Chasseur lourd"

    if "bombardier" in role_tokens:
        return "Bombardier"
    if "médical" in role_tokens:
        return "Médical"
    if "minage" in role_tokens:
        return "Minage"
    if "récupération" in role_tokens:
        return "Récupération"
    if "ravitaillement" in role_tokens:
        return "Ravitaillement"
    if "réparation" in role_tokens:
        return "Réparation"
    if "données" in role_tokens:
        return "Données"
    if "science" in role_tokens:
        return "Science"
    if "exploration" in role_tokens:
        return "Exploration"
    if "course" in role_tokens:
        return "Course"
    if "cargo" in role_tokens:
        return _freight_class(vehicle.get("scu"))
    if "transport" in role_tokens:
        size = _size_word(vehicle.get("pad_type"))
        return f"Transport {size}" if size else "Transport léger"
    if "combat" in role_tokens:
        size = _size_word(vehicle.get("pad_type"))
        return f"Combat {size}" if size else "Combat moyen"
    if "industriel" in role_tokens:
        return "Industriel"
    if "polyvalent" in role_tokens:
        return "Multirôle"

    size = _size_word(vehicle.get("pad_type"))
    return f"Vaisseau {size}" if size else "Multirôle"

