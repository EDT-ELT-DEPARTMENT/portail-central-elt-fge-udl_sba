PORTAIL CENTRAL ELT — PREMIER DÉPLOIEMENT

1) Créer un dépôt GitHub privé/public selon votre choix.
2) Envoyer tous les fichiers de ce dossier à la racine du dépôt.
3) Dans Supabase > SQL Editor, exécuter une seule fois :
   supabase_portal_setup.sql
4) Dans Streamlit Community Cloud, créer une application depuis ce dépôt,
   fichier principal : app.py.
5) Dans App settings > Secrets, ajouter :

SUPABASE_URL = "https://VOTRE-PROJET.supabase.co"
SUPABASE_ANON_KEY = "VOTRE_CLE_ANON_OU_PUBLISHABLE"
SUPABASE_SERVICE_ROLE_KEY = "VOTRE_CLE_SERVICE_ROLE"

6) Ouvrir le portail et créer votre compte avec votre adresse e-mail.
7) Dans Supabase > SQL Editor, remplacer l'adresse dans la dernière requête
   commentée du script SQL et exécuter l'UPDATE pour vous attribuer le rôle admin.
8) Recharger le portail. L'administration permettra d'activer les profils et
   d'attribuer les accès EDT, H.SUP et Stages.

IMPORTANT
- Ne jamais mettre la clé service_role dans GitHub, un fichier Python ou un
  navigateur. Elle doit rester dans Streamlit Secrets.
- Ne pas supprimer les anciennes tables des applications.
- Les boutons SSO du portail génèrent des codes, mais le SSO ne sera pleinement
  opérationnel qu'après ajout du vérificateur dans chaque application cible.
- Les applications ne sont pas encore modifiées dans cette première livraison.
- Le compte utilisateur doit être créé via Supabase Auth. Si la confirmation
  d'e-mail est activée dans Supabase, l'utilisateur doit confirmer son e-mail.
