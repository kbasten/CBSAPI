from flask import Flask, g
import pymysql

from cbsapi.api_blueprint import api_bp

app = Flask('CBS_API')

app.config.from_object('cbsapi.config')

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
