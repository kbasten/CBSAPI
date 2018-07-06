from functools import wraps

from flask import Blueprint, g, jsonify, abort, Response, request
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
            abort(500, description=None)

    return wrapper


@api_bp.errorhandler(HTTPException)
def http_exception(e: HTTPException) -> Response:
    """
    Error handler for http exceptions raised through flask.abort,
    so that they could be served as JSON
    """
    response = {
        'status': 'ERROR',
        'description': 'Internal server error'
    }
    if isinstance(e, HTTPException):
        response['description'] = getattr(e, 'description', str(e))

    response = jsonify(response)
    response.status_code = getattr(e, 'code', 500)

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


@api_bp.route('/player/<string:name>')
@default_status_response
def player(name):
    """
    Gets information about a player by their name

    To get more than just the basic data, user list of arguments (RFC6570)

    Available filters: avatar, unlocks, collection, games

    e.g.: `/player/Robot?filter=avatar&filter=unlocks&filter=cards&filter=games` would return::

        {
            "data": {
                "avatar": {                                 # avatar can be null if the player didn't
                    "head": 22,                             # login yet, otherwise has ids of avatar pieces
                    "body": 8,
                    "legs": 39,
                    "arm_back": 1,
                    "arm_front": 15
                },
                "created": 1403697353,                      # timestamp of user registration
                "games": {
                    "lost": 0
                    "won": 2
                },
                "last_login": null,                         # timestamp of last login or null
                "name": "Robot",
                "rating": 0.0036600898738470278,            # player's displayed rating
                "unlocks": {
                    "achievements": 0,
                    "avatar_pieces": 0,
                    "idols": 0
                }
            },
            "status": "OK"
        }
    """
    filters = request.args.getlist('filter')
    with g.db.cursor() as cursor:
        # Select basic data from the profiles table
        cursor.execute("""
        SELECT name, id, created, login_date AS last_login
        FROM profiles
        WHERE LOWER(name) = %s
        """, name)
        result = cursor.fetchone()

        if result is None:
            abort(404, description="Player not found")

        user_id = result.pop('id')
        # Convert datetime to timestamps
        result['created'] = result['created'].timestamp()
        if result['last_login'] is not None:
            result['last_login'] = result['last_login'].timestamp()

        cursor.execute("""
        SELECT gold, alpha_ranked * real_ranked AS rating
        FROM profile_data
        WHERE profile_id = %s
        """, user_id)
        result.update(cursor.fetchone())

        if 'avatar' in filters:
            cursor.execute("""
            SELECT head, body, leg AS legs, arm_back, arm_front
            FROM avatars
            WHERE profile_id = %s
            """, user_id)
            result['avatar'] = cursor.fetchone()

        if 'unlocks' in filters:
            cursor.execute("""
            SELECT 
                (SELECT COUNT(*) FROM achievement_unlocks WHERE profile_id = %s)    AS achievements,
                (SELECT COUNT(*) FROM avatar_unlocks WHERE profile_id = %s)         AS avatar_pieces,
                (SELECT COUNT(*) FROM idol_unlocks WHERE profile_id = %s)           AS idols
            """, (user_id, user_id, user_id))
            result['unlocks'] = cursor.fetchone()

        if 'collection' in filters:
            cursor.execute("""
            SELECT 
                CAST(SUM(ct.rarity = 0) AS UNSIGNED)    AS commons,
                CAST(SUM(ct.rarity = 1) AS UNSIGNED)    AS uncommons,
                CAST(SUM(ct.rarity = 2) AS UNSIGNED)    AS rares
            FROM cards c
                JOIN card_types ct on c.type_id = ct.id
            WHERE c.owner_id = %s
            """, user_id)
            result['collection'] = cursor.fetchone()

        if 'games' in filters:
            cursor.execute("""
            SELECT 
                CAST(SUM(win=1) AS UNSIGNED)    AS won,
                CAST(SUM(win=0) AS UNSIGNED)    AS lost
            FROM game_player_stats
            WHERE profile_id = %s
            """, user_id)
            result['games'] = cursor.fetchone()

    return result
