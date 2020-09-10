from app.api import equipments
from flask import request,jsonify
from . import api
from ..models import User,Equipment,ApplicationType,LenderApplication,EquipmentPutOnApplication,EquipmentBorrowApplication
from ..models import EquipmentStatus
import datetime

@api.route('/stat',methods=['GET'])
def stat():
    stat=dict()
    stat['total_users'] = User.query.count()
    stat['confirmed_users'] = User.query.filter_by(confirmed=True).count()
    stat['unconfirmed_users'] = stat['total_users'] - stat['confirmed_users']
    stat['normal_users'] = User.query.filter_by(role_id=3).count()
    stat['lender_users'] = User.query.filter_by(role_id=2).count()
    stat['total_equipements'] = Equipment.query.count()
    stat['unreviewed_equipments'] = Equipment.query.filter_by(status=EquipmentStatus.UNREVIEWED).count()
    stat['idle_equipments'] = Equipment.query.filter_by(status=EquipmentStatus.IDLE).count()
    stat['lease_equipments'] = Equipment.query.filter_by(status=EquipmentStatus.LEASE).count()
    stat['lender_applications'] = LenderApplication.query.count()
    stat['equipment_puton_applications'] = EquipmentPutOnApplication.query.count()
    stat['equipment_borrow_applications'] = EquipmentBorrowApplication.query.count()
    borrow_log = [0,0,0,0,0,0,0]
    for i in range(0,7):
        equipments = EquipmentBorrowApplication.query.all()
        for x in equipments:
            if (datetime.datetime.now()-x.application_time).days == i:
                borrow_log[i]+=1
    stat['borrow_log'] = borrow_log
    return jsonify(stat),200