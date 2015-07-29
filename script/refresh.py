from douban_client import DoubanClient
import yaml
from pymongo import MongoClient
import sys


def refresh():
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]
    config = yaml.load(file("../config.yaml", "r"))
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
        client.refresh_token(user["douban"]["refresh_token"])  # refresh token
        if client.token_code == "":
            print "[FAILED] Douban user: " + user["douban"]["uid"] + ", Refresh token"
            continue
        user["douban"]["access_token"] = client.token_code
        user["douban"]["refresh_token"] = client.refresh_token_code
        db["users"].save(user)
        print "[SUCCEED] Douban user: " + user["douban"]["uid"] + ", Refresh token"


if __name__ == "__main__":
    refresh()