from datetime import datetime
from flask import jsonify, request
from flask import current_app
from flask_mail import Mail, Message
from ..models import SystemLogContent,User,SystemLog
from . import api
from .. import db
from threading import Thread


def send_async_email(app, msg):
    mail = Mail(app)
    with app.app_context():
        mail.send(msg)


def send_mail(to, subject, template, token):
    app = current_app._get_current_object()
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX']+": "+subject,
                  sender=current_app.config['MAIL_USERNAME'], recipients=[to])
    msg.html = "<h3>Please click the link below to confirm your account </h3><a href='https://equipment-leasing-web.vercel.app/users/confirm?confirm_token={}'>https://equipment-leasing-web.vercel.app/users/confirm?confirm_token={}</a>".format(
        token, token)
    thr = Thread(target=send_async_email, args=[app, msg])
    thr.start()
    return thr


@api.route('/login', methods=['POST'])
def login():
    data = request.json
    if data is None:
        return jsonify({"error": "bad request"}), 400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user is not None and user.verify_password(password):
        jwt = user.generate_auth_token(expiration=86400*365)
        user_confirmed = user.to_json()
        user_confirmed['token'] = jwt
        return jsonify(user_confirmed), 200
    return jsonify({'error': "invalid username or password"}), 401


@api.route('/register', methods=['POST'])
def register():
    data = request.json
    if data is None:
        return jsonify({"error": "bad request"}), 400
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    print(user)
    if user is not None:
        return jsonify({'error': 'this email has been registered'}),400
    else:
        user = User.query.filter_by(username=username).first()
        print(user)
        if user is not None:
            return jsonify({'error': 'this username has been registered'}), 400
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        jwt = user.generate_auth_token(expiration=86400*365)
        user_uncomfirmed = user.to_json()
        user_uncomfirmed['confirm_token'] = jwt
        send_mail(email, 'Activate your account', '/confirm', jwt)
        return jsonify(user_uncomfirmed)


@api.route('/users/confirm', methods=['POST'])
def confirm():
    user = User.verify_auth_token(request.headers.get("Authorization"))
    if user:
        user = User.update_userinfo(
            user.id, User.get_admin(), {'confirmed': True})
        jwt = user.generate_auth_token(expiration=86400*365)
        user_comfirmed = user.to_json()
        user_comfirmed['token'] = jwt
        log = SystemLog(content="new user register id={}".format(user.id),type='insert',log_time=datetime.now())
        db.session.add(log)
        db.session.commit()
        return jsonify(user_comfirmed), 200
    return jsonify({'error': 'bad request'}), 400


@api.route('/users', methods=['GET'])
def get_users():
    Users = dict()
    if User.verify_auth_token(request.headers.get('Authorization')):
        users, total = User.search_byusername(request.args)
        users = [x.to_json() for x in users]
        Users['total'] = total
        Users['users'] = users
        return jsonify(Users), 200
    return jsonify({'error': 'invalid token'}), 401


@api.route('/users/<int:id>', methods=['GET', 'PUT', 'DELETE'])
def operate_user(id):
    operator = User.verify_auth_token(request.headers.get("Authorization"))
    if not operator:
        return jsonify({'error': 'invalid token'}), 401
    if request.method == 'GET':
        user = User.query.filter_by(id=id).first()
        if user:
            return jsonify(user.to_json()), 200
        else:
            return jsonify({"error":"no such user"}),404
    if request.method == 'PUT':
        data = request.json
        user = User.update_userinfo(id, operator, data)
        if user is not None:
            log = SystemLog(content=SystemLogContent.UPDATE_LOG.format(
                username = operator.username,id = operator.id,
                role = operator.role.name, item =" User's info",
                item_id = user.id
            ),type='update',log_time=datetime.now())
            db.session.add(log)
            db.session.commit()
            return jsonify(user.to_json()), 200
        return jsonify({'error': 'illegal params'}), 400
    if request.method == 'DELETE':
        user = User.delete_user(id, operator)
        if user is not None:
            log = SystemLog(content=SystemLogContent.DELETE_LOG.format(
                username = operator.username,id = operator.id,
                role = operator.role.name, item =" User",
                item_id = user["id"]
            ),type='delete',log_time=datetime.now())
            db.session.add(log)
            db.session.commit()
            return jsonify(user), 200
        return jsonify({'error': 'no permission'}), 401
