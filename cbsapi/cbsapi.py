import inspect

import yaml
from flask import Flask, Response, jsonify

from cbsapi.database import Database


class EndpointAction(object):
    def __init__(self, action):
        self.action = action

    def __call__(self, *args):
        result = self.action()
        if result is not None:
            return jsonify(result)
        return Response(status=500, headers={})


class CBSAPI(object):
    def __init__(self, config_file):
        self.flask = Flask('CBS_API')

        with open(config_file, 'r') as conf:
            self.config = yaml.load(conf)

        self.db = Database(self.config['Database'])

        # get all endpoints in this class
        for endpoint in filter(lambda func: func[0].startswith('endpoint_'),
                               inspect.getmembers(self, predicate=inspect.ismethod)):
            rule, handler = endpoint[1]()
            # and add them to the list of endpoints
            self.add_endpoint(rule, handler)

    def run(self):
        self.flask.run(**self.config['Flask'])

    def add_endpoint(self, rule, handler):
        # name is equal to rule, since they are unique anyway
        self.flask.add_url_rule(rule, endpoint=rule, view_func=EndpointAction(handler))

    def endpoint_online(self):
        def online():
            with self.db as cursor:
                cursor.execute("SELECT COUNT(*) as online FROM server_profiles WHERE online_state = 'LOBBY';")
                return cursor.fetchone()

        return '/online', online

    def endpoint_blackmarket(self):
        def blackmarket():
            with self.db as cursor:
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

        return '/blackmarket', blackmarket

    def endpoint_toprankedprofiles(self):
        def toprankedprofiles():
            with self.db as cursor:
                cursor.execute("SELECT P.name, PD.alpha_ranked * PD.real_ranked AS rating "
                    "FROM profiles P "
                    "INNER JOIN profile_data PD "
                    "ON PD.profile_id = P.id "
                    "ORDER BY rating DESC "
                    "LIMIT 50")
                return cursor.fetchall()

        return '/ranking', toprankedprofiles
