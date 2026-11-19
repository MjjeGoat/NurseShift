import logging
from typing import Any, Dict

from app.db import get_db

logger = logging.getLogger("nurseshift.seed")

SEED_USERS: Dict[str, Dict[str, Any]] = {
    "user_admin": {
        "name": "Ing. Martin Svoboda",
        "email": "martin.svoboda@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000001",
        "role": "admin",
        "workload": 1.0,
        "active": True,
    },
    "user_head": {
        "name": "Mgr. Eva Dvořáková",
        "email": "eva.dvorakova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000002",
        "role": "head_nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_1": {
        "name": "Bc. Jana Nováková",
        "email": "jana.novakova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000003",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_2": {
        "name": "Bc. Petra Černá",
        "email": "petra.cerna@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000004",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_3": {
        "name": "Lucie Procházková",
        "email": "lucie.prochazkova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000005",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_4": {
        "name": "Bc. Klára Veselá",
        "email": "klara.vesela@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000006",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_5": {
        "name": "Mgr. Tereza Horáková",
        "email": "tereza.horakova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000007",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_6": {
        "name": "Hana Němcová",
        "email": "hana.nemcova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000008",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_7": {
        "name": "Bc. Veronika Králová",
        "email": "veronika.kralova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000009",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_8": {
        "name": "Markéta Benešová",
        "email": "marketa.benesova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000010",
        "role": "nurse",
        "workload": 0.75,
        "active": True,
    },
    "user_9": {
        "name": "Bc. Alena Pokorná",
        "email": "alena.pokorna@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000011",
        "role": "nurse",
        "workload": 1.0,
        "active": True,
    },
    "user_10": {
        "name": "Simona Růžičková",
        "email": "simona.ruzickova@nemocnice.cz",
        "microsoft_oid": "00000000-0000-0000-0000-000000000012",
        "role": "nurse",
        "workload": 0.5,
        "active": True,
    },
}

SEED_DEPARTMENT_CONFIG: Dict[str, Any] = {
    "shift_duration_hours": 12,
    "min_staff_day": 3,
    "min_staff_night": 2,
    "weekly_hours_full_workload": 37.5,
    "rules_config": {
        "prevent_night_to_day": True,
        "max_consecutive_shifts": 3,
    },
}

SEED_SCHEDULE_2026_11: Dict[str, Any] = {
    "year": 2026,
    "month": 11,
    "status": "draft",
    "shifts": {
        "2026-11-01": {
            "day": ["user_1", "user_2", "user_3"],
            "night": ["user_4", "user_5"],
            "vacation": ["user_6"],
        },
        "2026-11-02": {
            "day": ["user_1", "user_2", "user_7"],
            "night": ["user_4", "user_8"],
            "vacation": ["user_6"],
        },
        "2026-11-03": {
            "day": ["user_3", "user_5", "user_9"],
            "night": ["user_7", "user_10"],
            "vacation": [],
        },
    },
}


def seed_database(force: bool = False) -> Dict[str, Any]:
    """Seed initial hospital users, department settings and demo schedule."""
    db = get_db()

    settings_doc = db.collection("settings").document("department_config").get()
    if settings_doc.exists and not force:
        logger.info("Database already contains department_config, skipping seed.")
        return {"seeded": False, "reason": "already_initialized"}

    for user_id, user_data in SEED_USERS.items():
        db.collection("users").document(user_id).set(user_data)

    db.collection("settings").document("department_config").set(SEED_DEPARTMENT_CONFIG)

    db.collection("schedules").document("2026-11").set(SEED_SCHEDULE_2026_11)

    logger.info("Successfully seeded Firestore database with test data.")
    return {
        "seeded": True,
        "counts": {
            "users": len(SEED_USERS),
            "settings": 1,
            "schedules": 1,
        },
    }
