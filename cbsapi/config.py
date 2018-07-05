import os

import yaml


def mk_conf_from_file(file):
    with open(file, 'r') as f:
        conf = yaml.load(f)

    def get_config(which, default):
        return default if which not in conf else conf[which]

    return mk_conf(get_config)


def mk_conf_from_env():
    return mk_conf(os.getenv)


def mk_conf(func):
    class CONF:
        FLASK = {
            'host': func('CBSAPI_HOST', '127.0.0.1'),
            'port': int(func('CBSAPI_PORT', 5000)),
            # first we convert into int, because bool('0') is True, as the string is nonempty
            'debug': bool(int(func('CBSAPI_DEBUG', 0)))  # Use 1 for True 0 for False
        }

        DATABASE = {
            'host': func('CBSAPI_DB_HOST', '127.0.0.1'),
            'user': func('CBSAPI_DB_USER', 'callersbane'),
            'password': func('CBSAPI_DB_PASSWORD', 'callersbane'),
            'db': func('CBSAPI_DB_DATABASE', 'scrolls')
        }

    return CONF
