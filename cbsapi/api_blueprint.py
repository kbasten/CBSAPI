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
            abort(500, description=None)

    return wrapper


@api_bp.errorhandler(HTTPException)
def http_exception(e: HTTPException) -> Response:
    """
    Error handler for http exceptions raised through flask.abort,
    so that they could be served as JSON
    """
    # TODO weirdly this is catching more than just HTTPExceptions, so description and code weren't always present
    response = jsonify({'status': 'ERROR', 'description': getattr(e, 'description', str(e))})
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

    Returned data:

        {
            name: string                        # nickname
            rating: float                       # display rating (not hidden)
            gold: int                           # gold owned
            last_login: timestamp               # last login, can be null
            created: timestamp                  # When was the account created
            achievements_unlocked: int          # How many achievements did the player unlock,
            cosmetic_unlocks: {
                avatar_pieces: int              # How many unlockable avatar pieces the player has unlocked
                idols: int                      # How many unlockable idols the player has unlocked
            }
            avatar: {
                head: int                       # id of the player's head avatar piece, can be null
                body: int                       # id of the player's body avatar piece, can be null
                legs: int                       # id of the player's legs avatar piece, can be null
                arms_back: int                  # id of the player's arms back avatar piece, can be null
                arms_front: int                 # id of the player's arms front avatar piece, can be null
            }
            collection: {
                commons: int                    # number of owned common cards
                uncommons: int                  # number of owned uncommon cards
                rares: int                      # number of owned rare cards
            }
        }
    """
    name = name.lower()
    with g.db.cursor() as cursor:
        cursor.execute(
            """
            SELECT p.name                                                             AS name,
                   pd.alpha_ranked * pd.real_ranked                                   AS rating,
                   pd.gold                                                            AS gold,
                   p.login_date                                                       AS last_login,
                   p.created                                                          AS created,
                   (SELECT COUNT(*) FROM achievement_unlocks WHERE profile_id = p.id) AS achievements_unlocked,
                   (SElECT COUNT(*) FROM avatar_unlocks WHERE profile_id = p.id)      AS avatar_unlocked,
                   (SELECT COUNT(*) FROM idol_unlocks WHERE profile_id = p.id)        AS idols_unlocked,
                   a.head                                                             AS avatar_head,
                   a.body                                                             AS avatar_body,
                   a.leg                                                              AS avatar_legs,
                   a.arm_back                                                         AS arm_back,
                   a.arm_front                                                        AS arm_front,
                   cc.commons                                                         AS commons,
                   cc.uncommons                                                       AS uncommons,
                   cc.rares                                                           AS rares
            FROM profiles p
                   INNER JOIN profile_data pd ON pd.profile_id = p.id
                   LEFT JOIN avatars a ON a.profile_id = p.id
                   LEFT JOIN (SELECT owner_id,
                                     CAST(SUM(ct.rarity = 0) AS UNSIGNED) AS commons,
                                     CAST(SUM(ct.rarity = 1) AS UNSIGNED) AS uncommons,
                                     CAST(SUM(ct.rarity = 2) AS UNSIGNED) AS rares
                              FROM cards c
                                     INNER JOIN card_types ct ON c.type_id = ct.id
                              GROUP BY owner_id) AS cc ON cc.owner_id = p.id
            WHERE p.name = %s;""",
            name
        )
        player_data = cursor.fetchone()
        transformed_data = dict(
            name=player_data['name'],
            rating=player_data['rating'],
            gold=player_data['gold'],
            last_login=player_data['last_login'].timestamp() if player_data['last_login'] else player_data['last_login'],
            created=player_data['created'].timestamp(),
            achievements=player_data['achievements_unlocked'],
            cosmetics_unlocks=dict(
                avatar_pieces=player_data['avatar_unlocked'],
                idols=player_data['idols_unlocked']
            ),
            avatar=dict(
                head=player_data['avatar_head'],
                body=player_data['avatar_body'],
                legs=player_data['avatar_legs'],
                arm_back=player_data['arm_back'],
                arm_front=player_data['arm_front'],
            ),
            collection=dict(
                commons=player_data['commons'],
                uncommons=player_data['uncommons'],
                rares=player_data['rares']
            )
        )
        return transformed_data
