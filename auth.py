import streamlit as st
from supabase import create_client

def get_config():
    return {
        "url": str(st.secrets.get("SUPABASE_URL", "")).strip().rstrip("/"),
        "anon_key": str(st.secrets.get("SUPABASE_ANON_KEY", "") or st.secrets.get("SUPABASE_KEY", "")).strip(),
        "service_key": str(st.secrets.get("SUPABASE_SERVICE_ROLE_KEY", "")).strip(),
    }

def get_or_create_clients(cfg):
    if "_portal_auth_client" not in st.session_state:
        st.session_state["_portal_auth_client"] = create_client(cfg["url"], cfg["anon_key"])
    if "_portal_service_client" not in st.session_state:
        st.session_state["_portal_service_client"] = create_client(cfg["url"], cfg["service_key"])
    return st.session_state["_portal_auth_client"], st.session_state["_portal_service_client"]

def sign_in(client, email, password):
    result = client.auth.sign_in_with_password({"email": email.strip(), "password": password})
    if not result.user:
        raise RuntimeError("Utilisateur non retourné par Supabase.")
    return {"id": result.user.id, "email": result.user.email}

def sign_up(client, email, password, full_name):
    return client.auth.sign_up({
        "email": email,
        "password": password,
        "options": {"data": {"full_name": full_name}},
    })

def sign_out(client):
    try:
        client.auth.sign_out()
    except Exception:
        pass

def load_profile(client, user_id):
    result = client.table("portal_profiles").select(
        "id,email,full_name,role,is_active"
    ).eq("id", user_id).maybe_single().execute()
    return result.data

def list_user_access(client, user_id):
    result = client.table("portal_app_access").select(
        "app_key,enabled"
    ).eq("user_id", user_id).eq("enabled", True).execute()
    return result.data or []

def is_admin(profile):
    return bool(profile and profile.get("role") == "admin" and profile.get("is_active"))

def admin_list_profiles(service_client):
    result = service_client.table("portal_profiles").select(
        "id,email,full_name,role,is_active,created_at"
    ).order("created_at", desc=True).execute()
    return result.data or []

def admin_update_profile(service_client, user_id, role, is_active):
    service_client.table("portal_profiles").update({
        "role": role, "is_active": bool(is_active)
    }).eq("id", user_id).execute()

def admin_save_access(service_client, user_id, access):
    for app_key, enabled in access.items():
        service_client.table("portal_app_access").upsert({
            "user_id": user_id,
            "app_key": app_key,
            "enabled": bool(enabled),
        }, on_conflict="user_id,app_key").execute()
