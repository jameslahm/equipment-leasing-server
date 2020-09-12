import unittest
import json

from flask.json import jsonify
from app import create_app, db
from app.models import User, Role, Equipment, LenderApplication, EquipmentBorrowApplication, EquipmentPutOnApplication


class APITestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        admin = User(email=self.app.config["FLASK_ADMIN"],
                     password="secure", username="zhangzhi_up", confirmed=True)
        db.session.add(admin)

        test_user = User(email="fake@example.com",
                         username="fake", password="fake", confirmed=True)
        db.session.add(test_user)
        db.session.commit()
        self.client = self.app.test_client()
        self.test_user = test_user
        self.admin = admin

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def get_api_headers(self, user: User):
        return {
            'Authorization': user.generate_auth_token(86400) if user else None,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }

    def test_get_logs(self):
        response = self.client.get(
            '/api/stat', headers=self.get_api_headers(self.test_user))

        self.assertEqual(response.status_code, 401)

        response = self.client.get(
            '/api/stat', headers=self.get_api_headers(self.admin))

        self.assertEqual(response.status_code, 200)

        json_reponse = json.loads(response.get_data(as_text=True))
        expected_keys = ['total_users', 'confirmed_users',
                         'unconfirmed_users', 'normal_users', 'lender_users', 'total_equipments', 'unreviewed_equipments', 'idle_equipments', 'lease_equipments', 'lender_applications', 'equipment_puton_applications', 'borrow_log','equipment_borrow_applications']
        self.assertEqual(sorted(json_reponse.keys()), sorted(expected_keys))
