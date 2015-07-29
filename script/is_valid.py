from douban_client import DoubanClient
import yaml
from pymongo import MongoClient
import sys


def is_valid():
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]
    config = yaml.load(file("config.yml", "r"))
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        conf = config["TEST"]
    else:
        conf = config["PRODUCTION"]

    SCOPE = 'douban_basic_common,shuo_basic_r,shuo_basic_w'
    API_KEY = conf["douban_api_key"]
    API_SECRET = conf["douban_api_secret"]
    redirect_uri = conf["douban_redirect_uri"]

    client = DoubanClient(API_KEY, API_SECRET, redirect_uri, SCOPE)
    cursor = db["users"].find()
    for user in cursor:
        token = user["douban"]["access_token"]
        client.auth_with_token(token)
        try:
            print ("[SUCCESS] " + client.user.me["uid"])
        except:
            print ("[FAILED]" + user["douban"]["uid"])
            continue



if __name__ == "__main__":
    is_valid()
