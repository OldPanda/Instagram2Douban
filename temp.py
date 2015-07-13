import cPickle as pickle
from pymongo import MongoClient
import time
import json
from pprint import pprint
import urllib
# with open("instagram_data_sample.json") as f:
#     data = json.load(f)
#
# for media in data["data"]:
#     print media["images"]["standard_resolution"]["url"]
#     try:
#         print media["caption"]["text"]
#     except:
#         print ""
#     print
import tornado.web
import tornado.httpserver
from tornado.options import define, options
from tornado import httpclient, gen, ioloop

define("port", default=8080, help="run on the given port", type=int)
def func():
    print "hello", time.ctime()

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Auth Success " + time.ctime() + "!")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            ]
        settings = dict(
            debug=True,
            )
        tornado.web.Application.__init__(self, handlers, **settings)

INSTAGRAM_URL = 'https://api.instagram.com/v1/'
DOUBAN_URL = 'https://api.douban.com/'

def upload_pic_to_douban(user, pic_url, caption):
    """Upload picture to Douban from url directly
    Args:
        user (dict): user information
        pic_url (str): picture url
        caption (str): picture caption
    """
    print pic_url
    douban_info = user["account"]["douban"]
    access_token = douban_info["token"]
    url = DOUBAN_URL + "shuo/v2/statuses/"

    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    params = {"text": caption.encode("utf-8"),
              "image": urllib2.urlopen(pic_url)}
    opener.addheaders = [("Authorization",
                          "Bearer {}".format(access_token))]
    try:
        opener.open(url, params)
    except:
        print "opener open error"

def imgs_json_to_list(data):
    """ convert instagram retrived json data to list
    Args:
        data: json string
    Returns:
        res: a list of (img_url, caption)
    """
    res = []
    data = json.loads(data)["data"]
    for entry in data:
        img_url = data["images"]["standard_resolution"]["url"]
        if data["caption"]:
            caption = data["caption"]["text"] + " via instagram"
        else:
            caption = "via instagram"
        res.append((img_url, caption))
    return res



def fetch_pic_and_upload(user):
    """Fetch all latest pics from the given user and upload
       them onto Douban
    Args:
        user (dict): user information
    """
    instagram_info = user["account"]["instagram"]
    access_token = instagram_info["token"]
    username = instagram_info["username"]
    min_timestamp = user["last_sync_time"]
    user["last_sync_time"] = str(time.time())
    # conn["user"].save(user)  # remember to uncomment this line to update sync time
    url = INSTAGRAM_URL + "users/self/media/recent?"
    arguments = "access_token={access_token}&min_timestamp={timestamp}".format(
            access_token=access_token,
            timestamp=min_timestamp
        )
    url += arguments
    print url
    try:
        response = urllib.urlopen(url).read()
        inst_response = json.loads(response)
    except:
        print "response error"
        return

    for pic_info in reversed(inst_response["data"]):
        pic_url = pic_info["images"]["standard_resolution"]["url"]
        caption = pic_info["caption"]
        pic_caption = "via_inst_"+caption["text"] if caption else "via_inst_"
        # download_save_pic(pic_url, username)
        upload_pic_to_douban(user, pic_url, pic_caption)

@tornado.gen.coroutine
def sync_all(db):
    users = db["users"]
    cursor = users.find({}, {"_id": 0, "douban.access_token": 1, "instagram.access_token": 1, "last_sync_time": 1})
    for user in cursor:
        fetch_pic_and_upload(user)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]

    repeat = ioloop.PeriodicCallback(sync_all(db), 6000000000000)
    repeat.start()

    ioloop.IOLoop.instance().start()
