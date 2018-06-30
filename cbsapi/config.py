import os

FLASK = {
    'host': os.getenv('CBSAPI_HOST', '127.0.0.1'),
    'port': int(os.getenv('CBSAPI_PORT', 5000)),
    'debug': bool(os.getenv('CBSAPI_DEBUG', 0))
}

DATABASE = {
    'host': os.getenv('CBSAPI_DB_HOST', '127.0.0.1'),
    'user': os.getenv('CBSAPI_DB_USER', 'callersbane'),
    'password': os.getenv('CBSAPI_DB_PASSWORD', 'callersbane'),
    'db': os.getenv('CBSAPI_DB_DATABASE', 'scrolls')
}
