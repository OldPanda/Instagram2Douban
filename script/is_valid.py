from douban_client import DoubanClient
import yaml
from pymongo import MongoClient
import sys



def set_up():
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
    return db, client

def check_valid(client, user):
    token = user["douban"]["access_token"]
    client.auth_with_token(token)
    try:
        client.user.me["uid"]
        return True
    except:
        return False


def query_users(db, client, query_uid=None):
    """ if query_uid is given, query that specific douban uid
    Args:
        db (mongodb instance)
        client (douban client instance)
        query_uid (string)
    Returns:
        failed_users (list of string)
    """
    if query_uid != None:
        cursor = db["users"].find({"douban.uid":query_uid})
    else:
        cursor = db["users"].find()
    failed_users = []
    for user in cursor:
        if check_valid(client, user):
            print ("[SUCCESS] " + client.user.me["uid"])
        else:
            print ("[FAILED]" + user["douban"]["uid"])
            failed_users.append(user["douban"]["uid"])
    return failed_users



# def is_valid():
#     conn = MongoClient('mongodb://localhost:27017/')
#     db = conn["insdouban"]
#     config = yaml.load(file("config.yml", "r"))
#     if len(sys.argv) > 1 and sys.argv[1] == "--test":
#         conf = config["TEST"]
#     else:
#         conf = config["PRODUCTION"]
#
#     SCOPE = 'douban_basic_common,shuo_basic_r,shuo_basic_w'
#     API_KEY = conf["douban_api_key"]
#     API_SECRET = conf["douban_api_secret"]
#     redirect_uri = conf["douban_redirect_uri"]
#
#     client = DoubanClient(API_KEY, API_SECRET, redirect_uri, SCOPE)
#     cursor = db["users"].find()
#     for user in cursor:
#         token = user["douban"]["access_token"]
#         client.auth_with_token(token)
#         try:
#             print ("[SUCCESS] " + client.user.me["uid"])
#         except:
#             print ("[FAILED]" + user["douban"]["uid"])
#             continue



if __name__ == "__main__":
    #is_valid()
    query_uid = None
    if len(sys.argv) >= 2:
        query_uid = sys.argv[2]
    db, client = set_up()
    query_users(db, client, query_uid)
