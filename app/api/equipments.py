from flask import jsonify,request
from flask import request
from ..models import Equipment,User
from . import api

@api.route('/equipments',methods=['GET'])
def get_equiments():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return jsonify({"error":"unauthorized"}), 401
    anslist,total = Equipment.search_equipments(current_user, request.args)
    return jsonify({"equipments":[x.to_json() for x in anslist],"total":total}),200


@api.route('/equipments/<int:id>',methods=["GET","PUT","DELETE"])
def equipment_operate(id):
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return jsonify({"error":"unauthorized"}), 401
    if request.method == "GET":
        equipment = Equipment.query.filter_by(id=id).first()
        if equipment is not None:
            return jsonify(equipment.to_json()),200
        return jsonify({'error':'no such equipment'}),404
    if request.method == "PUT":
        update = Equipment.update_equipment(id, current_user, request.json)
        if update is None:
            return jsonify({"error":"no such equipment"}, 404)
        return jsonify(update.to_json()),200
    if request.method == "DELETE":
        delete = Equipment.delete_equipment(id, current_user)
        if delete == None:
            return jsonify({"error":"no such equipment"}), 404
        return jsonify(delete),200
