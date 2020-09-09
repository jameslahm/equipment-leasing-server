from crypt import methods
from flask import Flask, jsonify
from flask.globals import request
from flask.helpers import make_response
from .. import db
from ..models import Equipment, User

from .__init__ import api

@api.route('/equipments',methods=['GET'])
def get_all():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return jsonify({"error":"error message"})
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 10)
    elist = Equipment.search_byusername(current_user, request.args)
    anslist = []
    for i in range((page-1)*page_size, min(len(elist),page*page_size)):
        anslist.append(elist[i])
    return jsonify({"equipments":anslist,"total":len(anslist)})
    


@api.route('/equipments/<id>',methods=["GET","PUT","DELETE"])
def equipment_operate(id):
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return jsonify({"error":"error message"})
    if request.method == "GET":
        return jsonify(Equipment.query.get(id).to_json())
    if request.method == "PUT":
        Equipment.update_equipment(id, current_user, request.form)
        return jsonify(Equipment.query.get(id).to_json())
    if request.method == "DELETE":
        return jsonify(Equipment.delete_equipment(id, current_user))


