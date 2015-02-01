import os
import uuid
import plyvel
import simplejson as json
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, StaticFileHandler, HTTPError
import math

class Gathering(object):
    def __init__(self):
        self.id = str(uuid.uuid4())
        self.friends = {}
        self.recommendations = []
        self.selected_rec = None
        self.centroid = None

    def add_friend(self, loc):
        """
        Takes in the location of a new friend, and returns the id of the new friend
        Loc should be of type list [lat, lng]
        """
        friend_id = str(uuid.uuid4())
        self.friends[friend_id] = loc
        self.__update_centroid()
        return friend_id

    def update_friend(self, friend_id, loc):
        self.friends[friend_id] = loc
        self.__update_centroid()

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

    def __update_centroid(self):
        self.centroid = self.__centrepoint([[float(lat), float(lng)] for lat, lng in self.friends.values()])

    def __centrepoint(self, coordinates):
        coordinates = [map(math.radians, c) for c in coordinates]
        points = len(coordinates)
        mean_x = sum(math.cos(lat) * math.cos(lng) for lat, lng in coordinates) / points
        mean_y = sum(math.cos(lat) * math.sin(lng) for lat, lng in coordinates) / points
        mean_z = sum(math.sin(lat) for lat, _ in coordinates) / points
        lng = math.atan2(mean_y, mean_x)
        hyp = math.sqrt(mean_x ** 2 + mean_y ** 2)
        lat = math.atan2(mean_z, hyp)
        return [math.degrees(lat), math.degrees(lng)]

class BaseHandler(RequestHandler):
    @property
    def db(self):
        return self.application.db

    # TODO: Add functions to override 404 and 500

class HomeHandler(BaseHandler):
    def get(self):
        self.render("main.html")

class GatheringNewHandler(BaseHandler):
    def post(self):
        g = Gathering()
        self.db.put(g.id, json.dumps(g.to_dict()))

        self.redirect("/gatherings/" + g.id)

class GatheringHandler(BaseHandler):
    def get(self, gathering_id):
        gjson = self.db.get(str(gathering_id))
        if not gjson:
            raise HTTPError(404)
        g = Gathering.gathering_from_json(gjson)
        friend_id = self.get_secure_cookie("friend_id")
        print friend_id
        print g.friends
        print friend_id in g.friends
        if friend_id in g.friends:
            in_gathering = "true"
        else:
            in_gathering = "false"
        self.render("gathering.html", in_gathering=in_gathering)

    def post(self, gathering_id):
        """Add a new friend.
        """
        gjson = self.db.get(str(gathering_id))
        if not gjson:
            raise HTTPError(404)
        g = Gathering.gathering_from_json(gjson)
        friend_id = self.get_secure_cookie("friend_id")
        if not friend_id or (friend_id not in g.friends):
            lat, lng = self.get_body_argument("lat"), self.get_body_argument("lng")
            friend_id = g.add_friend([lat, lng])
            self.db.put(g.id, json.dumps(g.to_dict()))
            self.set_secure_cookie("friend_id", friend_id)
            print "setting cookie.."
        self.write(g.to_dict())

    def put(self, gathering_id):
        """Update the location of an existing friend.
        """
        gjson = self.db.get(str(gathering_id))
        if not gjson:
            raise HTTPError(404)

        g = Gathering.gathering_from_json(gjson)
        friend_id = self.get_secure_cookie("friend_id")
        print "put", friend_id
        print "put", g.centroid
        if friend_id:
            lat, lng = self.get_body_argument("lat"), self.get_body_argument("lng")
            g.update_friend(friend_id, [lat, lng])
            print "Update location."
            print g.centroid
            self.db.put(g.id, json.dumps(g.to_dict()))

        self.write(g.to_dict())

class GatheringPollHandler(BaseHandler):
    """Endpoint for longpolling to hit, to constantly get updated
    Gathering data. Should return 302 when provided with an If-Not-Match
    etag header that matches.
    """
    def get(self, gathering_id):
        """If the request provides an etag header, this *should* return a 304 automagically
        if the etag headers match."""
        gjson = self.db.get(str(gathering_id))
        if not gjson:
            raise HTTPError(404)

        g = Gathering.gathering_from_json(gjson)
        self.write(g.to_dict())

class FriendHandler(BaseHandler):
    def delete(self, gathering_id, friend_id):
        """Delete a friend.
        """
        gjson = self.db.get(str(gathering_id))
        if not gjson:
            raise HTTPError(404)
        g = Gathering.gathering_from_json(gjson)
        g.del_friend(friend_id)
        self.db.put(g.id, json.dumps(g.to_dict()))

        self.set_header(200)
        self.write('')

class NotFoundHandler(BaseHandler):
    def prepare(self):
        self.set_status(404)
        self.render("404.html")

class WTFSGEApplication(Application):
    """The main application used by this app.
    We use a separate class because we want a global db connection.
    """
    def __init__(self):
        handlers = [
                url(r"/", HomeHandler),
                url(r"/gatherings/", GatheringNewHandler, name="newgathering"),
                url(r"/gatherings/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})", GatheringHandler),
                url(r"/gatherings/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})/data", GatheringPollHandler),
                url(r"/gatherings/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})/friends/([a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12})", FriendHandler),
                url(r"/static", StaticFileHandler)
        ]

        settings = dict(
                template_path=os.path.join(os.path.dirname(__file__), "templates"),
                static_path=os.path.join(os.path.dirname(__file__), "static"),
                default_handler_class=NotFoundHandler,
                # Insecure because public repo
                cookie_secret=":A@[&%p<y~NQ^*e[T7ArS%(u^|TYf^1YB|cl*_$cG-U_X{5{L1&!n><mC)t8kh%.",
                debug=True
        )
        Application.__init__(self, handlers, **settings)
        # Use a global connection to leveldb.
        self.db = plyvel.DB('db', create_if_missing=True)

def main():
    app = WTFSGEApplication()
    app.listen(4000)
    IOLoop.current().start()

if __name__ == '__main__':
    print "Go to http://localhost:4000 on your browser..."
    main()
