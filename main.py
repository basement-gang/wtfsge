import os
import uuid
import plyvel
import simplejson as json
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, StaticFileHandler, HTTPError
import math

def centrepoint(coordinates):
    coordinates = [ map(math.radians,c) for c in coordinates ]
    points = len(coordinates)
    mean_x = sum(math.cos(lat) * math.cos(lng) for lat,lng in coordinates)/points
    mean_y = sum(math.cos(lat) * math.sin(lng) for lat,lng in coordinates)/points
    mean_z = sum(math.sin(lat)                 for lat,_   in coordinates)/points
    lng = math.atan2(mean_y,mean_x)
    hyp = math.sqrt(mean_x**2 + mean_y**2)
    lat = math.atan2(mean_z,hyp)
    return [math.degrees(lat),math.degrees(lng)]

class Gathering(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.friends = {}
        self.recommendations = []
        self.selected_rec = None
        self.centroid = None

    def add_friend(self,friend_id,loc):
        """
        Takes in the location of a new friend, and returns the id of the new friend
        Loc should be of type list [lat, lng]
        """
        if friend_id == None:
            friend_id = str(uuid.uuid4())
        self.friends[friend_id] = loc
        self.centroid = centrepoint([ [float(lat),float(lng)] for lat,lng in self.friends.values() ])
        print self.centroid
        return friend_id


    def del_friend(self, id):
        if id in self.friends:
            del self.friends[id]

    def to_dict(self):
        return self.__dict__

    @classmethod
    def gathering_from_json(cls, jsonstr):
        g = Gathering()
        gdict = json.loads(jsonstr)

        g.id = gdict['id']
        g.friends = gdict['friends']
        g.recommendations = gdict['recommendations']
        g.selected_rec = gdict['selected_rec']
        g.centroid = gdict['centroid']

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
        self.render("gathering.html")

    def post(self, gathering_id):
        gjson = self.db.get(str(gathering_id))
        g = Gathering.gathering_from_json(gjson)
        friend_id = self.get_secure_cookie("friend_id")
        if not friend_id or ( friend_id not in g.friends ):
            lat, lng = self.get_body_argument("lat"), self.get_body_argument("lng")
            friend_id = g.add_friend(friend_id,[lat, lng])
            self.db.put(g.id,json.dumps(g.__dict__))
            self.set_secure_cookie("friend_id", friend_id)
        self.write(g.to_dict())

    def on_finish(self):
        self.db.close()


class NotFoundHandler(RequestHandler):
    def prepare(self):
        self.set_status(404)
        self.render("404.html")

def make_app():
    return Application([
        url(r"/", HomeHandler),
        url(r"/gathering/new", GatheringNewHandler, name="newgathering"),
        url(r"/gathering/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})", GatheringHandler),
        url(r"/static", StaticFileHandler)
            ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
        default_handler_class=NotFoundHandler,
        # Insecure because public repo
        cookie_secret=":A@[&%p<y~NQ^*e[T7ArS%(u^|TYf^1YB|cl*_$cG-U_X{5{L1&!n><mC)t8kh%.",
            )

def main():
    app = make_app()
    app.listen(4000)
    IOLoop.current().start()

if __name__ == '__main__':
    print "Go to http://localhost:4000 on your browser..."
    main()
