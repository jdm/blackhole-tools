import ConfigParser
from mozillapulse.consumers import MalformedMessage
from pymongo import MongoClient

def normalize_data(who, when, source, extra):
    return {'email': who,
            'datetime': when,
            'source': source,
            'extra': extra}

DEFAULT_CONFIG = "config"

class MongoConnection(object):
    def __init__(self, dbname, configfilename=None):
        config = ConfigParser.RawConfigParser()
        config.read(configfilename or DEFAULT_CONFIG)
        host = port = None
        try:
            host = config.get('mongo', 'host')
        except:
            host = None
        try:
            port = config.get('mongo', 'post')
        except:
            port = None

        self.client = MongoClient(host=host, port=port)
        self.db = self.client[dbname]

    def add_contribution(self, who, when, source, extra):
        data = normalize_data(who, when, source, extra)
        self.db.contributions.insert(data)

    def add_entrypoint(self, who, when, source, extra):
        data = normalize_data(who, when, source, extra)
        self.db.entrypoints.insert(data)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.client.disconnect()
