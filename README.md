[![codecov](https://codecov.io/gh/jameslahm/equipment-leasing-server/branch/master/graph/badge.svg?token=C6J7838S9J)](https://codecov.io/gh/jameslahm/equipment-leasing-server)
[![Build Status](https://travis-ci.com/jameslahm/equipment-leasing-server.svg?token=zMepxcNDKbRfwzCYs7iz&branch=master)](https://travis-ci.com/jameslahm/equipment-leasing-server)

## Install Vscode Extensions
```
pylance
```


## Switch to virtual environment
```bash
virtualenv venv
source venv/Script/activate
```

## Install Dependencies
```bash
yarn
```

```bash
pip install -r requirements.txt

pip install `your want to install`

pip freeze > requirements.txt
```

## Start Development
```bash
# start development server
flask run
```

## Play with Shell
```bash
flask shell
```

## Migrate Database
```bash
# Init Database
flask db init

flask db migrate -m "your comment"

flask db upgrade
```

## Commit Message
see https://www.conventionalcommits.org/en/v1.0.0/

see http://www.ruanyifeng.com/blog/2016/01/commit_message_change_log.html

## Other
flask-sqlalchemy-stubs==0.0.1