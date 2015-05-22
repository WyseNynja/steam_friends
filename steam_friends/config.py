import logging


log = logging.getLogger(__name__)


class Config(object):
    CACHE_DEFAULT_TIMEOUT = 60 * 20
    CACHE_TYPE = 'simple'
    DEBUG = False
    LOGGER_NAME = 'flask'
    OPENID_FS_STORE_PATH = "/tmp/steam_friends/openid"

    # todo: remove this and revoke the key. but I'm lazy now
    STEAMODD_API_KEY = "DA0509DA52BC706F282F2D315D3C61BB"

    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DEBUG_TB_PROFILER_ENABLED = True
    SECRET_KEY = "not very secret"
    TESTING = False


class ProductionConfig(Config):
    CACHE_REDIS_PORT = '10002'
    CACHE_REDIS_HOST = '127.0.0.1'
    CACHE_TYPE = 'redis'
    DEBUG = False

    # todo: remove this and revoke the key. but I'm lazy now
    SECRET_KEY = '\xbfCN\xf6\xbfy\xde\xcb~\x19\x1b\xc5\x9dN\x0f"n\x8b\x13$S\xa5\xe7\xd3'

    SERVER_NAME = 'steam.stitthappens.com'
    TESTING = False


class TestingConfig(Config):
    SECRET_KEY = "not very secret"
    TESTING = True


configs = {
    'dev': "{}.{}".format(__name__, 'DevelopmentConfig'),
    'prod': "{}.{}".format(__name__, 'ProductionConfig'),
    'test': "{}.{}".format(__name__, 'TestingConfig'),
}
