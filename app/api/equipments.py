from crypt import methods
from flask import Flask, jsonify, Response
from flask import json
from flask.globals import request
from sqlalchemy.sql.expression import null
from ..models import Equipment, User
from . import api

@api.route('/equipments',methods=['GET'])
def get_all():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return Response(jsonify({"error":"unauthorized"}), 401)
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 10)
    elist = Equipment.search_byusername(current_user, request.args)
    anslist = []
    for i in range((page-1)*page_size, min(len(elist),page*page_size)):
        anslist.append(elist[i].to_json())
    return Response(jsonify({"equipments":anslist,"total":len(anslist)}))
    


@api.route('/equipments/<int:id>',methods=["GET","PUT","DELETE"])
def equipment_operate(id):
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return Response(jsonify({"error":"unauthorized"}), 401)
    if request.method == "GET":
        equipment = Equipment.query.filter_by(id=id).first()
        if equipment is None:
            return Response(jsonify({}))
        return Response(jsonify(equipment.to_json()))
    if request.method == "PUT":
        update = Equipment.update_equipment(id, current_user, request.form)
        if update == null:
            return Response(jsonify({"error":"no such equipment"}, 400))
        return Response(jsonify(Equipment.query.get(id).to_json()))
    if request.method == "DELETE":
        delete = Equipment.delete_equipment(id, current_user)
        if delete == null:
            return Response(jsonify({"error":"no such equipment"}), 400)
        return Response(jsonify(delete.to_json()))
