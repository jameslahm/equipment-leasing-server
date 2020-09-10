from flask import request,jsonify
from . import api
from ..models import User,ApplicationType,LenderApplication,EquipmentPutOnApplication,EquipmentBorrowApplication
import json

#获取全部申请
@api.route("/applications/<type>", methods=['GET','POST'])
def operate_applications(type):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    if not user:
        return jsonify({"error":'invalid token'}),401
    if request.method == 'GET':
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            items ,total = LenderApplication.get_application(user,request.args)
            if items is not None:
                return jsonify({
                    'lender_applications':[x.to_json() for x in items],
                    'total':total
                    }),200
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            items ,total = EquipmentPutOnApplication.get_application(user,request.args)
            if items is not None:
                return jsonify({
                    'equipment_puton_applications':[x.to_json() for x in items],
                    'total':total
                    }),200
        else:           #APPLY_BORROW
            items ,total = EquipmentBorrowApplication.get_application(user,request.args)          
            if items is not None:
                return jsonify({
                    'equipment_borrow_applications':[x.to_json() for x in items],
                    'total':total
                    }),200
        return jsonify({'error':'invalid params'}),400
    if request.method == 'POST':
        body = request.json
        print(body)
        body['candidate_id'] = user.id 
        application = None
        if type == ApplicationType.APPLY_LENDER:
            application = LenderApplication.insert_lender_application(body)
        elif type == ApplicationType.APPLY_PUTON:
            application = EquipmentPutOnApplication.insert_equipment_puton_application(body)
        elif type == ApplicationType.APPLY_BORROW:
            application = EquipmentBorrowApplication.insert_equipment_borrow_application(body)
        if application is not None:
            return jsonify(application.to_json()),200

        return jsonify({'error':'invalid params'}),400

#获取申请信息            
@api.route("/applications/<type>/<int:id>", methods = ['GET'])
def get_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    res = None
    if not user:
        return jsonify({"error": 'invalid token'}),401
    else:
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            res = LenderApplication.query.filter_by(id=id).first()
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            res = EquipmentPutOnApplication.query.filter_by(id=id).first()
        else:           #APPLY_BORROW
            res = EquipmentBorrowApplication.query.filter_by(id=id).first()
        if res is not None:
            return jsonify(res.to_json()),200
        return jsonify({'error':'no such application'}),400

#更新申请信息            
@api.route("/applications/<type>/<int:id>", methods = ['PUT'])
def update_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    item = None

    if not user:
        return jsonify({"error": 401})
    else:
        if type == ApplicationType.APPLY_LENDER:   #APPLY_LENDER
            item = LenderApplication.update_application(id,user,request.json)
        elif type == ApplicationType.APPLY_PUTON: #APPLY_PUTON
            item = EquipmentPutOnApplication.update_application(id,user,request.json)
        else:           #APPLY_BORROW
            item = EquipmentBorrowApplication.update_application(id,user,request.json)
        if item is not None:
            return jsonify(item.to_json()),200
        return jsonify({'error':'no such application'}),400
