from flask import request, jsonify
from datetime import datetime
from . import api
from .. import db
from ..models import ApplicationStatus, User, ApplicationType, LenderApplication, EquipmentPutOnApplication, EquipmentBorrowApplication
from ..models import SystemLog, SystemLogContent
# 获取全部申请


@api.route("/applications/<type>", methods=['GET', 'POST'])
def operate_applications(type):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    if not (user and user.confirmed):
        return jsonify({"error": 'invalid token'}), 401
    if request.method == 'GET':
        if type == ApplicationType.APPLY_LENDER:  # APPLY_LENDER
            items, total = LenderApplication.get_application(
                user, request.args)
            if items is not None:
                return jsonify({
                    'lender_applications': [x.to_json() for x in items],
                    'total': total
                }), 200
        elif type == ApplicationType.APPLY_PUTON:  # APPLY_PUTON
            items, total = EquipmentPutOnApplication.get_application(
                user, request.args)
            if items is not None:
                return jsonify({
                    'equipment_puton_applications': [x.to_json() for x in items],
                    'total': total
                }), 200
        else:  # APPLY_BORROW
            items, total = EquipmentBorrowApplication.get_application(
                user, request.args)
            if items is not None:
                return jsonify({
                    'equipment_borrow_applications': [x.to_json() for x in items],
                    'total': total
                }), 200
        return jsonify({'error': 'invalid params'}), 400
    if request.method == 'POST':
        body = request.json
        body['candidate_id'] = user.id
        application = None
        item = ""
        if type == ApplicationType.APPLY_LENDER and user.role.name == 'normal':
            application = LenderApplication.insert_lender_application(body)
            item = "lender application"
        elif type == ApplicationType.APPLY_PUTON and user.role.name == 'lender':
            item = "puton application"
            application = EquipmentPutOnApplication.insert_equipment_puton_application(
                body)
        elif type == ApplicationType.APPLY_BORROW and user.role.name == 'normal':
            item = "borrow application"
            application = EquipmentBorrowApplication.insert_equipment_borrow_application(
                body)
        if application is not None:
            log = SystemLog(content=SystemLogContent.INSERT_LOG.format(
                username=user.username, id=user.id,
                role=user.role.name, item=item,
                item_id=application.id
            ), type='insert', log_time=datetime.now())
            db.session.add(log)
            db.session.commit()
            return jsonify(application.to_json()), 200

        return jsonify({'error': 'bad request'}), 400

# 获取申请信息


@api.route("/applications/<type>/<int:id>", methods=['GET'])
def get_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    application = None
    if not (user and user.confirmed):
        return jsonify({"error": 'invalid token'}), 401
    else:
        if type == ApplicationType.APPLY_LENDER:  # APPLY_LENDER
            application = LenderApplication.query.filter_by(id=id).first()
        elif type == ApplicationType.APPLY_PUTON:  # APPLY_PUTON
            application = EquipmentPutOnApplication.query.filter_by(
                id=id).first()
        else:  # APPLY_BORROW
            application = EquipmentBorrowApplication.query.filter_by(
                id=id).first()
        if application is not None:

            return jsonify(application.to_json()), 200
        return jsonify({'error': 'no such application'}), 404


@api.route("/applications/<type>/<int:id>", methods=['DELETE'])
def delete_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    application = None
    if not (user and user.confirmed):
        return jsonify({"error": 'invalid token'}), 401
    else:
        if type == ApplicationType.APPLY_LENDER:  # APPLY_LENDER
            item = "lender application"
            application = LenderApplication.delete_application(id, user)
        elif type == ApplicationType.APPLY_PUTON:  # APPLY_PUTON
            item = "puton application"
            application = EquipmentPutOnApplication.delete_application(
                id, user)
        else:  # APPLY_BORROW
            item = 'borrow application'
            application = EquipmentBorrowApplication.delete_application(
                id, user)
        if application is not None:
            log = SystemLog(content=SystemLogContent.DELETE_LOG.format(
                username=user.username, id=user.id,
                role=user.role.name, item=item,
                item_id=application.id
            ), type='delete', log_time=datetime.now())
            db.session.add(log)
            db.session.commit()
            return jsonify(application.to_json()), 200
        return jsonify({'error': 'no such application'}), 404

# 更新申请信息


@api.route("/applications/<type>/<int:id>", methods=['PUT'])
def update_application(type, id):
    token = request.headers.get("Authorization")
    user = User.verify_auth_token(token)
    application = None

    if not (user and user.confirmed):
        return jsonify({"error": 401})
    else:
        item=""
        if type == ApplicationType.APPLY_LENDER:  # APPLY_LENDER
            item = "lender application"
            application = LenderApplication.query.filter_by(id=id).first()
            if application and application.status != ApplicationStatus.UNREVIEWED:
                return jsonify({"error": "bad request"}), 400

            if user.role.name != 'admin':
                return jsonify({"error": "bad request"}), 400

            application = LenderApplication.update_application(
                id, user, request.json)
        if type == ApplicationType.APPLY_PUTON:  # APPLY_PUTON
            item = "puton application"
            application = EquipmentPutOnApplication.query.filter_by(
                id=id).first()
            if application and application.status != ApplicationStatus.UNREVIEWED:
                return jsonify({"error": "bad request"}), 400

            if user.role.name != 'admin':
                return jsonify({"error": "bad request"}), 400

            application = EquipmentPutOnApplication.update_application(
                id, user, request.json)
        if type == ApplicationType.APPLY_BORROW:  # APPLY_BORROW
            item = "borrow application"
            application = EquipmentBorrowApplication.query.filter_by(
                id=id).first()
            if application and application.status != ApplicationStatus.UNREVIEWED:
                return jsonify({"error": "bad request"}), 400

            if application and (application.reviewer_id != user.id and user.role.name != 'admin'):
                return jsonify({"error": "bad request"}), 400

            application = EquipmentBorrowApplication.update_application(
                id, user, request.json)
        if application is not None:
            log = SystemLog(content=SystemLogContent.UPDATE_LOG.format(
                username=user.username, id=user.id,
                role=user.role.name, item=item,
                item_id=application.id
            ), type='update', log_time=datetime.now())
            db.session.add(log)
            db.session.commit()
            return jsonify(application.to_json()), 200
        return jsonify({'error': 'no such application'}), 404
