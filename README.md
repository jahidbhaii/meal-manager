
# Meal Manager — Online Ready

This version is designed for Streamlit Community Cloud + Supabase.

## What you get
- Shared live cloud database
- Daily meal +/- buttons
- Total bazar only
- All members' deposits in one screen
- Excel-style Preview
- Excel export
- Optional group password
- No local SQLite dependency

## 1) Create Supabase database
1. Create a Supabase project.
2. Open SQL Editor.
3. Paste everything from `schema.sql`.
4. Run it.

## 2) Put the app on GitHub
Upload:
- app.py
- requirements.txt
- schema.sql
- .streamlit/secrets.toml.example
- .gitignore
- README.md

IMPORTANT: Do not upload your real secrets.toml or service-role key.

## 3) Deploy on Streamlit Community Cloud
Create a new app from your GitHub repository.
Main file: `app.py`

Then open:
App -> Settings -> Secrets

Paste this, replacing the values:

SUPABASE_URL = "https://YOUR-PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR-SUPABASE-SERVICE-ROLE-KEY"
APP_PASSWORD = "YOUR-GROUP-PASSWORD"

Save. The app will restart.

## 4) Share the Streamlit URL
Streamlit will give you a public URL like:
https://your-app-name.streamlit.app

Anyone with the URL and group password can use the app.

## IMPORTANT SECURITY
The service-role key is powerful. It must remain only inside Streamlit Secrets.
Never put it in app.py, GitHub, screenshots, or messages.

## Changing members
For the first version, change members directly in Supabase:
Table Editor -> members.
You can add a new member with active = true.

## Future upgrade
If needed, this can later be upgraded to individual accounts, admin/member roles, monthly locking, edit history, and a custom domain.
