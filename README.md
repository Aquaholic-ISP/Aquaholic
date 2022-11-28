# Aquaholic
[![codecov](https://codecov.io/gh/Aquaholic-ISP/Aquaholic/branch/main/graph/badge.svg?token=F228E2GSLW)](https://codecov.io/gh/Aquaholic-ISP/Aquaholic)
[![Unittest](https://github.com/Aquaholic-ISP/Aquaholic/actions/workflows/aquaholic-app.yml/badge.svg)](https://github.com/Aquaholic-ISP/Aquaholic/actions/workflows/aquaholic-app.yml)

## Description

An application for calculating the amount of water that a person should drink per day, 
and offering a notification to remind him/her to drink water in each hour of the day
according to the generated schedule.

## How to install and run
1. Clone the repository from github
```
git clone https://github.com/Aquaholic-ISP/Aquaholic.git
```
2. Move into the project directory
```
cd Aquaholic
```
3. Create virtual environment
```
python -m venv env
```
4. Start virtual environment in bash or zsh
```
. env/bin/activate
```
5. Install dependencies
```
pip install -r requirements.txt
```
6. Create .env file following what's written in sample.env
- For LINE Login, you can get CLIENT_ID, and CLIENT_SECRET from [LINE Developers Console](https://developers.line.biz/console/)
following step 3 in [LINE Developers Documentation](https://developers.line.biz/en/docs/line-login/getting-started/#step-3-check-the-channel-settings-and-enter-the-callback-url).
```
# Fill information for line login service
CLIENT_ID = line-login-client-id
CLIENT_SECRET = line-login-client-secret
```
- For LINE Notify, you can get CLIENT_ID_NOTIFY, and CLIENT_SECRET_NOTIFY from registering a service with
[LINE Notify](https://notify-bot.line.me/my/services/).
- For the REDIRECT_URI_NOTIFY, we suggest that you should use your_base_url + /noti/callback/ and
please make sure that it is the same as what you registered in 
[Managed Registered Services - LINE Notify](https://notify-bot.line.me/my/services/).


```
# Fill information for line notify service
REDIRECT_URI_NOTIFY = line-notify-callback-url
CLIENT_ID_NOTIFY = line-notify-client-id
CLIENT_SECRET_NOTIFY = line-notify-client-secret
```
7. Run migrations 
```
python manage.py migrate
```
8. Install data from data fixtures
```
python manage.py loaddata data/aquaholic.json data/users.json
```
9. Run crontab for local development 
```
python manage.py crontab add
```
10. Run server 
```
python manage.py runserver
```
11. Visit the following url
```
http://127.0.0.1:8000/aquaholic/
```

## How to run
1. When open new terminal
```
cd Aquaholic
```

2. Make sure to activate virtual environment 
```
. env/bin/activate
```
3. Run crontab for local development 
```
python manage.py crontab add
```
4. Run the below command
```
python manage.py runserver
```


## Crontab Note
To stop crontab when you're done using it, run the below command
```
python manage.py crontab remove
```


## Project Documents

All project documents are in the [Project Wiki](../../wiki/Home).

## The deployed url

https://aquaholicwebapp.pythonanywhere.com/aquaholic/

