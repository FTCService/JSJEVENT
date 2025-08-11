import json
import os
import secrets
from django.conf import settings  # import settings here

TOKEN_FILE_PATH = os.path.join(os.path.dirname(__file__), "temp_tokens.json")

def generate_temp_token():
    return secrets.token_urlsafe(32)

def save_token(token, user_id):
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, "r") as f:
            data = json.load(f)
    else:
        data = {}
    data[token] = user_id
    with open(TOKEN_FILE_PATH, "w") as f:
        json.dump(data, f)

def get_user_id(token):
    if not os.path.exists(TOKEN_FILE_PATH):
        return None
    with open(TOKEN_FILE_PATH, "r") as f:
        data = json.load(f)
    return data.get(token)

def remove_token(token):
    if not os.path.exists(TOKEN_FILE_PATH):
        return
    with open(TOKEN_FILE_PATH, "r") as f:
        data = json.load(f)
    if token in data:
        del data[token]
    with open(TOKEN_FILE_PATH, "w") as f:
        json.dump(data, f)

# New helper function to generate login URL including user_type query param
def send_temp_login_link(temp_user):
    # Ensure your settings.py has SITE_URL defined, e.g. SITE_URL = "https://example.com"
    base_url = f"{settings.SITE_URL}/temp-login/{temp_user.token}/"
    login_url = f"{base_url}?type={temp_user.user_type}"
    return {
        "login_url": login_url
    }
