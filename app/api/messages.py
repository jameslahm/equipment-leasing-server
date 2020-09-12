from email import message
from flask import jsonify,request
from ..models import Message,User
from . import api
from .. import db
from datetime import datetime
from sqlalchemy import and_

@api.route('/messages',methods=['GET'])
def get_unread_senders():
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        senders = Message.get_unread_senders(user)
        return jsonify(senders),200
    return jsonify({'error': 'invalid token'}), 401    

@api.route('/messages/:id',methods=['GET'])
def get_messages(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        messages = Message.get_messages(user,id)
        return jsonify([message.to_json() for message in messages]),200
    return jsonify({'error': 'invalid token'}), 401    

@api.route('/messages/:id',methods=['POST'])
def add_message(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        body = request.json
        body['sender_id'] = user.id
        body['receiver_id'] = id
        message = Message.insert_message(user,body)
        if message is not None:
            return jsonify(message.to_json()),200
        else:
            return jsonify({'error':'insert error'}),404            
    return jsonify({'error': 'invalid token'}), 401    

@api.route('/messages/:id',methods=['PUT'])
def update_message(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        messages = Message.query.filter_by(sender_id=id,receiver_id=user.id,isRead=False).all()
        for message in messages:
            message.isRead = True
        db.session.commit()
        return jsonify([message.to_json() for message in messages]),200
    return jsonify({'error': 'invalid token'}), 401    
