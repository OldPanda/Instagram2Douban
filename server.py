# -*- coding: utf-8 -*-
import os
import logging
import tornado.web
import tornado.gen
import tornado.httpserver
import tornado.ioloop
from pymongo import MongoClient
from utils.InstagramLoginAuth import InstagramOAuth2Mixin
from utils.DoubanLoginAuth import DoubanOAuth2Mixin
from utils import tools
from tornado.options import define, options
from uuid import uuid4
from functools import partial
from sync_server import sync_img

define("port", default=8080, help="run on the given port", type=int)


class DoubanAuthHandler(DoubanOAuth2Mixin, tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            token = yield self.get_authenticated_user(
                redirect_uri=self.settings['douban_redirect_uri'],
                code=self.get_argument('code')
            )
            if token:
                self.application.user_info["douban"] = token
                self.set_secure_cookie("douban", str(uuid4()))
                self.redirect("/auth/instagram")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['douban_redirect_uri'],
                client_id=self.settings['douban_api_key'],
                scope=None,
                response_type='code'
            )


class InstagramAuthHandler(InstagramOAuth2Mixin, tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        if self.get_argument('code', False):
            token = yield self.get_authenticated_user(
                redirect_uri=self.settings['instagram_redirect_uri'],
                code=self.get_argument('code')
            )
            if token:
                self.application.user_info["instagram"] = token
                self.set_secure_cookie("instagram", str(uuid4()))
                add_user(self.application.db, self.application.user_info)
                #self.redirect(self.get_argument("next", "/"))
                self.redirect("/")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['instagram_redirect_uri'],
                client_id=self.settings['instagram_client_id'],
                scope=None, # used default scope
                response_type='code'
            )
class HomeHandler(tornado.web.RequestHandler):

    def get(self):
        # self.set_secure_cookie("user_id", "ilovewilbeibi~~~")
        self.write("Auth Success " + "Success" + "!")

class Application(tornado.web.Application):

    def __init__(self, db):
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/douban", DoubanAuthHandler),
            (r"/auth/instagram", InstagramAuthHandler),
            ]
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            instagram_client_id="0a0fd5f2726a4d9387b5e827a65a169d",
            instagram_client_secret="3f374090b5f941c6b0c0b6a489120a6e",
            instagram_redirect_uri="http://localhost:8080/auth/instagram",
            douban_api_key="087d1fa8c7b0696519775efa57113c2f",
            douban_api_secret="74876e47a6d9e46a",
            douban_redirect_uri="http://localhost:8080/auth/douban",
            cookie_secret=str(uuid4()),
            #cookie_secret="FILL IN YOUR COOKIE SEC1234567890",
            xsrf_cookies=True,
            debug=True,
            )

        self.db = db
        self.user_info = {}
        tornado.web.Application.__init__(self, handlers, **settings)

def add_user(db, user_info):
    """ add user to database
    """
    new_user = tools.oauth_data_to_doc(user_info)
    db.users.update({"douban.uid": new_user["douban"]["uid"]}, new_user, upsert=True)



def main():
    logging.basicConfig(format='[%(asctime)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='sync_server_log.txt',
                        filemode='wb',
                        level=logging.NOTSET)
    conn = MongoClient('mongodb://localhost:27017/')
    logging.info("MongoDB connection succeed")
    db = conn["insdouban"]
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(db))
    http_server.listen(options.port, address="0.0.0.0")
    sync_server = tornado.ioloop.PeriodicCallback(
        partial(sync_img, db),
        15000
    ) # 15 seconds
    sync_server.start()
    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()
