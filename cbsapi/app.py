from flask import Flask, g
import pymysql

from api_blueprint import api

app = Flask('CBS_API')

app.config.from_object('config')

app.register_blueprint(api)


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
