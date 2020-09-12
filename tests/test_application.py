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

    def test_lender_application(self):
        response = self.client.post(
            '/api/applications/lender', headers=self.get_api_headers(self.test_user), data=json.dumps({
                "lab_name": "123",
                "lab_location": "234"
            }))
        print(response.data)
        print(User.verify_auth_token(self.test_user.generate_auth_token(86400)))
        self.assertEqual(response.status_code, 200)

        # First change test_user to lender
        self.test_user.role_id = 2
        db.session.commit()
        response = self.client.post(
            '/api/applications/lender', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 400)

        response = self.client.get(
            '/api/applications/lender', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            '/api/applications/lender/1', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.put('/api/applications/lender/1', headers=self.get_api_headers(self.admin), data=json.dumps({
            "status": "agree"
        }))
        self.assertEqual(response.status_code, 200)

    def test_puton_application(self):
        self.test_user.role_id = 3
        db.session.commit()
        response = self.client.post(
            '/api/applications/puton', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 400)

        # First change test_user to lender
        self.test_user.role_id = 2
        db.session.commit()
        response = self.client.post('/api/applications/puton', headers=self.get_api_headers(self.test_user), data=json.dumps({
            "name": "123",
            "usage": "234"
        }))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            '/api/applications/puton', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            '/api/applications/puton/1', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.put('/api/applications/puton/1', headers=self.get_api_headers(self.admin), data=json.dumps({
            "status": "agree"
        }))
        self.assertEqual(response.status_code, 200)

    def test_borrow_application(self):
        self.test_user.role_id = 3
        db.session.commit()

        e = Equipment(name="123", usage="123", owner_id=self.test_user.id)
        db.session.add(e)
        db.session.commit()

        response = self.client.post(
            '/api/applications/borrow', headers=self.get_api_headers(self.test_user), data=json.dumps({
                "return_time": 15000000000,
                "usage": "123",
                "equipment_id": 1
            }))
        print(response.data)
        self.assertEqual(response.status_code, 200)

        # First change test_user to lender
        self.test_user.role_id = 2
        db.session.commit()
        response = self.client.post('/api/applications/borrow', headers=self.get_api_headers(self.test_user), data=json.dumps({
            "name": "123",
            "usage": "234",
            "equipment_id": 1
        }))
        self.assertEqual(response.status_code, 400)

        response = self.client.get(
            '/api/applications/borrow', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(
            '/api/applications/borrow/1', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

        response = self.client.put('/api/applications/borrow/1', headers=self.get_api_headers(self.test_user), data=json.dumps({
            "status": "agree"
        }))
        self.assertEqual(response.status_code, 200)
