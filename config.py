import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = os.getenv('SECRET_KEY') or "hard to guess"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    FLASK_ADMIN = os.getenv('FLASK_ADMIN') or 'fake@example.com'
    FLASKY_MAIL_SUBJECT_PREFIX = 'Equipment Leasing Team'
    MAIL_SERVER = 'smtp.qq.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_PASSWORD = '123456'
    MAIL_USERNAME = 'fake@example.com'

    @staticmethod
    def init_app(app):
        pass


class Development(Config):
    ENV = 'development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data-dev.sqlite')


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data-test.sqlite')


class ProductionConfig(Config):
    ENV = 'production'
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data-prod.sqlite')
    # SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")


config = {
    'development': Development,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': Development
}
