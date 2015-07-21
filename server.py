# -*- coding: utf-8 -*-
import os
import logging
import tornado.web
import tornado.gen
import tornado.httpserver
import tornado.ioloop
import base64
import yaml
from pymongo import MongoClient
from utils.InstagramLoginAuth import InstagramOAuth2Mixin
from utils.DoubanLoginAuth import DoubanOAuth2Mixin
from utils import tools
from tornado.options import define, options
from uuid import uuid4
from functools import partial
from sync_server import sync_img


define("port", default=8080, help="run on the given port", type=int)
define("test", default=False, help="Turn on autoreload and log to stderr", type=bool)

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
                # self.set_secure_cookie("douban", str(uuid4()))
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
            unlink = self.get_secure_cookie("unlink", None)
            code = self.get_argument('code')
            token = yield self.get_authenticated_user(
                redirect_uri=self.settings['instagram_redirect_uri'],
                code=self.get_argument('code')
            )
            if token and not unlink:
                self.application.user_info["instagram"] = token
                # self.set_secure_cookie("instagram", str(uuid4()))
                add_user(self.application.db, self.application.user_info)
                self.redirect("/")
            elif token:
                del_user(self.application.db, token)
                self.redirect("/")
        else:
            yield self.authorize_redirect(
                redirect_uri=self.settings['instagram_redirect_uri'],
                client_id=self.settings['instagram_client_id'],
                scope=None,  # used default scope
                response_type='code'
            )


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        if self.get_secure_cookie("unlink", None):
            message = "Unlink succeed! "
        elif self.get_argument("auth_succeed", None):
            message = "Link succeed! "
        else:
            message = None
        self.clear_all_cookies()
        self.application.user_info = {}
        self.render("index.html", message=message)


class UnlinkHandler(InstagramOAuth2Mixin, tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        self.set_secure_cookie("unlink", str(uuid4()))
        yield self.authorize_redirect(
            redirect_uri=self.settings['instagram_redirect_uri'],
            client_id=self.settings['instagram_client_id'],
            scope=None,  # used default scope
            response_type='code'
        )


class Application(tornado.web.Application):
    def __init__(self, db, conf):
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/douban", DoubanAuthHandler),
            (r"/auth/instagram", InstagramAuthHandler),
            (r"/unlink", UnlinkHandler)
            ]
        settings = dict(
            template_path = os.path.join(os.path.dirname(__file__), "templates"),
            static_path = os.path.join(os.path.dirname(__file__), "static"),
            instagram_client_id = conf["instagram_client_id"],
            instagram_client_secret = conf["instagram_client_secret"],
            instagram_redirect_uri = conf["instagram_redirect_uri"],
            douban_api_key = conf["douban_api_key"],
            douban_api_secret = conf["douban_api_secret"],
            douban_redirect_uri = conf["douban_redirect_uri"],
            cookie_secret = str(base64.b64encode(uuid4().bytes + uuid4().bytes)),
            # xsrf_cookies = True,
            debug = True,
            )

        self.db = db
        self.user_info = {}
        tornado.web.Application.__init__(self, handlers, **settings)


def add_user(db, user_info):
    """ add user to database
    """
    new_user = tools.oauth_data_to_doc(user_info)
    db.users.update({"douban.uid": new_user["douban"]["uid"]},
                    new_user, upsert=True)
    logging.info("Saved user Douban: [{douban}], Instagram: [{instagram}]"
                 .format(
                    douban=new_user["douban"]["uid"],
                    instagram=new_user["instagram"]["username"]
                 ))


def del_user(db, user_info):
    """delete user from database
    """
    inst_id = user_info['user']['id']
    db["users"].remove({"instagram.id": inst_id})


def main():
    logging.basicConfig(format='[%(asctime)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='server_log',
                        filemode='a',
                        level=logging.NOTSET)
    conn = MongoClient('mongodb://localhost:27017/')
    logging.info("MongoDB connection succeed")
    db = conn["insdouban"]
    tornado.options.parse_command_line()
    config = yaml.load(file("config.yaml", "r"))
    if options.test:
        conf = config["TEST"]
    else:
        conf = config["PRODUCTION"]
    http_server = tornado.httpserver.HTTPServer(Application(db, conf))
    http_server.listen(options.port)
    sync_server = tornado.ioloop.PeriodicCallback(
        partial(sync_img, db, conf),
        #180000
        conf["PERIOD"]
    )  # 3 min
    sync_server.start()
    tornado.ioloop.IOLoop.instance().start()


if __name__ == "__main__":
    main()
