from flask.globals import request
import json
from flask.helpers import make_response
from .. import db
from ..models import Equipment, User
from . import api

@api.route('/equipments',methods=['GET'])
def get_all():
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return make_response(json.dumps({"error":"error message"}), 401)
    page = request.args.get("page", 1)
    page_size = request.args.get("page_size", 10)
    elist = Equipment.search_byusername(current_user, request.args)
    anslist = []
    for i in range((page-1)*page_size, min(len(elist),page*page_size)):
        anslist.append(elist[i])
    return {"equipments":anslist,"total":len(anslist)}
    


@api.route('/equipments/<id>',methods=["GET","PUT","DELETE"])
def equipment_operate(id):
    current_user = User.verify_auth_token(request.headers.get("Authorization"))
    if not current_user:
        return make_response(json.dumps({"error":"error message"}), 401)
    if request.method == "GET":
        return Equipment.query.get(id).to_json()
    if request.method == "PUT":
        Equipment.update_equipment(id, current_user, request.form)
        return Equipment.query.get(id).to_json()
    if request.method == "DELETE":
        return Equipment.delete_equipment(id, current_user)


