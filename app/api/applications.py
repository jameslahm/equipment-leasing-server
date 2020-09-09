from flask import request,jsonify
from . import api
from ..models import User,ApplicationType,LenderApplication,EquipmentPutOnApplication,EquipmentBorrowApplication
import json

#分页
def paginate(page: int, page_size: int, applications):
    #page默认为1,page_size默认为10
    page = int(page)
    page_size = int(page_size)
    if not page:
        page = 1
    if not page_size:
        page_size = 10

    begin_index = (page-1)*page_size
    end_index = page*page_size
    if end_index > len(applications):
        return  applications[begin_index:]
    else:
        return applications[begin_index:end_index]

#获取全部申请
@api.route("/applications/<type>", methods=['GET'])
def get_all_applications(type):
    para = {}   #参数字典
    for key in request.args.keys():
        para[key] = request.args.get(key)
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)

    if not user:
        return jsonify({"error":401})
    elif (not type):
        return jsonify({"error":400})
    else:
        applications = [] 
        items = []
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            items = LenderApplication.query.all()
            if para["status"]:
                items = filter(lambda x: x.status == para["status"], items)
            if para["reviewer_id"]:
                items = filter(lambda x: x.candidate_id == para["reviewer_id"], items)
        
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            items = EquipmentPutOnApplication.query.all()
            if para["status"]:
                items = filter(lambda x: x.status == para["status"], items)
            if para["candidate_id"]:
                items = filter(lambda x: x.candidate_id == para["candidate_id"], items)
            if para["reviewer_id"]:
                items = filter(lambda x: x.candidate_id == para["reviewer_id"], items)

        else:           #APPLY_BORROW
            items = EquipmentBorrowApplication.query.all()
            if para["status"]:
                items = filter(lambda x: x.status == para["status"], items)
            if para["candidate_id"]:
                items = filter(lambda x: x.candidate_id == para["candidate_id"], items)
            if para["reviewer_id"]:
                items = filter(lambda x: x.candidate_id == para["reviewer_id"], items)
            
        for item in items:
            applications.append(item.to_json())

        res = paginate(para["page"], para["page_size"], applications)
        if type == ApplicationType.APPLY_LENDER:
            return jsonify({"lender_applications": res, "total": len(res)})
        elif type == ApplicationType.APPLY_PUTON:
            return jsonify({"equipment_puton_applications": res, "total": len(res)})
        else:
            return jsonify({"equipment_borrow_applications": res, "total": len(res)})
                    
            
#获取申请信息            
@api.route("/applications/<int:type>/<int:id>", methods = ['GET'])
def get_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    res = None

    if not user:
        return jsonify({"error": 401})
    else:
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            res = LenderApplication.query.get(id).to_json()
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            res = EquipmentPutOnApplication.query.get(id).to_json()
        else:           #APPLY_BORROW
            res = EquipmentBorrowApplication.query.get(id).to_json()

        return jsonify(res)

#更新申请信息            
@api.route("/applications/<int:type>/<int:id>", methods = ['PUT'])
def update_application(type, id):
    status = request.args.get("status")
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    item = None

    if not user:
        return jsonify({"error": 401})
    else:
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            item = LenderApplication.query.get(id)
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            item = EquipmentPutOnApplication.query.get(id)
        else:           #APPLY_BORROW
            item = EquipmentBorrowApplication.query.get(id)

    item.status = status
    return jsonify(item.to_json())
