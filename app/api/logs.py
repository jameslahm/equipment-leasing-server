from flask import jsonify, request
from ..models import SystemLog, User
from . import api


@api.route('/logs', methods=['GET'])
def get_logs():
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user and user.role.name == 'admin':
        items, total = SystemLog.get_logs(user, request.args)
        if items is not None:
            return jsonify({
                'logs': [x.to_json() for x in items],
                'total': total
            }), 200
        else:
            return jsonify({'error': 'no logs'}), 404
    return jsonify({'error': 'invalid token'}), 401
