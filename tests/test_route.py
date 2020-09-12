import unittest
import json
import re
from base64 import b64encode
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
                         username="fake", password="fake")
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

    def test_404(self):
        response = self.client.get(
            '/wrong/url',
            headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 404)

    

    
