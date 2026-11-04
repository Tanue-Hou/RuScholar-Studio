"""
Discipline rules (PhD Thesis Butler polishing clusters) and PPL calibration.

Loaded lazily and once per process. Previously both backend/main.py and
services/diagnostic_service.py loaded these files into their own globals.
"""
import functools
import json
import logging
import os

from services.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_RULES = {
    "do_rules": [
        "Использовать безличные и неопределенно-личные конструкции",
        "Соблюдать строгую логическую последовательность (введение -> методы -> результаты)"
    ],
    "dont_rules": [
        "Использовать местоимения первого лица (я, мы)",
        "Использовать эмоционально-окрашенную лексику и метафоры",
        "Злоупотреблять пассивным залогом и длинными цепочками существительных"
    ]
}


def _load_json(path: str, what: str) -> dict:
    if not os.path.exists(path):
        logger.warning("%s not found at %s; using built-in defaults.", what, path)
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning("Failed to load %s from %s: %s", what, path, e)
        return {}


@functools.lru_cache(maxsize=1)
def get_rule_clusters() -> dict:
    return _load_json(settings.rules_path, "polishing rules").get("clusters", {})


@functools.lru_cache(maxsize=1)
def get_calibration_db() -> dict:
    return _load_json(settings.calibration_path, "calibration config")


def get_discipline_rules(discipline: str) -> dict:
    clusters = get_rule_clusters()
    rules = clusters.get(discipline, clusters.get("UNIVERSAL"))
    if not rules and clusters:
        rules = next(iter(clusters.values()), None)
    return rules or DEFAULT_RULES


def get_calibration(discipline: str) -> dict:
    db = get_calibration_db()
    return db.get(discipline, db.get("UNIVERSAL", {}))
