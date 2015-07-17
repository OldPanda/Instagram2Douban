import tornado.ioloop
import time
import urllib
import urllib2
import json
from functools import partial
from pymongo import MongoClient
from utils import MultipartPostHandler
import logging


INSTAGRAM_URL = 'https://api.instagram.com/v1/'
DOUBAN_URL = 'https://api.douban.com/'


def fetch_pic_and_upload(user, users):
    """Fetch all latest pics from the given user and upload
       them onto Douban
    Args:
        user (dict): user information
    """
    instagram_info = user["instagram"]
    access_token = instagram_info["access_token"]
    # username = instagram_info["username"]
    min_timestamp = user["last_sync_time"]

    url = INSTAGRAM_URL + "users/self/media/recent?"
    arguments = "access_token={access_token}&min_timestamp={timestamp}".format(
            access_token=access_token,
            timestamp=min_timestamp
        )
    url += arguments
    try:
        response = urllib.urlopen(url).read()
        inst_response = json.loads(response)
        logging.info("Sent request to " + url)
    except:
        logging.error(url + " response error")
        return

    if len(inst_response["data"]) == 0:
        return
    user["last_sync_time"] = str(int(time.time()))
    users.save(user)
    for pic_info in reversed(inst_response["data"]):
        pic_url = pic_info["images"]["standard_resolution"]["url"]
        caption = pic_info["caption"]
        pic_caption = caption["text"] + "  via Ins2Douban" if caption \
            else "via Ins2Douban"
        upload_pic_to_douban(user, pic_url, pic_caption)


def upload_pic_to_douban(user, pic_url, caption):
    """Upload picture to Douban from url directly
    Args:
        user (dict): user information
        pic_url (str): picture url
        caption (str): picture caption
    """
    douban_info = user["douban"]
    access_token = douban_info["access_token"]
    url = DOUBAN_URL + "shuo/v2/statuses/"

    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    params = {"text": caption.encode("utf-8"),
              "image": urllib2.urlopen(pic_url)}
    opener.addheaders = [("Authorization",
                          "Bearer {}".format(access_token))]
    try:
        opener.open(url, params)
        logging.info("Uploaded picture to " + url + " succeed")
    except:
        logging.error("Uploading picture failed: " + pic_url + " open error")


def sync_img(db):
    users = db["users"]
    cursor = users.find()
    for user in cursor:
        fetch_pic_and_upload(user, users)


def main():
    """This function is used to be executed independently,
       shouldn't be called outside
    """
    logging.basicConfig(format='[%(asctime)s] %(message)s',
                        datefmt='%m/%d/%Y %I:%M:%S %p',
                        filename='sync_server_log.txt',
                        filemode='wb',
                        level=logging.NOTSET)
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]
    ioloop = tornado.ioloop.IOLoop.instance()
    sync_server = tornado.ioloop.PeriodicCallback(
        partial(sync_img, db),
        15000
        )  # 15s
    sync_server.start()
    ioloop.start()
