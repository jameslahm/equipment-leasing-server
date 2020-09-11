from sqlalchemy.sql.expression import false
from . import db
from flask import current_app
from datetime import datetime
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer


class Permission:
    NORMAL = 0x01
    LENDER = 0x02
    ADMIN = 0x04


class RoleName:
    ADMIN = 'admin'
    NORMAL = 'normal'
    LENDER = 'lender'


class EquipmentStatus:
    UNREVIEWED = 'unreviewed'
    IDLE = 'idle'
    LEASE = 'lease'
    REFUSED = 'refused'


class ApplicationStatus:
    UNREVIEWED = 'unreviewed'
    AGREE = 'agree'
    REFUSE = 'refuse'

# TODO:


class NotificationContent:
    APPLICATION_APPLY_MESSAGE = " New unreviewed {type}, apply id: {id}, apply user id: {user_id}, username:{username}"
    APPLICATION_AGREE_MESSAGE = "Congratulations,Your {type} has been accepted, reviewer id:{reviewer_id}, reviewer name: {reviewer_name}, review time: {review_time}"
    APPLICATION_REFUSE_MESSAGE = "Sorry,Your {type} has been refused, reviewer id:{reviewer_id}, reviewer name: {reviewer_name}, review time: {review_time}"


class ApplicationType:
    APPLY_LENDER = 'lender'
    APPLY_PUTON = 'puton'
    APPLY_BORROW = 'borrow'


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    permission = db.Column('permission',
                           db.Integer,
                           unique=False)
    name = db.Column('name', db.Integer, unique=True)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        for name in [RoleName.ADMIN, RoleName.LENDER, RoleName.NORMAL]:
            role = Role.query.filter_by(name=name).first()
            if role is None:
                if name == RoleName.ADMIN:
                    role = Role(permission=Permission.ADMIN, name=name)
                if name == RoleName.LENDER:
                    role = Role(permission=Permission.LENDER, name=name)
                if name == RoleName.NORMAL:
                    role = Role(permission=Permission.NORMAL, name=name)
                db.session.add(role)
                db.session.commit()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    email = db.Column('email', db.String(64), unique=True)
    username = db.Column('username', db.String(64), unique=True)
    role_id = db.Column(db.Integer, db.ForeignKey(
        'roles.id'))
    password_hash = db.Column(
        'password_hash', db.String(64))
    confirmed = db.Column('confirmed', db.Boolean, default=False)
    avatar = db.Column('avatar', db.String(128))
    equipments = db.relationship('Equipment', backref='owner',
                                 lazy='dynamic', cascade="all,delete")
    lender_application = db.relationship(
        'LenderApplication', backref='user', lazy='dynamic', cascade="all,delete")
    lab_name = db.Column('lab_name', db.String(64), default="")
    lab_location = db.Column('lab_location', db.String(64), default="")

    sended_notifications = db.relationship(
        'Notification', backref='sender', lazy='select', foreign_keys='Notification.sender_id', cascade='all,delete')
    received_notifications = db.relationship(
        'Notification', backref='receiver', lazy='select', foreign_keys='Notification.receiver_id', cascade='all,delete')

    puton_applications = db.relationship(
        'EquipmentPutOnApplication', backref='candidate', lazy='select', foreign_keys='EquipmentPutOnApplication.candidate_id', cascade="all,delete")

    review_borrow_applications = db.relationship(
        'EquipmentBorrowApplication', backref='reviewer', lazy='select', foreign_keys='EquipmentBorrowApplication.reviewer_id', cascade="all,delete")

    borrow_applications = db.relationship(
        'EquipmentBorrowApplication', backref='candidate', lazy='select', foreign_keys='EquipmentBorrowApplication.candidate_id', cascade="all,delete")

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['FLASK_ADMIN']:
                self.role = Role.query.filter_by(
                    permission=Permission.ADMIN).first()
            else:
                self.role = Role.query.filter_by(
                    permission=Permission.NORMAL).first()
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
        # TODO:
        return s.dumps({"id": self.id}).decode('utf-8')

    @staticmethod
    def verify_auth_token(token):
        s = TimedJSONWebSignatureSerializer(current_app.config['SECRET_KEY'])
        try:
            # TODO:
            id = s.loads(token.encode('utf-8')).get("id")
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
        page = int(body['page'])+1 if body.get('page') else 1
        page_size = int(body['page_size']) if body.get('page_size') else 10
        pa = User.query.filter(User.username.contains(u_name))
        if body.get('order'):
            if body.get('order_by'):
                if body['order_by'] == 'username':
                    if body.get('order') == 'desc':
                        pa = pa.order_by(User.username.desc())
                    else:
                        pa = pa.order_by(User.username.asc())
                if body['order_by'] == 'id':
                    if body.get('order') == 'desc':
                        pa = pa.order_by(User.id.desc())
                    else:
                        pa = pa.order_by(User.id.asc())
        pa = pa.paginate(
            int(page), int(page_size), error_out=False
        )
        return pa.items, pa.total

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
                if body.get('confirmed') == True or body.get('confirmed') == False:
                    user_update.confirmed = body['confirmed']
                if body.get('role'):
                    user_update.role = Role.query.filter_by(
                        name=body['role']).first()
                    user_update.role_id = user_update.role.id
        else:
            return None
        db.session.commit()
        return user_update

    @staticmethod
    def delete_user(id, user_now):
        user_update = User.query.filter(User.id == id).first()
        if user_now and user_update:
            if user_now.role.permission == Permission.ADMIN:
                record = user_update.to_json()
                db.session.delete(user_update)
                db.session.commit()
                return record
        else:
            return None


class Equipment(db.Model):
    __tablename__ = 'equipments'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    owner_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'))
    status = db.Column('status', db.String(
        64), default=EquipmentStatus.UNREVIEWED)
    name = db.Column('name', db.String(64))
    usage = db.Column('usage', db.String(64))
    borrow_applications = db.relationship(
        'EquipmentBorrowApplication', backref='equipment', lazy='dynamic', cascade="all,delete")
    confirmed_back = db.Column('comfirmed_back', db.Boolean, default=True)
    current_application_id = db.Column('current_application_id', db.Integer)
    puton_applications = db.relationship(
        'EquipmentPutOnApplication', backref='equipment', lazy='dynamic', cascade='all,delete')

    def to_json(self):
        json_equipment = {
            'id': self.id,
            'status': self.status,
            'name': self.name,
            'owner': {
                'lab_name': self.owner.lab_name,
                'lab_location': self.owner.lab_location,
                'email': self.owner.email,
                'username': self.owner.username,
                'id': self.owner_id
            },
            'usage': self.usage,
            'confirmed_back': self.confirmed_back
        }
        current_application = {} if self.current_application_id else None
        if self.current_application_id:
            application = EquipmentBorrowApplication.query.filter_by(
                id=self.current_application_id).first()
            current_application['id'] = self.current_application_id
            current_application['candidate_id'] = application.candidate_id
        json_equipment["current_application"] = current_application
        return json_equipment

    @staticmethod
    def insert_equipment(owner_id, name, usage):
        equipment = Equipment(owner_id=owner_id, name=name, usage=usage)
        equipment.status = EquipmentStatus.UNREVIEWED
        db.session.add(equipment)
        db.session.commit()
        return equipment

    @staticmethod
    def search_equipments(user_now, body):
        if user_now:
            equipments = Equipment.query
            if body.get('current_candidate_id'):
                candidate_id = int(body['current_candidate_id'])
                for x in equipments.all():
                    user_id = -1
                    user = EquipmentBorrowApplication.query.filter_by(
                        id=x.current_application_id).first()
                    if user is not None:
                        user_id = user.candidate_id
                    if user_id != candidate_id:
                        equipments = equipments.filter(Equipment.id != x.id)
            if body.get('name'):
                equipments = equipments.filter(
                    Equipment.name.contains(body['name']))
            if body.get('lab_location'):
                equipments = equipments.filter(
                    Equipment.lab_location.contains(body['lab_location']))
            if body.get('status'):
                equipments = equipments.filter(
                    Equipment.status == body['status'])
            if body.get('owner_id'):
                equipments = equipments.filter(
                    Equipment.owner_id == body['owner_id'])
            if body.get('order'):
                if body.get('order_by'):
                    if body['order_by'] == 'name':
                        if body.get('order') == 'desc':
                            equipments = equipments.order_by(
                                Equipment.name.desc())
                        else:
                            equipments = equipments.order_by(
                                Equipment.name.asc())
                    if body['order_by'] == 'id':
                        if body.get('order') == 'desc':
                            equipments = equipments.order_by(
                                Equipment.id.desc())
                        else:
                            equipments = equipments.order_by(
                                Equipment.id.asc())
            page = int(body['page'])+1 if body.get('page') else 1
            page_size = int(body['page_size']) if body.get('page_size') else 10
            pa = equipments.paginate(
                page, page_size, error_out=False
            )
            return pa.items, pa.total
        else:
            return None

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
                if body.get('confirmed_back') == True:
                    equipment.confirmed_back = True
                    equipment.status = EquipmentStatus.IDLE
                db.session.commit()
                return equipment
            else:
                if equipment:
                    borrower = EquipmentBorrowApplication.query.filter_by(
                        id=equipment.current_application_id).first().candidate
                    if borrower.id == user_now.id:
                        equipment.current_application_id = None
                        db.session.commit()
                        return equipment
                return None
        else:
            return None

    @staticmethod
    def delete_equipment(id, user_now):
        equipment = Equipment.query.filter(Equipment.id == id).first()
        if user_now and equipment:
            if user_now.role.permission == Permission.ADMIN or \
                    equipment.owner_id == user_now.id:
                record = equipment.to_json()
                db.session.delete(equipment)
                db.session.commit()
                return record
        return None


class LenderApplication(db.Model):
    __tablename__ = 'lender_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'))
    lab_name = db.Column('lab_name', db.String(64))
    lab_location = db.Column('lab_location', db.String(64))
    status = db.Column('status', db.String(
        64), default=ApplicationStatus.UNREVIEWED)
    application_time = db.Column('application_time', db.DateTime)
    review_time = db.Column('review_time', db.DateTime)

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
            },
            'application_time': self.application_time.timestamp()*1000,
            'review_time': self.review_time.timestamp()*1000 if self.review_time else None
        }
        return json_lenderApplication

    @staticmethod
    def insert_lender_application(body):
        candidate_id = body.get('candidate_id')
        lab_name = body.get('lab_name')
        lab_location = body.get('lab_location')
        application = LenderApplication(candidate_id=candidate_id,
                                        lab_name=lab_name, lab_location=lab_location, application_time=datetime.now())
        candidate = User.query.filter_by(id=candidate_id).first()
        candidate.lab_name = lab_name
        candidate.lab_location = lab_location

        db.session.add(application)
        db.session.commit()
        notification = Notification(type=ApplicationType.APPLY_LENDER, sender_id=candidate_id,
                                    receiver_id=User.get_admin().id, application_id=application.id)
        db.session.add(notification)
        db.session.commit()
        return application

    @staticmethod
    def on_changed_status(target, value, oldvalue, initiator):
        target.review_time = datetime.now()
        if(value == ApplicationStatus.AGREE):
            User.update_userinfo(target.candidate_id, User.get_admin(), {
                'role': 'lender'
            })
        notification = Notification(type=ApplicationType.APPLY_LENDER, sender_id=User.get_admin(
        ).id, receiver_id=target.candidate_id, application_id=target.id)
        db.session.add(notification)
        db.session.commit()

    @staticmethod
    def get_application(user_now, body):
        applications = LenderApplication.query
        if user_now:
            if user_now.role.permission == Permission.ADMIN:
                pass
            else:
                applications = applications.filter(
                    LenderApplication.candidate_id == user_now.id)
            if body.get('status'):
                applications = applications.filter(
                    LenderApplication.status == body['status'])
            if body.get('candidate_id'):
                applications = applications.filter(
                    LenderApplication.candidate_id == body['candidate_id'])
            if body.get('reviewer_id'):
                applications = applications.filter(
                    LenderApplication.reviewer_id == body['reviewer_id'])
            if body.get('order'):
                if body.get('order_by'):
                    if body['order_by'] == 'application_time':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                LenderApplication.application_time.desc())
                        else:
                            applications = applications.order_by(
                                LenderApplication.application_time.asc())
                    if body['order_by'] == 'id':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                LenderApplication.id.desc())
                        else:
                            applications = applications.order_by(
                                LenderApplication.id.asc())
            page = int(body['page'])+1 if body.get('page') else 1
            page_size = int(body['page_size']) if body.get('page_size') else 10

            pa = applications.paginate(
                page, page_size, error_out=False
            )
            return pa.items, pa.total
        return None

    @staticmethod
    def update_application(id, user_now, body):
        if user_now:
            application = LenderApplication.query.filter(
                LenderApplication.id == id).first()
            application.status = body.get('status')
            db.session.commit()
            return application
        return None

    @staticmethod
    def delete_application(id, user_now):
        if user_now.id == User.get_admin().id:
            application = LenderApplication.query.filter_by(id=id).first()
            if application is None:
                return None
            res = application.to_json()
            db.session.delete(application)
            Notification.query.filter_by(
                type='lender', application_id=id).delete()
            db.session.commit()
            return res
        else:
            return None

    @staticmethod
    def on_delete(mapper, connection, target):
        print(target)
        Notification.query.filter_by(
            type='lender', application_id=target.id).delete()
        # db.session.commit()


db.event.listen(LenderApplication, 'before_delete',
                LenderApplication.on_delete)

db.event.listen(LenderApplication.status, 'set',
                LenderApplication.on_changed_status)


class EquipmentPutOnApplication(db.Model):
    __tablename__ = 'equipemnt_puton_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column(db.Integer, db.ForeignKey(
        'users.id'))
    equipment_id = db.Column(db.Integer, db.ForeignKey(
        'equipments.id'))
    application_time = db.Column('application_time', db.DateTime)
    status = db.Column('status', db.String(
        64), default=ApplicationStatus.UNREVIEWED)
    review_time = db.Column('review_time', db.DateTime)
    # reviewer_id = db.Column(db.Integer, db.ForeignKey(
    #     'users.id', ondelete='cascade'))
    # TODO:

    # reviewer = db.relationship(
    #     'User', backref='review_puton_applications', lazy='select', foreign_keys=[reviewer_id])

    def to_json(self):
        json_equipmentBorrowApplication = {
            'id': self.id,
            'status': self.status,
            'equipment': {
                'id': self.equipment_id,
                'name': Equipment.query.filter_by(id=self.equipment_id).first().name,
                'usage': Equipment.query.filter_by(id=self.equipment_id).first().usage
            },
            'application_time': self.application_time.timestamp()*1000,
            'review_time': self.review_time.timestamp()*1000 if self.review_time else None,
            'candidate': {
                'username': self.candidate.username,
                'email': self.candidate.email,
                'avatar': self.candidate.avatar,
                'id': self.candidate_id,
                'lab_name': self.candidate.lab_name,
                'lab_location': self.candidate.lab_location
            }
        }
        return json_equipmentBorrowApplication

    @staticmethod
    def insert_equipment_puton_application(body):
        candidate_id = body.get('candidate_id')
        usage = body.get('usage')
        name = body.get('name')
        equipment_id = body.get('equipment_id')
        equipment = Equipment.query.filter_by(id=equipment_id).first()
        if equipment is None or equipment.status != EquipmentStatus.REFUSED:
            equipment = Equipment.insert_equipment(candidate_id, name, usage)
        application = EquipmentPutOnApplication(candidate_id=candidate_id,
                                                application_time=datetime.now(),
                                                equipment_id=equipment.id)
        equipment.status = EquipmentStatus.UNREVIEWED
        db.session.add(application)
        db.session.commit()
        notification = Notification(type=ApplicationType.APPLY_PUTON, sender_id=candidate_id,
                                    receiver_id=User.get_admin().id, application_id=application.id)
        db.session.add(notification)
        db.session.commit()
        return application

    @staticmethod
    def on_changed_status(target, value, oldvalue, initiator):
        target.review_time = datetime.now()
        if value == ApplicationStatus.AGREE:
            equipment = Equipment.query.filter_by(
                id=target.equipment_id).first()
            equipment.status = EquipmentStatus.IDLE
            db.session.commit()
        if value == ApplicationStatus.REFUSE:
            equipment = Equipment.query.filter_by(
                id=target.equipment_id).first()
            equipment.status = EquipmentStatus.REFUSED
        notification = Notification(type=ApplicationType.APPLY_PUTON, sender_id=User.get_admin(
        ).id, receiver_id=target.candidate_id, application_id=target.id)
        db.session.add(notification)
        db.session.commit()

    @staticmethod
    def get_application(user_now, body):
        if user_now:
            if user_now.role.permission == Permission.ADMIN:
                applications = EquipmentPutOnApplication.query
            else:
                applications = EquipmentPutOnApplication.query.filter(
                    EquipmentPutOnApplication.candidate_id == user_now.id)
            if body.get('status'):
                applications = applications.filter(
                    EquipmentPutOnApplication.status == body['status'])
            if body.get('candidate_id'):
                applications = applications.filter(
                    EquipmentPutOnApplication.candidate_id == body['candidate_id'])
            # if body.get('reviewer_id'):
            #     applications = applications.filter(
            #         EquipmentPutOnApplication.reviewer_id == body['reviewer_id'])
            if body.get('order'):
                if body.get('order_by'):
                    if body['order_by'] == 'application_time':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                EquipmentPutOnApplication.application_time.desc())
                        else:
                            applications = applications.order_by(
                                EquipmentPutOnApplication.application_time.asc())
                    if body['order_by'] == 'id':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                EquipmentPutOnApplication.id.desc())
                        else:
                            applications = applications.order_by(
                                EquipmentPutOnApplication.id.asc())
            page = int(body['page'])+1 if body.get('page') else 1
            page_size = int(body['page_size']) if body.get('page_size') else 10
            pa = applications.paginate(
                page, page_size, error_out=False
            )
            return pa.items, pa.total
        return None

    @staticmethod
    def update_application(id, user_now, body):
        if user_now:
            application = EquipmentPutOnApplication.query.filter(
                EquipmentPutOnApplication.id == id).first()
            application.status = body.get('status')
            db.session.commit()
            return application
        return None

    @staticmethod
    def delete_application(id, user_now):
        if user_now.id == User.get_admin().id:
            application = EquipmentPutOnApplication.query.filter_by(
                id=id).first()
            if application is None:
                return None
            res = application.to_json()
            db.session.delete(application)
            Notification.query.filter_by(
                type='puton', application_id=id).delete()
            db.session.commit()
            return res
        else:
            return None

    @staticmethod
    def on_delete(mapper, connection, target):
        print(target)
        Notification.query.filter_by(
            type='puton', application_id=target.id).delete()
        print(target)
        # db.session.commit()


db.event.listen(EquipmentPutOnApplication, 'before_delete',
                EquipmentPutOnApplication.on_delete)

db.event.listen(EquipmentPutOnApplication.status, 'set',
                EquipmentPutOnApplication.on_changed_status)


class EquipmentBorrowApplication(db.Model):
    __tablename__ = 'equipment_borrow_applications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    candidate_id = db.Column('candidate_id', db.ForeignKey(
        'users.id'))

    return_time = db.Column('return_time', db.DateTime)
    usage = db.Column('usage', db.String(64))

    equipment_id = db.Column(db.Integer, db.ForeignKey(
        'equipments.id'))

    application_time = db.Column('application_time', db.DateTime)
    status = db.Column('status', db.String(
        64), default=ApplicationStatus.UNREVIEWED)
    review_time = db.Column('review_time', db.DateTime)
    reviewer_id = db.Column('reviewer_id', db.Integer,
                            db.ForeignKey('users.id'))

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
            'equipment': {
                'id': self.equipment_id,
                'name': Equipment.query.filter_by(id=self.equipment_id).first().name,
                'usage': Equipment.query.filter_by(id=self.equipment_id).first().usage
            },
            'usage': self.usage,
            'application_time': self.application_time.timestamp()*1000,
            'review_time': self.review_time.timestamp()*1000 if self.review_time else None,
            'candidate': {
                'username': self.candidate.username,
                'email': self.candidate.email,
                'avatar': self.candidate.avatar,
                'id': self.candidate_id
            }
        }
        return json_equipmentBorrowApplication

    @staticmethod
    def insert_equipment_borrow_application(body):
        candidate_id = body.get('candidate_id')
        equipment_id = body.get('equipment_id')
        return_time = datetime.fromtimestamp(body.get('return_time')/1000)
        usage = body.get('usage')
        equipment = Equipment.query.filter_by(id=equipment_id).first()
        application = EquipmentBorrowApplication(
            equipment_id=equipment_id, return_time=return_time,
            usage=usage, application_time=datetime.now(),
            reviewer_id=equipment.owner_id, candidate_id=candidate_id)
        db.session.add(application)
        db.session.commit()
        notification1 = Notification(type=ApplicationType.APPLY_BORROW, sender_id=candidate_id,
                                     receiver_id=equipment.owner_id, application_id=application.id)
        db.session.add(notification1)
        notification2 = Notification(type=ApplicationType.APPLY_BORROW, sender_id=candidate_id,
                                     receiver_id=User.get_admin().id, application_id=application.id)
        db.session.add(notification2)
        db.session.commit()
        return application

    @staticmethod
    def on_changed_status(target, value, oldvalue, initiator):
        notification = Notification(type=ApplicationType.APPLY_BORROW, sender_id=target.reviewer_id,
                                    receiver_id=target.candidate_id, application_id=target.id)
        db.session.add(notification)
        db.session.commit()
        if value == ApplicationStatus.AGREE:
            equipment = Equipment.query.filter_by(
                id=target.equipment_id).first()
            equipment.confirmed_back = False
            equipment.current_application_id = target.id
            equipment.status = EquipmentStatus.LEASE

    @staticmethod
    def get_application(user_now, body):
        if user_now:
            if user_now.role.permission == Permission.ADMIN:
                applications = EquipmentBorrowApplication.query
            else:
                if user_now.role.permission == Permission.LENDER:
                    applications = EquipmentBorrowApplication.query.filter(
                        EquipmentBorrowApplication.reviewer_id == user_now.id)
                else:
                    applications = EquipmentBorrowApplication.query.filter(
                        EquipmentBorrowApplication.candidate_id == user_now.id)

            if body.get('status'):
                applications = applications.filter(
                    EquipmentBorrowApplication.status == body['status'])
            if body.get('candidate_id'):
                applications = applications.filter(
                    EquipmentBorrowApplication.candidate_id == body['candidate_id'])
            if body.get('reviewer_id'):
                applications = applications.filter(
                    EquipmentBorrowApplication.reviewer_id == body['reviewer_id'])
            if body.get('order'):
                if body.get('order_by'):
                    if body['order_by'] == 'application_time':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                EquipmentBorrowApplication.application_time.desc())
                        else:
                            applications = applications.order_by(
                                EquipmentBorrowApplication.application_time.asc())
                    if body['order_by'] == 'id':
                        if body.get('order') == 'desc':
                            applications = applications.order_by(
                                EquipmentBorrowApplication.id.desc())
                        else:
                            applications = applications.order_by(
                                EquipmentBorrowApplication.id.asc())
            page = int(body['page'])+1 if body.get('page') else 1
            page_size = int(body['page_size']) if body.get('page_size') else 10
            pa = applications.paginate(
                page, page_size, error_out=False
            )
            return pa.items, pa.total
        return None

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
        return None

    @staticmethod
    def delete_application(id, user_now):
        if user_now.id == User.get_admin().id:
            application = EquipmentBorrowApplication.query.filter_by(
                id=id).first()
            if application is None:
                return None
            res = application.to_json()
            db.session.delete(application)
            Notification.query.filter_by(
                type='borrow', application_id=id).delete()
            db.session.commit()
            return res
        else:
            return None

    @staticmethod
    def on_delete(mapper, connection, target):
        print(target)
        Notification.query.filter_by(
            type='borrow', application_id=target.id).delete()
        print(target)
        # db.session.commit()


db.event.listen(EquipmentBorrowApplication, 'before_delete',
                EquipmentBorrowApplication.on_delete)

db.event.listen(EquipmentBorrowApplication.status, 'set',
                EquipmentBorrowApplication.on_changed_status)


class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column('id', db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column('sender_id', db.Integer,
                          db.ForeignKey('users.id'))
    receiver_id = db.Column('receiver_id', db.Integer,
                            db.ForeignKey('users.id'))
    content = db.Column('content', db.String(64))
    notification_time = db.Column('notification_time', db.DateTime)
    isRead = db.Column('isRead', db.Boolean, default=False)
    type = db.Column('type', db.String(64))
    application_id = db.Column('application_id', db.Integer)

    def __init__(self, **kwargs):
        super(Notification, self).__init__(**kwargs)
        self.notification_time = datetime.now()

        if self.type == ApplicationType.APPLY_LENDER:
            application = LenderApplication.query.filter_by(
                id=self.application_id).first()
            if application.status == ApplicationStatus.UNREVIEWED:
                self.content = NotificationContent.APPLICATION_APPLY_MESSAGE.format(type='Lender Application', id=self.application_id,
                                                                                    user_id=self.sender_id, username=User.query.filter_by(id=self.sender_id).first().username)
            if application.status == ApplicationStatus.REFUSE:
                self.content = NotificationContent.APPLICATION_REFUSE_MESSAGE.format(type='Lender Application', reviewer_id=self.sender_id,
                                                                                     reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)
            if application.status == ApplicationStatus.AGREE:
                self.content = NotificationContent.APPLICATION_AGREE_MESSAGE.format(type='Lender Application', reviewer_id=self.sender_id,
                                                                                    reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)

        if self.type == ApplicationType.APPLY_PUTON:
            application = EquipmentPutOnApplication.query.filter_by(
                id=self.application_id).first()
            if application.status == ApplicationStatus.UNREVIEWED:
                self.content = NotificationContent.APPLICATION_APPLY_MESSAGE.format(type='Equipment Puton Application', id=self.application_id,
                                                                                    user_id=self.sender_id, username=User.query.filter_by(id=self.sender_id).first().username)
            if application.status == ApplicationStatus.REFUSE:
                self.content = NotificationContent.APPLICATION_REFUSE_MESSAGE.format(type='Equipment Puton Application', reviewer_id=self.sender_id,
                                                                                     reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)
            if application.status == ApplicationStatus.AGREE:
                self.content = NotificationContent.APPLICATION_AGREE_MESSAGE.format(type='Equipment Puton Application', reviewer_id=self.sender_id,
                                                                                    reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)

        if self.type == ApplicationType.APPLY_BORROW:
            application = EquipmentBorrowApplication.query.filter_by(
                id=self.application_id).first()
            if application.status == ApplicationStatus.UNREVIEWED:
                self.content = NotificationContent.APPLICATION_APPLY_MESSAGE.format(type='Equipment Borrow Application', id=self.application_id,
                                                                                    user_id=self.sender_id, username=User.query.filter_by(id=self.sender_id).first().username)
            if application.status == ApplicationStatus.REFUSE:
                self.content = NotificationContent.APPLICATION_REFUSE_MESSAGE.format(type='Equipment Borrow Application', reviewer_id=self.sender_id,
                                                                                     reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)
            if application.status == ApplicationStatus.AGREE:
                self.content = NotificationContent.APPLICATION_AGREE_MESSAGE.format(type='Equipment Borrow Application', reviewer_id=self.sender_id,
                                                                                    reviewer_name=User.query.filter_by(id=self.sender_id).first().username, review_time=self.notification_time)

    def to_json(self):
        application = None
        if self.type == ApplicationType.APPLY_BORROW:
            application = EquipmentBorrowApplication.query.filter(
                EquipmentBorrowApplication.id == self.application_id
            ).first()
        if self.type == ApplicationType.APPLY_LENDER:
            application = LenderApplication.query.filter(
                LenderApplication.id == self.application_id
            ).first()
        if self.type == ApplicationType.APPLY_PUTON:
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
            'notification_time': self.notification_time.timestamp()*1000,
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
            notifications = Notification.query.filter(
                Notification.receiver_id == user_now.id)
            if body.get('isRead'):
                isRead = True if body['isRead'] == 'true' else False
                notifications = notifications.filter(
                    Notification.isRead == isRead)
            order = body.get('order')
            if order == 'asc':
                order_by = body.get('order_by')
                if order_by == 'id':
                    notifications = notifications.order_by(
                        Notification.id.asc())
                if order_by == 'notification_time':
                    notifications = notifications.order_by(
                        Notification.id.asc())
            if order == 'desc':
                order_by = body.get('order_by')
                if order_by == 'id':
                    notifications = notifications.order_by(
                        Notification.id.desc())
                if order_by == 'notification_time':
                    notifications = notifications.order_by(
                        Notification.id.desc())

            page = int(body['page'])+1 if body.get('page') else 1
            page_size = int(body['page_size']) if body.get('page_size') else 10
            pa = notifications.paginate(
                page, page_size, error_out=False
            )
            if body.get('total') == 'true':
                return [], pa.total
            return pa.items, pa.total
        return None

    @staticmethod
    def update_notification(id, user_now, body):
        if user_now:
            notification = Notification.query.filter(
                Notification.id == id).first()
            if notification is not None:
                notification.isRead = body.get('isRead') or notification.isRead
                db.session.commit()
                return notification.to_json()
        return None

    @staticmethod
    def delete_notification(id, user_now):
        if user_now:
            notification = Notification.query.filter(
                Notification.id == id).first()
            if notification is not None:
                res = notification.to_json()
                db.session.delete(notification)
                db.session.commit()
                return res
        return None
