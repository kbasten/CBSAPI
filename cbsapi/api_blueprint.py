from functools import wraps

from flask import Blueprint, g, jsonify, abort, Response
from werkzeug.exceptions import HTTPException

api_bp = Blueprint('API', 'api_bp')


def default_status_response(f):

    @wraps(f)
    def wrapper(*args, **kwargs):
        """Zavola volanou funkci, ktera vrati status, podle statusu obohati odpoved o JSON"""
        ret = f(*args, **kwargs)
        if ret:

            return jsonify({'status': 'OK', 'data': ret})
        else:
            abort(500)

    return wrapper


@api_bp.errorhandler(HTTPException)
def http_exception(e: HTTPException) -> Response:
    """
    Error handler for http exceptions raised through flask.abort,
    so that they could be served as JSON
    """
    response = jsonify({'status': 'ERROR', 'description': e.description})
    response.status_code = e.code
    return response


@api_bp.route('/online')
@default_status_response
def online():
    with g.db.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) as online FROM server_profiles WHERE online_state = 'LOBBY';")
        ret = cursor.fetchone()
    return ret


@api_bp.route('/blackmarket')
@default_status_response
def blackmarket():
    with g.db.cursor() as cursor:
        cursor.execute("SELECT MIN(moo.price) AS price, moo.level, moo.type, cat.name "
                       "FROM "
                       "(SELECT ca.level AS level, mo.price AS price, ca.type_id AS type "
                       "FROM marketplace_offers mo "
                       "LEFT JOIN cards ca "
                       "ON ca.id = mo.card_id "
                       "ORDER BY price ASC, level DESC) AS moo "
                       "LEFT JOIN card_types cat "
                       "ON moo.type = cat.id "
                       "GROUP BY moo.type, moo.level")
        return cursor.fetchall()


@api_bp.route('/ranking')
@default_status_response
def ranking():
    with g.db.cursor() as cursor:
        cursor.execute("SELECT P.name, PD.alpha_ranked * PD.real_ranked AS rating "
                       "FROM profiles P "
                       "INNER JOIN profile_data PD "
                       "ON PD.profile_id = P.id "
                       "ORDER BY rating DESC "
                       "LIMIT 50")
        return cursor.fetchall()
