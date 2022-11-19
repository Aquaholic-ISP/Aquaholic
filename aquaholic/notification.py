import requests
from decouple import config
from json import JSONDecodeError


def get_access_token(code):
    api_url = "https://notify-bot.line.me/oauth/token"
    content_type = "application/x-www-form-urlencoded"

    grant_type = "authorization_code"
    code = code
    redirect_uri = config('REDIRECT_URI_NOTIFY')
    client_id = config('CLIENT_ID_NOTIFY')
    client_secret = config('CLIENT_SECRET_NOTIFY')
    headers = {'Content-Type': content_type}
    data = {
        "grant_type": grant_type,
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    r = requests.post(api_url, headers=headers, data=data)
    try:
        return r.json()['access_token']
    except JSONDecodeError:
        return None


def send_notification(message, token):
    url = 'https://notify-api.line.me/api/notify'
    token = token
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer ' + token}

    r = requests.post(url, headers=headers, data={'message': message})
    return r.json()['status']
