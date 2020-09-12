from app.api import comments
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

    def test_get_comments(self):
        response = self.client.get(
            '/api/equipments/1/comments', headers=self.get_api_headers(self.test_user))

        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response["total"])

    def test_create_and_delete_comment(self):
        response = self.client.post(
            '/api/equipments/1/comments', headers=self.get_api_headers(self.test_user), data=json.dumps({
                "content": "123"
            }))

        self.assertEqual(response.status_code, 400)

        self.test_user.role_id = 2
        e = Equipment(name="123", owner_id=self.test_user.id)
        db.session.add(e)
        db.session.commit()

        response = self.client.post(
            '/api/equipments/1/comments', headers=self.get_api_headers(self.test_user), data=json.dumps({
                "content": "123",
                "rating":5
            }))

        self.assertEqual(response.status_code, 200)

        response = self.client.delete(
            '/api/equipments/1/comments/1', headers=self.get_api_headers(self.test_user))

        self.assertEqual(response.status_code, 200)
