import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config():
    SECRET_KEY = os.getenv('SECRET_KEY') or "hard to guess"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = True

    @staticmethod
    def init_app(app):
        pass


class Development(Config):
    ENV='development'
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data-dev.sqlite')

class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED=False
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data-test.sqlite')

class ProductionConfig(Config):
    ENV='production'
    SQLALCHEMY_DATABASE_URI = os.path.join('sqlite:///' + basedir +
                                           '/data.sqlite')


config = {
    'development': Development,
    'testing': TestConfig,
    'production': ProductionConfig,
    'default': Development
}