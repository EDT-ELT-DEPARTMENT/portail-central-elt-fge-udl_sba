import streamlit as st
from supabase import create_client
from auth import (
    get_config, get_or_create_clients, sign_in, sign_up, sign_out,
    load_profile, list_user_access, is_admin, admin_list_profiles,
    admin_update_profile, admin_save_access,
)
from sso import issue_sso_code, APP_CATALOG, build_sso_url

st.set_page_config(
    page_title="Portail central ELT",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
.block-container {padding-top: 2rem; max-width: 1180px;}
.hero {
  padding: 2rem 2.2rem; border-radius: 18px;
  background: linear-gradient(120deg,#102a43,#176b87);
  color: white; margin-bottom: 1.4rem;
}
.hero h1 {color:white; margin-bottom:.3rem;}
.hero p {color:#e5f3f8; font-size:1.05rem;}
.app-card {
  border: 1px solid rgba(120,140,160,.28);
  border-radius: 15px; padding: 1.15rem; min-height: 175px;
}
.small-muted {color: #73808c; font-size:.9rem;}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <h1>⚡ Portail central ELT</h1>
  <p>Faculté de génie électrique · Université Djillali Liabès de Sidi Bel Abbès</p>
  <p>Un point d'accès central aux plateformes pédagogiques et administratives.</p>
</div>
""", unsafe_allow_html=True)

try:
    cfg = get_config()
    if not cfg["url"] or not cfg["anon_key"]:
        st.error("Configuration incomplète : ajoutez SUPABASE_URL et SUPABASE_ANON_KEY dans les secrets Streamlit.")
        st.stop()
    if not cfg["service_key"]:
        st.error("SUPABASE_SERVICE_ROLE_KEY est nécessaire côté serveur pour créer les codes SSO et administrer les accès.")
        st.stop()
    auth_client, service_client = get_or_create_clients(cfg)
except Exception as exc:
    st.error(f"Initialisation impossible : {exc}")
    st.stop()

if "portal_user" not in st.session_state:
    st.session_state.portal_user = None
if "portal_profile" not in st.session_state:
    st.session_state.portal_profile = None

def refresh_profile():
    user = st.session_state.get("portal_user")
    if not user:
        return None
    profile = load_profile(auth_client, user["id"])
    st.session_state.portal_profile = profile
    return profile

# Réauthentification de la session Streamlit courante si l'objet client existe.
if st.session_state.portal_user:
    try:
        current = auth_client.auth.get_user()
        if current and current.user:
            st.session_state.portal_user = {
                "id": current.user.id,
                "email": current.user.email,
            }
        else:
            st.session_state.portal_user = None
            st.session_state.portal_profile = None
    except Exception:
        st.session_state.portal_user = None
        st.session_state.portal_profile = None

if not st.session_state.portal_user:
    tab_login, tab_signup = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
    with tab_login:
        with st.form("portal_login_form"):
            email = st.text_input("Adresse e-mail")
            password = st.text_input("Mot de passe", type="password")
            submitted = st.form_submit_button("Se connecter", use_container_width=True)
        if submitted:
            try:
                user = sign_in(auth_client, email, password)
                st.session_state.portal_user = user
                profile = load_profile(auth_client, user["id"])
                st.session_state.portal_profile = profile
                st.rerun()
            except Exception as exc:
                st.error(f"Connexion refusée : {exc}")
    with tab_signup:
        st.info("La création d'un compte ne donne pas automatiquement accès aux applications. L'administration doit activer les autorisations.")
        with st.form("portal_signup_form"):
            full_name = st.text_input("Nom et prénom")
            new_email = st.text_input("Adresse e-mail", key="signup_email")
            new_password = st.text_input("Mot de passe", type="password", key="signup_password")
            confirm = st.text_input("Confirmer le mot de passe", type="password")
            created = st.form_submit_button("Créer mon compte", use_container_width=True)
        if created:
            if not full_name.strip() or not new_email.strip() or not new_password:
                st.warning("Veuillez remplir tous les champs.")
            elif new_password != confirm:
                st.error("Les deux mots de passe ne correspondent pas.")
            elif len(new_password) < 10:
                st.error("Choisissez un mot de passe d'au moins 10 caractères.")
            else:
                try:
                    sign_up(auth_client, new_email.strip(), new_password, full_name.strip())
                    st.success("Compte créé. Si Supabase exige une confirmation par e-mail, confirmez votre adresse puis connectez-vous.")
                except Exception as exc:
                    st.error(f"Création impossible : {exc}")
    st.stop()

profile = st.session_state.portal_profile or refresh_profile()
if not profile:
    st.error("Votre profil central n'existe pas encore. Contactez l'administrateur.")
    if st.button("Se déconnecter"):
        sign_out(auth_client)
        st.session_state.portal_user = None
        st.rerun()
    st.stop()

if not profile.get("is_active", False):
    st.warning("Votre compte est désactivé ou en attente d'activation. Contactez l'administration.")
    if st.button("Se déconnecter"):
        sign_out(auth_client)
        st.session_state.portal_user = None
        st.session_state.portal_profile = None
        st.rerun()
    st.stop()

with st.sidebar:
    st.markdown("### 👤 Mon compte")
    st.write(profile.get("full_name") or st.session_state.portal_user.get("email"))
    st.caption(st.session_state.portal_user.get("email"))
    st.caption(f"Rôle : {profile.get('role', 'non défini')}")
    if st.button("Se déconnecter", use_container_width=True):
        sign_out(auth_client)
        st.session_state.portal_user = None
        st.session_state.portal_profile = None
        st.rerun()

st.subheader("Mes plateformes")
st.write("Sélectionnez une plateforme à laquelle votre compte est autorisé à accéder.")

try:
    allowed = list_user_access(auth_client, st.session_state.portal_user["id"])
except Exception as exc:
    st.error(f"Impossible de lire vos autorisations : {exc}")
    allowed = []

access_map = {item["app_key"]: item for item in allowed if item.get("enabled")}
cols = st.columns(3)
for col, app_key in zip(cols, ("edt", "hsup", "stages")):
    app = APP_CATALOG[app_key]
    with col:
        st.markdown('<div class="app-card">', unsafe_allow_html=True)
        st.markdown(f"### {app['icon']} {app['title']}")
        st.write(app["description"])
        if app_key in access_map:
            if st.button(f"Préparer l'accès à {app['short']}", key=f"open_{app_key}", use_container_width=True):
                try:
                    code = issue_sso_code(service_client, st.session_state.portal_user["id"], app_key)
                    st.session_state[f"sso_url_{app_key}"] = build_sso_url(app["url"], code)
                except Exception as exc:
                    st.error(f"Impossible de préparer l'accès : {exc}")
            target = st.session_state.get(f"sso_url_{app_key}")
            if target:
                st.link_button("Ouvrir la plateforme", target, use_container_width=True)
                st.caption("Lien temporaire à usage unique. Préparez un nouveau lien si celui-ci expire.")
        else:
            st.button("Accès non autorisé", key=f"disabled_{app_key}", disabled=True, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

st.caption("Les liens SSO ne fonctionneront qu'après l'installation du module de vérification dans chaque application.")

if is_admin(profile):
    st.divider()
    st.header("🛡️ Administration du portail")
    st.warning("Attribuez uniquement les rôles et accès correspondant aux fonctions réelles de chaque personne.")
    try:
        users = admin_list_profiles(service_client)
    except Exception as exc:
        st.error(f"Lecture des comptes impossible : {exc}")
        users = []

    if users:
        choices = {f"{u.get('email','')} — {u.get('full_name','')} ({u.get('role','')})": u for u in users}
        selected_label = st.selectbox("Choisir un compte", list(choices.keys()))
        selected_user = choices[selected_label]
        with st.form("admin_profile_form"):
            role_options = ["admin", "personnel", "enseignant", "etudiant"]
            role = st.selectbox("Rôle central", role_options, index=role_options.index(selected_user.get("role", "etudiant")))
            active = st.checkbox("Compte actif", value=bool(selected_user.get("is_active", True)))
            save_profile = st.form_submit_button("Enregistrer le profil")
        if save_profile:
            try:
                admin_update_profile(service_client, selected_user["id"], role, active)
                st.success("Profil mis à jour.")
                st.rerun()
            except Exception as exc:
                st.error(f"Modification impossible : {exc}")

        st.markdown("#### Autorisations par plateforme")
        current_access = {
            x["app_key"]: bool(x["enabled"])
            for x in service_client.table("portal_app_access").select("app_key,enabled").eq("user_id", selected_user["id"]).execute().data
        }
        with st.form("admin_access_form"):
            allow_edt = st.checkbox("Plateforme EDT", value=current_access.get("edt", False))
            allow_hsup = st.checkbox("Plateforme H.SUP", value=current_access.get("hsup", False))
            allow_stages = st.checkbox("Plateforme Stages", value=current_access.get("stages", False))
            save_access = st.form_submit_button("Enregistrer les autorisations")
        if save_access:
            try:
                admin_save_access(service_client, selected_user["id"], {
                    "edt": allow_edt, "hsup": allow_hsup, "stages": allow_stages
                })
                st.success("Autorisations mises à jour.")
                st.rerun()
            except Exception as exc:
                st.error(f"Enregistrement impossible : {exc}")
    else:
        st.info("Aucun profil trouvé.")
