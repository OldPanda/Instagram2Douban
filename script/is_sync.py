from douban_client import DoubanClient
import yaml
from pymongo import MongoClient
import sys


fail_list = set(["chaimy",
             "narcolept",
             "69549964",
             "wangtongt",
             "eaufavor",
             "yufree",
             "dallaslu",
             "superalsrk",
             "maogl",
             "131532755",
             "NioLiu",
             "tomtung",
             "udonmai",
             "irrisawu",
             "xiangjiaoyu",
             "XBH",
             "dec255",
             "dekaixu"])


def is_sync():
    conn = MongoClient('mongodb://localhost:27017/')
    db = conn["insdouban"]

    cursor = db["users"].find()
    for user in cursor:
        user["is_sync"] = False if user["douban"]["uid"] in fail_list else True
        db["users"].save(user)


if __name__ == "__main__":
    is_sync()