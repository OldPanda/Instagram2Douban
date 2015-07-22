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
CONFIG = {}


def fetch_pic_and_upload(user, users):
    """Fetch all latest pics from the given user and upload
       them onto Douban
    Args:
        user (dict): user information
        users (MongoDB collection): users info database
    """
    instagram_info = user["instagram"]
    access_token = instagram_info["access_token"]
    min_timestamp = user["last_sync_time"]

    url = INSTAGRAM_URL + "users/self/media/recent?"
    arguments = urllib.urlencode({
        "access_token": access_token,
        "min_timestamp": min_timestamp
    })

    try:
        response = urllib.urlopen(url+arguments).read()
        inst_response = json.loads(response)
        # logging.info("Sent request to " + url)
    except:
        logging.error("Inst_user: " + instagram_info["username"] + " response error")
        return

    if len(inst_response["data"]) == 0:
        # no new picture
        return
    user["last_sync_time"] = str(int(time.time()))
    users.save(user)

    for pic_info in reversed(inst_response["data"]):
        pic_url = pic_info["images"]["standard_resolution"]["url"]
        caption = pic_info["caption"]
        pic_caption = caption["text"] + "  via Ins2Douban" if caption \
            else "via Ins2Douban"
        is_refreshed = upload_pic_to_douban(user,
                                            pic_url,
                                            pic_caption,
                                            users)
        if is_refreshed:
            # update user info because of new access token
            user = users.find({
                "instagram.id": user["instagram"]["id"]
            })


def upload_pic_to_douban(user, pic_url, caption, users):
    """Upload picture to Douban from url directly
    Args:
        access_token (str): user's Douban access_token
        pic_url (str): picture url
        caption (str): picture caption
        users (MongoDB collection): user database
    Returns:
        (bool): if re-upload happened(AKA. new access token is fetched)
    """
    url = DOUBAN_URL + "shuo/v2/statuses/"

    access_token = user["douban"]["access_token"]
    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    params = {"text": caption.encode("utf-8"),
              "image": urllib2.urlopen(pic_url)}
    opener.addheaders = [("Authorization",
                          "Bearer {}".format(access_token))]

    try:
        res = opener.open(url, params)
        if res.code == 200:
            # upload pic succeed
            logging.info("Douban user: [{user}] uploaded picture succeed".format(
                    user=user["douban"]["uid"]
                ))
            return False  # indicate if a new access token is generated
        elif res.code == 106:
            # access token expires
            logging.warning("Douban user: " + user["douban"]["uid"] + " token expired")
            refresh_token = user["douban"]["refresh_token"]
            new_access_token = refresh(refresh_token, user, users)
            if new_access_token:
                # upload pic again
                user["douban"]["access_token"] = new_access_token
                upload_pic_to_douban(user, pic_url, caption, users)
                return True
            else:
                return False
    except:
        logging.error("Uploading picture failed: " + pic_url + " open error")
        return False


def refresh(refresh_token, user, users):
    """Send refresh token request to Douban
    Args:
        refresh_token (str): refresh token used to fetch new token
        user (dict): user info
        users (MongoDB collection): collection
    Returns:
        (str): new token (or False signal)
    """
    opener = urllib2.build_opener(MultipartPostHandler.MultipartPostHandler)
    url = "https://www.douban.com/service/auth2/token"
    params = {
        "client_id": CONFIG["douban_api_key"],
        "client_secret": CONFIG["douban_api_secret"],
        "redirect_uri": CONFIG["douban_redirect_uri"],
        "grant_type": "refresh_token",
        "refresh_token": refresh_token
    }

    try:
        # fetch new token using refresh token
        response = opener.open(url, params).read()
        user["access_token"] = response["access_token"]
        user["expires_in"] = response["expires_in"]
        user["refresh_token"] = response["refresh_token"]
        users.save(user)
        logging.info("Got a new access token for " + response["douban_user_id"])
        return user["access_token"]
    except:
        logging.error("Fetch user " + user["uid"] + "'s refresh token failed. ")
        return False


def sync_img(db, conf):
    """Synchronize pics for each user in database
    """
    global CONFIG
    CONFIG = conf
    users = db["users"]
    cursor = users.find()
    for user in cursor:
        fetch_pic_and_upload(user, users)


# def main():
#     """This function is used to be executed independently,
#        shouldn't be called outside
#     """
#     logging.basicConfig(format='[%(asctime)s] %(message)s',
#                         datefmt='%m/%d/%Y %I:%M:%S %p',
#                         filename='sync_server_log.txt',
#                         filemode='wb',
#                         level=logging.NOTSET)
#     conn = MongoClient('mongodb://localhost:27017/')
#     db = conn["insdouban"]
#     ioloop = tornado.ioloop.IOLoop.instance()
#     sync_server = tornado.ioloop.PeriodicCallback(
#         partial(sync_img, db),
#         15000
#         )  # 15s
#     sync_server.start()
#     ioloop.start()
