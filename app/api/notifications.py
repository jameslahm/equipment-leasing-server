from flask import request,jsonify
from . import api
from ..models import User,ApplicationType,LenderApplication,EquipmentPutOnApplication,EquipmentBorrowApplication,Notification
import json

@api.route('/notifications/<int:id>',methods=['PUT','DELETE'])
def operate_notification(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        if request.method =='PUT':
            item = Notification.update_notification(id,user,request.json)
            if item is not None:
                return jsonify(item.to_json()),200
            return jsonify({'error':'no such notification'}),400
        if request.method == 'DELETE':
            item = Notification.delete_notification(id,user)
            if item is not None:
                return jsonify(item),200
            return jsonify({'error':'no such notification'}),400
    return jsonify({'error':'invalid token'}),401

@api.route('/notifications',methods=['GET'])
def get_notifications():
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        items,total = Notification.get_notification(user,request.args)
        if items is not None:
            return jsonify({
                'notifications':[x.to_json() for x in items],
                'total':total
                }),200
        else:
            return jsonify({'error':'no such notification'}),400
    return jsonify({'error':'invalid token'}),401
