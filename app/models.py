import re

from sqlalchemy.sql.expression import null
from . import db 
from flask import request,current_app
from datetime import datetime
from werkzeug.security import check_password_hash,generate_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer

class Permission:
    NORMAL = 0x01
    LENDER = 0x02
    ADMIN = 0x04

class RoleName:
    ADMIN = 'admin'
    NORMAL = 'normal'
    LENDER ='lender'

class EquipmentStatus:
    UNREVIEWED = 0
    IDLE = 1
    LEASE = 2

class ApplicationStatus:
    UNREVIEWED = 0x01
    AGREE = 0x02
    REFUSE = 0x04

class NotificationContent:
    LENDER_APPLICATION_APPLY_MESSAGE = ""
    LENDER_APPLICATION_AGREE_MESSAGE = ""
    LENDER_APPLICATION_REFUSE_MESSAGE = ""
    EQUIPMENT_APPLICATION_APPLY_MESSAGE = ""
    EQUIPMENT_APPLICATION_AGREE_MESSAGE = ""
    EQUIPMENT_APPLICATION_REFUSE_MESSAGE = ""

class ApplicationType:
    APPLY_LENDER = 0
    APPLY_PUTON = 1
    APPLY_BORROW = 2


class Role(db.Model):
    __tablename__ = 'role'
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    permission = db.Column('permission',
    db.Enum(Permission.NORMAL,Permission.LENDER,Permission.ADMIN),
    unique=False)
    name = db.Column('name',db.Enum(
        RoleName.ADMIN,RoleName.NORMAL,RoleName.LENDER
    ),unique=True)
    users = db.relationship('User',backref='role',lazy='dynamic')

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    email = db.Column('email',db.String(64),unique=True)
    username = db.Column('username',db.String(64),unique=True)
    role_id = db.Column('role_id',db.Integer,db.ForeignKey('role.id',ondelete='cascade'))
    password = db.Column('password',db.String(64),nullable=False)
    confirmed = db.Column('confirmed',db.Boolean,default=False)
    avatar = db.Column('avatar',db.String(128))
    equipments = db.relationship('Equipment',backref='owner',lazy='dynamic')
    lender_app = db.relationship('LenderApplication',backref='user',lazy='dynamic')
    lab_name = db.Column('lab_name',db.String(64),default="")
    lab_location = db.Column('lab_name',db.String(64),default="")
    def to_json(self):
        json_user={
            'id':self.id,
            'username':self.userName,
            'email': self.email,
            'avatar': self.avatar,
            'confirmed': self.confirmed,
            'role': self.role.name,
        }
        if(self.role.name == RoleName.LENDER):
            json_user['lab_name']=self.lab_name
            json_user['lab_location']=self.lab_location
        return json_user
    
    @property
    def password(self):
        raise AttributeError("password is not readable")

    @password.setter
    def password(self, password):
        self.password = generate_password_hash(password)

    def verify_password(self,password):
        return check_password_hash(self.password_hash,password)

    def generate_auth_token(self,expiration):
        s=TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'],expires_in=expiration)
        return s.dumps(self.id).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s=TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            id=s.loads(token.encode('utf-8'))
        except:
            return False
        return User.query.filter(User.id == id).first()
    
    @staticmethod
    def search_byusername(u_name) :
        return User.query.filter(User.username.contains(u_name)).all()
    
    @staticmethod
    def update_userinfo(id,token,body:dict) :
        user_now = User.verify_auth_token(token)
        user_update = User.query.filter(User.id == id).first()
        if user_now and user_update:
            if body.get('username'):
                user_update.username = body.get('username')
            if body.get('password'):
                user_update.password = body.get('username')
            if body.get('avatar'):
                user_update.avatar = body.get('avatar')
            if user_now.role.permission == Permission.ADMIN :
                if body.get('confirmed'):
                    user_update.confirmed = body['confirmed']
                if body.get('role'):
                    user_update.role_id = body['role']
        else:
            return null
        db.session.commit()
        return user_update
    @staticmethod
    def delete_user(id,token) :
        user_now = User.verify_auth_token(token)
        user_update = User.query.filter(User.id == id).first()
        if user_now and user_update:
            if user_now.role.permission == Permission.ADMIN:
                record = User.query.filter(User.id == id).first()
                db.session.delete(record)
                db.session.commit()
                return record
        else:
            return null
    
class Equipment(db.Model):
    __tablename__ = 'equipment'
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    owner_id = db.Column('owner_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    status = db.Column('status',db.Enum(EquipmentStatus.UNREVIEWED,
    EquipmentStatus.IDLE,EquipmentStatus.LEASE),nullable=False)
    return_time = db.Column('return_time',db.datetime)
    name = db.Column('name',db.String(64))
    usage = db.Column('usage',db.String(64))
    current_application_id = db.Column('current_app_id',db.Integer,
    db.ForeignKey('equipmentBorrowApplication.id',ondelete='cascade'))
    confirmed_back = db.Column('comfirmed_back',db.Boolean,default=False)

    def to_json(self):
        json_equipment={
            'id': self.id,
            'status': self.status,
            'return_time': self.return_time,
            'name': self.name,
            'owner': {
                'lab_name': self.owner.lab_name,
                'lab_location': self.owner.lab_location,
                'email': self.owner.email,
                'username': self.owner.username,
                'id': self.owner_id
            }
        }
        return json_equipment

    @staticmethod
    def search_equipments(token,body):
        user_now = User.verify_auth_token(token)
        if user_now:
            equipments=Equipment.query
            if body.get('name'):
                equipments = equipments.filter(Equipment.name.contains(body['name']))
            if body.get('lab_location'):
                equipments = equipments.filter(Equipment.lab_location.contains(body['lab_location']))
            if body.get('status'):
                s = 0 if body['status'] == 'unreviewed' \
                else 1 if body['status'] == 'idle' else 2
                equipments = equipments.filter(Equipment.status == s)
            if body.get('owner_id'):
                equipments = equipments.filter(Equipment.owner_id == body['owner_id'])
            return equipments.all()
        else :
            return null

    @staticmethod
    def update_equipment(id,token,body):
        user_now = User.verify_auth_token(token)
        if user_now:
            equipment = Equipment.query.filter(Equipment.id == id).first()
            if equipment and (equipment.owner_id == user_now.id
            or user_now.role.permission == Permission.ADMIN):
                if body.get('name'):
                    equipment.name = body['name']
                if body.get('usage'):
                    equipment.usage = body['usage']
                db.session.commit()
                return equipment
            else:
                return null
        else:
            return null
    
    @staticmethod
    def delete_equipment(id,token):
        user_now = User.verify_auth_token(token)
        equipment = Equipment.query.filter(Equipment.id == id)
        if user_now and equipment:
            if user_now.role.permission == Permission.ADMIN or \
            equipment.owner_id == user_now.id :
                record = Equipment.query.filter(Equipment.id == id).first()
                db.session.delete(record)
                db.session.commit()
                return record     
        return null

class LenderApplication(db.Model):
    __tablename__ = 'lenderApplication'
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    candidate_id = db.Column('candidate_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    lab_name = db.Column('lab_name',db.String(64))
    lab_location = db.Column('lab_location',db.String(64))
    status = db.Column('status',db.Enum(
        ApplicationStatus.UNREVIEWED,
        ApplicationStatus.AGREE,
        ApplicationStatus.REFUSE
    ))
    
    def to_json(self):
        json_lenderApplication={
            'id': self.id,
            'status': self.status,
            'lab_name': self.lab_name,
            'lab_location': self.lab_location,
            'candidate': {
                'username': self.user.username,
                'email': self.user.email,
                'avatar': self.user.avatar,
                'id': self.candidate_id
            }
        }
        return json_lenderApplication
    
class EquipmentPutOnApplication(db.Model):
    __tablename__ = 'equipemnt_puton_application'
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    candidate_id = db.Column('candidate_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    usage = db.Column('usage',db.String(64))
    equipment_id = db.Column('equipment_id',db.Integer,db.ForeignKey('equipment.id',ondelete='cascade'))
    application_time = db.Column('application_time',db.datetime)
    status = db.Column('status',db.Enum(
        ApplicationStatus.UNREVIEWED,
        ApplicationStatus.AGREE,
        ApplicationStatus.REFUSE
    ))
    review_time = db.Column('review_time',db.datetime)
    reviewer_id = db.Column('reviewer_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    candidate = db.relationship('User',uselist=False,backref='putonApplications',lazy='dynamic',foreign_keys=candidate_id)
    reviewer = db.relationship('User',uselist=False,backref='reviewPutonApplications',lazy='dynamic',foreign_keys=reviewer_id)
    
    def to_json(self):
        json_equipmentBorrowApplication={
            'id':self.id,
            'status': self.status,
            'reviewer' : {
                'username': self.reviewer.username,
                'email': self.reviewer.email,
                'avatar': self.reviewer.avatar,
                'id': self.reviewer_id
            },
            'usage': self.usage,
            'application_time': self.application_time,
            'review_time': self.review_time,
            'candidate': {
                'username': self.candidate.username,
                'email': self.candidate.email,
                'avatar': self.candidate.avatar,
                'id': self.candidate_id
            }
        }
        return json_equipmentBorrowApplication

class EquipmentBorrowApplication(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    candidate_id = db.Column('candidate_id',db.ForeignKey('user.id',ondelete='cascade'))
    candidate = db.relationship('User',backref='borrowApplications',lazy='dynamic',foreign_keys=candidate_id)
    return_time = db.Column('review_time',db.datetime)
    usage = db.Column('usage',db.String(64))
    equipment_id = db.Column('equipment_id',db.Integer,db.ForeignKey('equipment.id',ondelete='cascade'))
    application_time = db.Column('application_time',db.datetime)
    status = db.Column('status',db.Enum(
        ApplicationStatus.UNREVIEWED,
        ApplicationStatus.AGREE,
        ApplicationStatus.REFUSE
    ))
    review_time = db.Column('review_time',db.datetime)
    reviewer_id = db.Column('reviewer_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    reviewer = db.relationship('User',backref='reviewBorrowApplications',lazy='dynamic',foreign_keys=reviewer_id)

    def to_json(self):
        json_equipmentBorrowApplication={
            'id': self.id,
            'status': self.status,
            'reviewer': {
                'username': self.reviewer.username,
                'email': self.reviewer.email,
                'lab_name': self.reviewer.lab_name,
                'lab_location': self.reviewer.lab_location,
                'id':self.reviewer_id
            },
            'usage': self.usage,
            'application_time': self.application_time,
            'review_time': self.review_time,
            'candidate': {
                'username': self.candidate.username,
                'email': self.candidate.email,
                'avatar': self.candidate.avatar,
                'id': self.candidate_id
            }
        }
        return json_equipmentBorrowApplication

class Notification(db.Model):
    id = db.Column('id',db.Integer,primary_key=True,autoincrement=True)
    sender_id = db.Column('sender_id',db.Integer,db.ForeignKey('user.id',ondelete='cascade'))
    receiver_id = db.Column('receiver_id',db.Integer,db.ForeignKey('user_id',ondelte='cascade'))
    sender = db.relationship('User',backref='sended_Notifications',lazy='dynamic',foreign_keys=sender_id)
    receiver = db.relationship('User',backref='received_Notifications',lazy='dynamic',foreign_keys=receiver_id)
    content = db.Column('content',db.String(64))
    notification_time = db.Column('notification_time',db.datetime)
    isRead = db.Column('isRead',db.Boolean)
    type = db.Column('type',ApplicationType)
    result = db.Column('result',ApplicationStatus)
    application_id = db.Column('application_id',db.Integer,db.ForeignKey(''))

    def to_json(self):
        json_notification={
            'id': self.id,
            'sender': {
                'username': self.sender.username,
                'email': self.sender.email,
                'avatar': self.sender.avatar,
                'id': self.sender_id
            },
            'content': self.content,
            'notification_time': self.notification_time,
            'isRead': self.isRead,
            'application_id': self.application_id,
            'type': self.type,
            'result': 'agree' if self.result == ApplicationStatus.AGREE
            else 'refuse' if self.result == ApplicationStatus.REFUSE 
            else 'unreviewed'
        }
        return json_notification
