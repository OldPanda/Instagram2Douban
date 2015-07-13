import tornado.ioloop
import time
import urllib, urllib2
import json
from pymongo import MongoClient
from utils import MultipartPostHandler

INSTAGRAM_URL = 'https://api.instagram.com/v1/'
DOUBAN_URL = 'https://api.douban.com/'

def fetch_pic_and_upload(user, db):
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
    print url
    try:
        response = urllib.urlopen(url).read()
        inst_response = json.loads(response)
    except:
        print "response error"
        return

    if len(inst_response["data"]) == 0:
        return
    user["last_sync_time"] = str(int(time.time()))
    db["users"].save(user)  # remember to uncomment this line to update sync time
    for pic_info in reversed(inst_response["data"]):
        pic_url = pic_info["images"]["standard_resolution"]["url"]
        caption = pic_info["caption"]
        pic_caption = caption["text"] + "  via Ins2Douban" if caption else "via Ins2Douban"
        # download_save_pic(pic_url, username)
        upload_pic_to_douban(user, pic_url, pic_caption)


def upload_pic_to_douban(user, pic_url, caption):
    """Upload picture to Douban from url directly
    Args:
        user (dict): user information
        pic_url (str): picture url
        caption (str): picture caption
    """
    print pic_url
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
        print "send" + url + "successed"
    except:
        print "opener open error"


def sync_img(db):
    users = db["users"]
    cursor = users.find({}, {"_id": 0, "douban.access_token": 1, "instagram.access_token": 1, "last_sync_time": 1})
    for user in cursor:
        fetch_pic_and_upload(user, db)

def main():
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]
    sync_server = tornado.ioloop.PeriodicCallback(sync_img(db), 12000) # 5 min (300000 ms)
    sync_server.start()

if __name__ == '__main__':
    main()
