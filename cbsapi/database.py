import logging
from threading import Lock

import mysql.connector


class Database():
    def __init__(self, config):
        self.cnx = None
        self.cursor = None
        self.lock = Lock()

        # merge YAML config with some default booleans
        self.config = {**config,
            **{'raise_on_warnings': True,
            'use_pure': True
        }}

    def __enter__(self):
        self.lock.acquire()
        try:
            self.cnx = mysql.connector.connect(**self.config)
            self.cursor = self.cnx.cursor(dictionary=True)
        except Exception as e:
            logging.error("Exception on opening database:")
            logging.error(e)
        return self.cursor

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if self.cursor is not None:
                self.cursor.close()
            if self.cnx is not None:
                self.cnx.close()
        except Exception as e:
            logging.error("Exception on closing database:")
            logging.error(e)

        self.lock.release()

    def close(self):
        if self.cnx is not None:
            self.cnx.close()
