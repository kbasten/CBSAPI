import os

FLASK = {
    'host': os.getenv('CBSAPI_HOST', '127.0.0.1'),
    'port': int(os.getenv('CBSAPI_PORT', 5000)),
    # first we convert into int, because bool('0') is True, as the string is nonempty
    'debug': bool(int(os.getenv('CBSAPI_DEBUG', 0)))  # Use 1 for True 0 for False
}

DATABASE = {
    'host': os.getenv('CBSAPI_DB_HOST', '127.0.0.1'),
    'user': os.getenv('CBSAPI_DB_USER', 'callersbane'),
    'password': os.getenv('CBSAPI_DB_PASSWORD', 'callersbane'),
    'db': os.getenv('CBSAPI_DB_DATABASE', 'scrolls')
}
