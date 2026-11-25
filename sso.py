from urllib.parse import urlencode
from datetime import datetime, timezone

APP_CATALOG = {
    "edt": {
        "short": "EDT",
        "icon": "📅",
        "title": "Gestion des emplois du temps",
        "description": "Emplois du temps, espaces enseignants, étudiants et administration.",
        "url": "https://edt-udl-2026-e7fwknwxqkxsyfstwcuq4n.streamlit.app/",
    },
    "hsup": {
        "short": "H.SUP",
        "icon": "⚡",
        "title": "Gestion des heures supplémentaires",
        "description": "EDT des enseignants et états des heures supplémentaires.",
        "url": "https://gestion-des-heures-suppl-mentaires-vacataires-j8wt9uxtmewa5gxd.streamlit.app/",
    },
    "stages": {
        "short": "Stages",
        "icon": "🎓",
        "title": "Stages professionnels",
        "description": "Demandes de stages, suivi et traitement administratif.",
        "url": "https://stages-professionnelsfge-2026-2027-fc2yjvjzhxr2pwrpdrgmww.streamlit.app/",
    },
}

def issue_sso_code(service_client, user_id, app_key):
    if app_key not in APP_CATALOG:
        raise ValueError("Application inconnue.")
    result = service_client.rpc("portal_issue_sso_code", {
        "p_user_id": user_id,
        "p_app_key": app_key,
    }).execute()
    if not result.data:
        raise RuntimeError("Aucun code SSO n'a été généré.")
    return str(result.data)

def build_sso_url(base_url, code):
    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}{urlencode({'sso': code})}"

def consume_sso_code(service_client, code, app_key):
    """À appeler côté serveur dans chaque application cible. Le code est consommé une seule fois."""
    if not code or app_key not in APP_CATALOG:
        return None
    result = service_client.rpc("portal_consume_sso_code", {
        "p_code": code,
        "p_app_key": app_key,
    }).execute()
    return result.data
