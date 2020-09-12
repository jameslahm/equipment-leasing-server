from flask import jsonify,request
from ..models import Comment,User,Equipment
from . import api

@api.route('/equipments/<int:id>/comments',methods=['GET'])
def get_comments(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:
        equipment_id = id
        body = request.args.to_dict()
        body['equipment_id']=equipment_id
        items, total = Comment.get_comments(user, body)
        print(items)
        if items is not None:
            return jsonify({
                'comments': [x.to_json() for x in items],
                'total': total
            }), 200
        else:
            return jsonify({'error': 'no such comments'}), 404
    return jsonify({'error': 'invalid token'}), 401

@api.route('/equipments/<int:id>/comments',methods =['POST'])
def add_comment(id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:    
        comment = Comment.insert_comment(user,id,request.json)
        if comment is not None:
            return jsonify(comment.to_json()),200
        else:
            return jsonify({'error':'insert error'}),400
    return jsonify({'error': 'invalid token'}), 401

@api.route('/equipments/<int:id>/comments/<int:comment_id>',methods=['DELETE'])
def delete_comment(id,comment_id):
    user = User.verify_auth_token(request.headers.get('Authorization'))
    if user:    
        comment = Comment.delete_comment(comment_id,user)
        if comment is not None:
            return jsonify(comment),200
        else:
            return jsonify({'error':'delete error'}),404        
    return jsonify({'error': 'invalid token'}), 401
 