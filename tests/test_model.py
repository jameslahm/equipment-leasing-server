import unittest
import time
from app import create_app, db
from app.models import User,  Role


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    def test_no_password_getter(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    def test_password_verification(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    def test_password_salts_are_random(self):
        u = User(password='cat')
        u2 = User(password='cat')
        self.assertTrue(u.password_hash != u2.password_hash)

    def test_invalid_token(self):
        u1 = User(password='cat')
        db.session.add(u1)
        db.session.commit()
        token = u1.generate_auth_token(86400)
        self.assertFalse(User.verify_auth_token(token+"123"))

    def test_expired_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(1)
        time.sleep(2)
        self.assertFalse(u.verify_auth_token(token))

    def test_valid_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_auth_token(86400)
        self.assertTrue(User.verify_auth_token(token))

    def test_user_role(self):
        u = User(email='fake@example.com', password='cat')
        self.assertTrue(u.role.name=='normal')

    def test_moderator_role(self):
        r = Role.query.filter_by(name='lender').first()
        u = User(email='fake@example.com', password='cat', role=r)
        self.assertTrue(u.role.name=='lender')

    def test_administrator_role(self):
        r = Role.query.filter_by(name='admin').first()
        u = User(email=self.app.config["FLASK_ADMIN"], password='cat', role=r)
        self.assertTrue(u.role.name=='admin')
        self.assertTrue(User.get_admin().id == u.id)

    def test_to_json(self):
        u = User(email='fake@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = u.to_json()
        expected_keys = ['username', 'avatar',
                         'id', 'email', 'confirmed', 'role']
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
