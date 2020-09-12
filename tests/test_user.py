from http.client import responses
import unittest
from app import create_app, db
from app.models import User, Role
import json


class FlaskClientTestCase(unittest.TestCase):
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

    def test_register_and_login(self):
        response = self.client.post('/api/register', headers=self.get_api_headers(None), data=json.dumps({
            'email': 'hello@example.com',
            'username': 'hello',
            'password': 'hello',
        }))
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/api/login', headers=self.get_api_headers(None), data=json.dumps({
            'username': 'hello',
            'password': 'hello'
        }))

        self.assertEqual(response.status_code, 200)

        json_response = json.loads(response.get_data(as_text=True))
        self.assertTrue(json_response.get('username') == 'hello')

        # send a confirmation token

        response = self.client.post(
            '/api/users/confirm', headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.test_user.confirmed == True)

    def test_get_user(self):
        response = self.client.get(
            '/api/users/{}'.format(self.test_user.id),
            headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], self.test_user.username)

    def test_token_auth(self):
        response = self.client.get(
            '/api/users/'+str(self.test_user.id),
            headers=self.get_api_headers(None))
        self.assertEqual(response.status_code, 401)

        response = self.client.get(
            '/api/users/'+str(self.test_user.id),
            headers=self.get_api_headers(self.test_user))
        self.assertEqual(response.status_code, 200)

    def test_no_auth(self):
        response = self.client.get('/api/users',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/equipments',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/applications/lender',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/applications/borrow',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/applications/lender',
                                   content_type='application/json')

        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/notifications',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)

        response = self.client.get('/api/messages',
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)
