import requests


def get_access_token(code):
    api_url = "https://notify-bot.line.me/oauth/token"
    content_type = "application/x-www-form-urlencoded"

    grant_type = "authorization_code"
    code = code
    redirect_uri = "http://127.0.0.1:8000/noti/callback/"
    client_id = "fVKMI2Q1k3MY5D3w2g0Hwt"
    client_secret = "7YdamNWV5MXvuH6pwGIHkYGHjLvC0xlcKYtw1OXjzVk"
    headers = {'Content-Type': content_type}
    data = {
        "grant_type": grant_type,
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret
    }
    r = requests.post(api_url, headers=headers, data=data)
    return r.json()['access_token']


def send_notification(message, token):
    url = 'https://notify-api.line.me/api/notify'
    token = token
    headers = {'content-type': 'application/x-www-form-urlencoded',
               'Authorization': 'Bearer ' + token}

    r = requests.post(url, headers=headers, data={'message': message})
    return r.json()['status']
