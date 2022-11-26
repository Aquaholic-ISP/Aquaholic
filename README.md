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
7. Run migrations 
```
python manage.py migrate
```
8. Install data from data fixtures
```
python manage.py loaddata data/aquaholic.json data/users.json
```
9. Run the below command
```
python manage.py runserver
```
10. Visit the following url
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

2. Run the below command
```
python manage.py runserver
```

## Project Documents

All project documents are in the [Project Wiki](../../wiki/Home).