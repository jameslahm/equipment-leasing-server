from flask import request, jsonify
from . import api
from ..models import User, Notification


@api.route('/notifications/<int:id>', methods=['PUT', 'DELETE'])
def operate_notification(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        if request.method == 'PUT':
            item = Notification.update_notification(id, user, request.json)
            if item is not None:
                return jsonify(item), 200
            return jsonify({'error': 'no such notification'}), 404
        if request.method == 'DELETE':
            item = Notification.delete_notification(id, user)
            if item is not None:
                return jsonify(item), 200
            return jsonify({'error': 'no such notification'}), 404
    return jsonify({'error': 'invalid token'}), 401


@api.route('/notifications/<int:id>', methods=['GET'])
def get_notification(id):
    user = User.verify_auth_token(request.headers.get("Authorization"))
    if user:
        notification = Notification.query.filter_by(id=id).first()
        if notification is not None and notification.receiver_id==user.id:
            return jsonify(notification.to_json()), 200
        return jsonify({'error': 'no such notification'}), 404


@api.route('/notifications', methods=['GET'])
def get_notifications():
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        items, total = Notification.get_notification(user, request.args)
        if items is not None:
            return jsonify({
                'notifications': [x.to_json() for x in items],
                'total': total
            }), 200
        else:
            return jsonify({'error': 'no such notification'}), 404
    return jsonify({'error': 'invalid token'}), 401
