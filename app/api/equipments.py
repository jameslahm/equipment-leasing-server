from flask import jsonify,request
from ..models import Equipment,User
from . import api
from ..models import SystemLog,SystemLogContent
from .. import db
from datetime import datetime

@api.route('/equipments',methods=['GET'])
def get_equiments():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not (current_user and current_user.confirmed):
        return jsonify({"error":"unauthorized"}), 401
    anslist,total = Equipment.search_equipments(current_user, request.args)
    return jsonify({"equipments":[x.to_json() for x in anslist],"total":total}),200


@api.route('/equipments/<int:id>',methods=["GET","PUT","DELETE"])
def equipment_operate(id):
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not (current_user and current_user.confirmed):
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
        log = SystemLog(content=SystemLogContent.UPDATE_LOG.format(
            username = current_user.username,id = current_user.id,
            role = current_user.role.name, item ="equipment",
            item_id = update.id
        ),type='update',log_time=datetime.now())
        db.session.add(log)
        db.session.commit()
        return jsonify(update.to_json()),200
    if request.method == "DELETE":
        delete = Equipment.delete_equipment(id, current_user)
        if delete == None:
            return jsonify({"error":"no such equipment"}), 404
        log = SystemLog(content=SystemLogContent.DELETE_LOG.format(
            username = current_user.username,id = current_user.id,
            role = current_user.role.name, item ="equipment",
            item_id = delete['id']
        ),type='delete',log_time=datetime.now())
        db.session.add(log)
        db.session.commit()
        return jsonify(delete),200
