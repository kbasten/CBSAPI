import sys
from flask import Flask, g
import pymysql

from cbsapi.config import mk_conf_from_file, mk_conf_from_env
from cbsapi.api_blueprint import api_bp

app = Flask('CBS_API')

if len(sys.argv) == 2:
    cfg = mk_conf_from_file(sys.argv[1])
else:
    cfg = mk_conf_from_env()

app.config.from_object(cfg)

app.register_blueprint(api_bp)


@app.before_request
def before_request():
    g.db = pymysql.connect(**app.config['DATABASE'],
                           cursorclass=pymysql.cursors.DictCursor)


@app.after_request
def after_request(response):
    g.db.close()
    return response


if __name__ == '__main__':
    app.run(**app.config['FLASK'])
