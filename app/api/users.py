from flask import Blueprint,Response,render_template,jsonify,request
from flask import request,abort,make_response
from flask import json, current_app
from flask.helpers import flash, url_for
from flask_mail import Mail, Message
from ..models import User,Role
from . import api
from .. import db
from threading import Thread


def send_async_email(app,msg):
    mail=Mail(app)
    with app.app_context():
        mail.send(msg)

def send_mail(to,subject,template,token):
    app = current_app._get_current_object()
    msg = Message(current_app.config['FLASKY_MAIL_SUBJECT_PREFIX']+subject,sender=current_app.config['MAIL_USERNAME'],recipients=[to])
    print(template)
    msg.html = "<h3>请确认注册</h3><a href='http://127.0.0.1/confirm?confirm_token={token}'>http://127.0.0.1/confirm</a>"
    thr = Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr

@api.route('/login',methods=['POST'])
def login():
    data = request.json
    if data is None:
        return jsonify({"error":"bad request"}),400
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username = username).first()
    if user is not None and user.verify_password(password) :
        jwt = user.generate_auth_token(expiration=86400*365)
        user_confirmed = user.to_json()
        user_confirmed['token'] = jwt
        return jsonify(user_confirmed),200
    return jsonify({'error':"invalid username or password"}),401

@api.route('/register',methods=['POST'])
def register():
    print('enter')
    data=request.json
    if data is None:
        return jsonify({"error":"bad request"}),400
    email = data.get('email')
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(email=email).first()
    if user is not None:
        return jsonify({'error':'this email has been registered'})
    else:
        user = User.query.filter_by(username=username).first()
        if user is not None:
            return jsonify({'error':'this username has been registered'}),400
        print(username)
        print(email)
        print(password)
        user = User(email = email,username = username,password = password)
        print('exit')
        jwt = user.generate_auth_token(expiration=86400*365)
        User_uncomfirmed=user.to_json()
        User_uncomfirmed['confirm_token']=jwt
        db.session.add(user)
        db.session.commit()
        send_mail(email,'确认你的账户','/confirm',jwt)
        print(User_uncomfirmed)
        return jsonify(User_uncomfirmed)


