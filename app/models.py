from itertools import permutations
from sqlalchemy.sql.expression import null
from . import db
from flask import current_app
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer
from copy import deepcopy

class Permission:
    NORMAL = 0x01
    LENDER = 0x02
    ADMIN = 0x04


class RoleName:
    ADMIN = 'admin'
    NORMAL = 'normal'
    LENDER = 'lender'


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
    __tablename__ = 'roles'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    permission = db.Column('permission',
                           db.Integer,
                           unique=False)
    name = db.Column('name', db.Integer, unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def insert_roles():
        for name in [RoleName.ADMIN,RoleName.LENDER,RoleName.NORMAL]:
            role = Role.query.filter_by(name = name).first()
            if role is None: 
                if name == RoleName.ADMIN:
                    role = Role(permission =Permission.ADMIN,name = name)
                if name == RoleName.LENDER:
                    role = Role(permission = Permission.LENDER,name = name)
                if name == RoleName.NORMAL:
                    role = Role(permission = Permission.NORMAL, name = name)
                db.session.add(role)
                db.session.commit()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    email = db.Column('email', db.String(64), unique=True)
    username = db.Column('username', db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey(
        'roles.id', ondelete='cascade'))
    password_hash = db.Column(
        'password_hash', db.String(64))
    confirmed = db.Column('confirmed', db.Boolean, default=False)
    avatar = db.Column('avatar', db.String(128))
    equipments = db.relationship('Equipment', backref='owner', lazy='dynamic')
    lender_app = db.relationship(
        'LenderApplication', backref='user', lazy='dynamic')
    lab_name = db.Column('lab_name', db.String(64), default="")
    lab_location = db.Column('lab_location', db.String(64), default="")

    def __init__(self,**kwargs):
        super(User,self).__init__(**kwargs)
        if self.role is None:
            if self.email==current_app.config['FLASK_ADMIN']:
                self.role=Role.query.filter_by(permission=Permission.ADMIN).first()
            else:
                self.role = Role.query.filter_by(permission=Permission.NORMAL).first()
            self.role_id = self.role.id

    def to_json(self):
        json_user = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'avatar': self.avatar,
            'confirmed': self.confirmed,
            'role': self.role.name,
        }
        if(self.role.name == RoleName.LENDER):
            json_user['lab_name'] = self.lab_name
            json_user['lab_location'] = self.lab_location
        return json_user

    @property
    def password(self):
        raise AttributeError("password is not readable")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration):
        s = TimedJSONWebSignatureSerializer(
            current_app.config['SECRET_KEY'], expires_in=expiration)
        return s.dumps(self.id).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            id = s.loads(token.encode('utf-8'))
        except:
            return False
        return User.query.filter(User.id == id).first()

    @staticmethod
    def get_admin():
        return User.query.filter(User.email == current_app.config['FLASK_ADMIN']).first()

    @staticmethod
    def search_byusername(body):
        if body.get('username'):
            u_name = body.get('username')
        else:
            u_name = ''
        page = body['page'] if body.get('page') else 1
        page_size = body['page_size'] if body.get('page_size') else 10
        pa = User.query.filter(User.username.contains(u_name)).paginate(
            int(page),int(page_size),error_out=False
        )
        return pa.items,pa.total
        

    @staticmethod
    def update_userinfo(id, user_now, body: dict):
        user_update = User.query.filter(User.id == id).first()
        if user_now and user_update:
            if body.get('username'):
                user_update.username = body.get('username')
            if body.get('password'):
                user_update.password = body.get('username')
            if body.get('avatar'):
                user_update.avatar = body.get('avatar')
            if user_now.role.permission == Permission.ADMIN:
                if body.get('confirmed')==True or body.get('confirmed')==False:
                    user_update.confirmed = body['confirmed']
                if body.get('role'):
                    user_update.role = Role.query.filter_by(name=body['role']).first()
                    user_update.role_id = user_update.role.id
        else:
            return null
        db.session.commit()
        return user_update

    @staticmethod
    def delete_user(id, user_now):
        user_update = User.query.filter(User.id == id).first()
        if user_now and user_update:
            if user_now.role.permission == Permission.ADMIN:
                record = User.query.filter(User.id == id).first().to_json()
                User.query.filter(User.id == id).delete()
                db.session.commit()
                return record
        else:
            return null


class Equipment(db.Model):
    __tablename__ = 'equipments'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='cascade'))
    status = db.Column('status', db.Integer, nullable=False)
    return_time = db.Column('return_time', db.DateTime)
    name = db.Column('name', db.String(64))
    usage = db.Column('usage', db.String(64))
    borrow_applications = db.relationship(
        'EquipmentBorrowApplication', backref='equipment', lazy='dynamic')
    confirmed_back = db.Column('comfirmed_back', db.Boolean, default=False)
    current_application_id=db.Column('current_application_id',db.Integer)

    # def get_current_application(self):
    #     if self.confirmed_back==True:
    #         return None
    #     current_application=self.borrow_applications.filter(status==ApplicationStatus.AGREE).order_by(EquipmentBorrowApplication.return_time.desc()).first()
    #     return current_application

    def to_json(self):
        json_equipment = {
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
    def search_equipments(user_now, body):
        if user_now:
            equipments = Equipment.query
            if body.get('name'):
                equipments = equipments.filter(
                    Equipment.name.contains(body['name']))
            if body.get('lab_location'):
                equipments = equipments.filter(
                    Equipment.lab_location.contains(body['lab_location']))
            if body.get('status'):
                s = 0 if body['status'] == 'unreviewed' \
                    else 1 if body['status'] == 'idle' else 2
                equipments = equipments.filter(Equipment.status == s)
            if body.get('owner_id'):
                equipments = equipments.filter(
                    Equipment.owner_id == body['owner_id'])
            page = body['page'] if body.get('page') else 1
            page_size = body['page_size'] if body.get('page_size') else 10
            pa = equipments.paginate(
                page,page_size,error_out=False
            )
            return pa.items,pa.total
        else:
            return null

    @staticmethod
    def update_equipment(id, user_now, body):
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
    def delete_equipment(id, user_now):
        equipment = Equipment.query.filter(Equipment.id == id)
        if user_now and equipment:
            if user_now.role.permission == Permission.ADMIN or \
                    equipment.owner_id == user_now.id:
                record = Equipment.query.filter(Equipment.id == id).first().to_json()
                Equipment.query.filter(Equipment.id == id).delete()
                db.session.commit()
                return record
        return null


class LenderApplication(db.Model):
    __tablename__ = 'lender_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='cascade'))
    lab_name = db.Column('lab_name', db.String(64))
    lab_location = db.Column('lab_location', db.String(64))
    status = db.Column('status', db.Integer)

    def to_json(self):
        json_lenderApplication = {
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

    @staticmethod
    def on_changed_status(target, value, oldvalue, initiator):
        User.update_userinfo(target.candidate_id, User.get_admin(), {
            'role': 0x02
        })

    @staticmethod
    def get_application(user_now, body):
        if user_now:
            if user_now.role.permission == Permission.ADMIN:
                applications = LenderApplication.query
            else:
                applications = LenderApplication.query.filter(
                    LenderApplication.candidate_id == id)
            if body.get('status'):
                s = 0x01 if body['status'] == 'unreviewed' \
                    else 0x02 if body['status'] == 'agree' else 0x04
                applications = applications.filter(
                    LenderApplication.status == s)
            if body.get('candidate_id'):
                applications = applications.filter(
                    LenderApplication.candidate_id == body['candidate_id'])
            if body.get('reviewer_id'):
                applications = applications.filter(
                    LenderApplication.reviewer_id == body['reviewer_id'])
            page = body['page'] if body.get('page') else 1
            page_size = body['page_size'] if body.get('page_size') else 10
            pa = applications.paginate(
                page,page_size,error_out=False
            )
            return pa.items,pa.total
        return null

    @staticmethod
    def update_application(id, user_now, body):
        if user_now:
            application = LenderApplication.query.filter(
                LenderApplication.id == id).first()
            application.status = body.get('status')
            db.session.commit()
            return application
        return null


db.event.listen(LenderApplication.status, 'set',
                LenderApplication.on_changed_status)


class EquipmentPutOnApplication(db.Model):
    __tablename__ = 'equipemnt_puton_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='cascade'))
    usage = db.Column('usage', db.String(64))
    equipment_id = db.Column(db.Integer, db.ForeignKey(
        'equipments.id', ondelete='cascade'))
    application_time = db.Column('application_time', db.DateTime)
    status = db.Column('status', db.Integer)
    review_time = db.Column('review_time', db.DateTime)
    reviewer_id = db.Column(db.Integer, db.ForeignKey(
        'users.id', ondelete='cascade'))
    # TODO:
    candidate = db.relationship(
        'User', backref='puton_applications', lazy='select', foreign_keys=[candidate_id])
    reviewer = db.relationship(
        'User', backref='review_puton_applications', lazy='select', foreign_keys=[reviewer_id])

    def to_json(self):
        json_equipmentBorrowApplication = {
            'id': self.id,
            'status': self.status,
            'reviewer': {
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

    @staticmethod
    def on_changed_status(target, value, oldvalue, initiator):
        target.review_time = datetime.now()

    @staticmethod
    def get_application(user_now, body):
        if user_now:
            if user_now.permission == Permission.ADMIN:
                applications = EquipmentPutOnApplication.query
            else:
                applications = EquipmentPutOnApplication.query.filter(
                    EquipmentPutOnApplication.candidate_id == user_now.id)
            if body.get('status'):
                s = 0x01 if body['status'] == 'unreviewed' \
                    else 0x02 if body['status'] == 'agree' else 0x04
                applications = applications.filter(
                    EquipmentPutOnApplication.status == s)
            if body.get('candidate_id'):
                applications = applications.filter(
                    EquipmentPutOnApplication.candidate_id == body['candidate_id'])
            if body.get('reviewer_id'):
                applications = applications.filter(
                    EquipmentPutOnApplication.reviewer_id == body['reviewer_id'])
            page = body['page'] if body.get('page') else 1
            page_size = body['page_size'] if body.get('page_size') else 10
            pa = applications.paginate(
                page,page_size,error_out=False
            )
            return pa.items,pa.total
        return null

    @staticmethod
    def update_application(id, user_now, body):
        if user_now:
            application = EquipmentPutOnApplication.query.filter(
                EquipmentPutOnApplication.id == id).first()
            application.status = body.get('status')
            db.session.commit()
            return application
        return null


db.event.listen(EquipmentPutOnApplication.status, 'set',
                EquipmentPutOnApplication.on_changed_status)


class EquipmentBorrowApplication(db.Model):
    __tablename__ = 'equipment_borrow_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column('candidate_id', db.ForeignKey(
        'users.id', ondelete='cascade'))
    candidate = db.relationship(
        'User', backref='borrow_applications', lazy='select', foreign_keys=[candidate_id])
    return_time = db.Column('return_time', db.DateTime)
    usage = db.Column('usage', db.String(64))

    equipment_id = db.Column(db.Integer, db.ForeignKey(
        'equipments.id', ondelete='cascade'))

    application_time = db.Column('application_time', db.DateTime)
    status = db.Column('status', db.Integer)
    review_time = db.Column('review_time', db.DateTime)
    reviewer_id = db.Column('reviewer_id', db.Integer,
                            db.ForeignKey('users.id', ondelete='cascade'))
    reviewer = db.relationship(
        'User', backref='review_borrow_applications', lazy='select', foreign_keys=[reviewer_id])

    def to_json(self):
        json_equipmentBorrowApplication = {
            'id': self.id,
            'status': self.status,
            'reviewer': {
                'username': self.reviewer.username,
                'email': self.reviewer.email,
                'lab_name': self.reviewer.lab_name,
                'lab_location': self.reviewer.lab_location,
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

    @staticmethod
    def get_application(user_now, body):
        if user_now:
            if user_now.permission == Permission.ADMIN:
                applications = EquipmentBorrowApplication.query
            else:
                if user_now.permission == Permission.LENDER:
                    applications = EquipmentBorrowApplication.query.filter(
                        EquipmentBorrowApplication.reviewer_id == user_now.id)
                else:
                    applications = EquipmentBorrowApplication.query.filter(
                        EquipmentBorrowApplication.candidate_id == user_now.id)

            if body.get('status'):
                s = 0x01 if body['status'] == 'unreviewed' \
                    else 0x02 if body['status'] == 'agree' else 0x04
                applications = applications.filter(
                    EquipmentBorrowApplication.status == s)
            if body.get('candidate_id'):
                applications = applications.filter(
                    EquipmentBorrowApplication.candidate_id == body['candidate_id'])
            if body.get('reviewer_id'):
                applications = applications.filter(
                    EquipmentBorrowApplication.reviewer_id == body['reviewer_id'])
            return applications.all()
        return null

    @staticmethod
    def update_application(id, user_now, body):
        if user_now:
            application = EquipmentBorrowApplication.query.filter(
                EquipmentBorrowApplication.id == id).first()
            application.status = body.get('status')
            application.reviewer_id = user_now.id
            application.review_time = datetime.now()
            db.session.commit()
            return application
        return null


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column('sender_id', db.Integer,
                          db.ForeignKey('users.id', ondelete='cascade'))
    receiver_id = db.Column('receiver_id', db.Integer,
                            db.ForeignKey('users.id', ondelete='cascade'))
    sender = db.relationship(
        'User', backref='sended_notifications', lazy='select', foreign_keys=[sender_id])
    receiver = db.relationship(
        'User', backref='received_notifications', lazy='select', foreign_keys=[receiver_id])
    content = db.Column('content', db.String(64))
    notification_time = db.Column('notification_time', db.DateTime)
    isRead = db.Column('isRead', db.Boolean)
    type = db.Column('type', db.Integer)
    application_id = db.Column('application_id', db.Integer)

    def to_json(self):
        if self.type == ApplicationType.APPLY_BORROW:
            application = EquipmentBorrowApplication.query.filter(
                EquipmentBorrowApplication.id == self.application_id
            ).first()
        if self.type == ApplicationType.APPLY_LENDER:
            application = LenderApplication.query.filter(
                LenderApplication.id == self.application_id
            ).first()
        else:
            application = EquipmentPutOnApplication.query.filter(
                EquipmentPutOnApplication.id == self.application_id
            ).first()
        json_notification = {
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
            'result': 'agree' if application.status == ApplicationStatus.AGREE
            else 'refuse' if application.status == ApplicationStatus.REFUSE
            else 'unreviewed'
        }
        return json_notification

    @staticmethod
    def get_notification(user_now, body):
        if user_now:
            if user_now.permission == Permission.ADMIN:
                notifications = Notification.query
            else:
                notifications = Notification.query.filter(
                    Notification.receiver_id == user_now.id)
            if body.get('isRead'):
                notifications = notifications.filter(
                    Notification.isRead == body['isRead'])
            page = body['page'] if body.get('page') else 1
            page_size = body['page_size'] if body.get('page_size') else 10
            pa = notifications.paginate(
                page,page_size,error_out=False
            )
            return pa.items,pa.total
        return null

    @staticmethod
    def update_notification(id, user_now, body):
        if user_now:
            notification = Notification.query.filter(
                Notification.id == id).first()
            notification.isRead = body.get('isRead')
            db.session.commit()
            return notification
        return null

    @staticmethod
    def delete_notification(id, user_now):
        if user_now:
            notification = Notification.query.filter(Notification.id == id).first().to_json()
            Notification.query.filter(Notification.id == id).delete()
            db.session.commit()
            return notification
        return null
