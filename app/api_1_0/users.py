from flask import Blueprint,Response,render_template,jsonify
from flask import request,abort,make_response
from flask import json, current_app
from flask.helpers import flash, url_for
from flask_mail import Mail, Message
from ..models import User
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
    msg.html = render_template(template + '.txt',token=token)
    thr = Thread(target=send_async_email,args=[app,msg])
    thr.start()
    return thr
    
@api.route('/register',methods=['POST'])
def register():
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first()
    if user is not None:
        return Response(jsonify({'error':'this email has been registered'}),400)
    else:
        user = User.query.filter_by(username=username).first()
        if user is not None:
            return Response(jsonify({'error':'this username has been registered'}),400)
        user = User(email = email,username = username,password = password)
        jwt = user.generate_auth_token(expiration=86400*365)
        User_uncomfirmed=user.to_json()
        User_uncomfirmed['confirm_token']=jwt
        db.session.add(user)
        db.session.commit()
        send_mail(email,'确认你的账户','/confirm',jwt)
        return Response(jsonify(User_uncomfirmed))

