import os
from tornado.ioloop import IOLoop
from tornado.web import RequestHandler, Application, url, StaticFileHandler

class HomeHandler(RequestHandler):
    def get(self):
        self.render("main.html")

def make_app():
    return Application([
        url(r"/", HomeHandler),
        url(r"/static", StaticFileHandler)
            ],
        template_path=os.path.join(os.path.dirname(__file__), "templates"),
        static_path=os.path.join(os.path.dirname(__file__), "static"),
                        )

def main():
    app = make_app()
    app.listen(4000)
    IOLoop.current().start()

if __name__ == '__main__':
    main()
