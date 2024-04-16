import os


class BaseConfig:
    DEBUG = False
    APP_TITLE = "Fossa gateway"
    PREFERRED_URL_SCHEME = "http"
    SECRET_KEY = ""
    HTTP_PORT = 5050

    # Where to find the HTTP service from Fossa
    FOSSA_NODE_PORT = 2345


class LocalConfig(BaseConfig):
    DEBUG = True
    HTTP_USER_PASSWORD = "supersecret"


class ProdConfig(BaseConfig):
    HTTP_PORT = 80
    HTTP_USER_PASSWORD = os.environ.get("HTTP_USER_PASSWORD")
