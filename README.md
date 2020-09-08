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
# export environment variables
yarn dotenv 

# start server
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