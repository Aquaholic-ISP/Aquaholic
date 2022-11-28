"""A module that keep methods related to line notification."""
import requests
from decouple import config


def get_access_token(code):
    """Generate access token from the given code."""
    api_url = "https://notify-bot.line.me/oauth/token"
    content_type = "application/x-www-form-urlencoded"

    grant_type = "authorization_code"
    redirect_uri = config('REDIRECT_URI_NOTIFY', default="line_callback_url")
    client_id = config('CLIENT_ID_NOTIFY', default="line_notify_client_id")
    client_secret = config('CLIENT_SECRET_NOTIFY', default="line_notify_client_id")
    headers = {'Content-Type': content_type}
    data = {
        "grant_type": grant_type,
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    response = requests.post(api_url, headers=headers, data=data)
    return response.json()['access_token']


def send_notification(message, token):
    """Send notification from message anf token provided."""
    url = 'https://notify-api.line.me/api/notify'
    if not token:
        return None
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer ' + token}

    response = requests.post(url, headers=headers, data={'message': message})
    return response.json()['status']


def check_token_status(token):
    """Check the token status (200 == valid)."""
    url = "https://notify-api.line.me/api/status"
    if not token:
        return 0
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer ' + token}
    response = requests.get(url, headers=headers)
    return response.json()['status']
