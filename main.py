import os
import uuid
import plyvel
import simplejson as json
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, StaticFileHandler, HTTPError

class Gathering(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.friends = {}
        self.recommendations = []
        self.selected_rec = None

    def add_friend(self, loc):
        """Takes in the location of a new friend, and returns the id of the new friend
        Loc should be of type list [lat, lng]
        """
        id = uuid.uuid5(self.id, str(loc))
        id = str(id)
        self.friends[id] = loc

        return id

    def del_friend(self, id):
        if id in self.friends:
            del self.friends[id]

    @classmethod
    def gathering_from_json(cls, jsonstr):
        g = Gathering()
        gdict = json.loads(jsonstr)

        g.id = gdict['id']
        g.friends = gdict['friends']
        g.recommendations = gdict['recommendations']
        g.selected_rec = gdict['selected_rec']

        return g

class HomeHandler(RequestHandler):
    def get(self):
        self.render("main.html")

class GatheringNewHandler(RequestHandler):
    def initialize(self):
        self.db = plyvel.DB('db', create_if_missing=True)

    def post(self):
        g = Gathering()
        self.db.put(g.id, json.dumps(g.__dict__))

        self.redirect("/gathering/" + g.id)

    def on_finish(self):
        self.db.close()

class GatheringHandler(RequestHandler):
    def initialize(self):
        self.db = plyvel.DB('db', create_if_missing=True)

    def get(self, gathering_id):
        #gjson_str = self.db.get(gathering_id)
        #g = Gathering.gathering_from_json(gjson_str)
        #self.render("gathering.html", friends=g.friends, recommendations=g.recommendations, selected_rec=g.selected_rec)
        self.render("gathering.html",
            friends = json.dumps({
               'mofo': [1.3577393, 103.7683112],
               'gofo': [1.3567393, 103.7673112],
               'lofo': [1.3587393, 103.7683112],
               'sofo': [1.3577393, 103.7693112],
            }),
            recommendations = json.dumps([
               'hehheh'
            ]),
            selected_rec = 0
         )
        """
        gid = str(gathering_id)
        gjson_str = self.db.get(gid)

        if gjson_str is None:
            raise HTTPError(404)

        g = Gathering.gathering_from_json(gjson_str)

        self.render("gathering.html", friends=g.friends, recommendations=g.recommendations, selected_rec=g.selected_rec)
        """

    def on_finish(self):
        self.db.close()

class NotFoundHandler(RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.render("404.html")

def make_app():
    return Application([
        url(r"/", HomeHandler),
        url(r"/gathering", GatheringNewHandler, name="newgathering"),
        url(r"/gathering/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})", GatheringHandler),
        url(r"/static", StaticFileHandler)
            ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        default_handler_class=NotFoundHandler,
            )

def main():
    app = make_app()
    app.listen(4000)
    IOLoop.current().start()

if __name__ == '__main__':
    print "Go to http://localhost:4000 on your browser..."
    main()
