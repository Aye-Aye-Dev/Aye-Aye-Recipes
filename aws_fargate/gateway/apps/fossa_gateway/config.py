import os


class BaseConfig:
    DEBUG = False
    APP_TITLE = "Fossa gateway"
    PREFERRED_URL_SCHEME = "http"
    SECRET_KEY = ""
    HTTP_PORT = 5050


class LocalConfig(BaseConfig):
    pass


class ProdConfig(BaseConfig):
    HTTP_PORT = 80
    HTTP_USER_PASSWORD = os.environ["HTTP_USER_PASSWORD"]
