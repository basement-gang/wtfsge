import plyvel
import simplejson as json
from main import Gathering

class TestMain:
    @classmethod
    def setup_class(self):
        self.db = plyvel.DB('test_db', create_if_missing=True)

    @classmethod
    def teardown_class(self):
        self.db.close()

    def test_gathering_serialize(self):
        g = Gathering()
        id = g.id
        self.db.put(g.id, json.dumps(g.__dict__))

        gjson = self.db.get(id)
        gtest = Gathering.gathering_from_json(gjson)

        assert gtest.__dict__ == g.__dict__
