from tornado import gen
import time


class User(object):
    """ User entry schema
    sample data:
    {  "douban": {   "uid": string,
                     "access_token": string,
                     "expire_date": string,
                     "refresh_token": string,
                     "name": string,
                     "avatar": string (url),
                     "signature": string,
                     "alt": string,
                     "desc": string,
                     "loc_name": string, }

       "instagram": { "id": string,
                      "access_token": string,
                      # "refresh_token": string,
                      "username": string,
                      "bio": string,
                      "full_name": string,
                      "website": string,
                      "profile_picture": string }


      "last_sync_time": string (unix timestamp)
    }
    """
    def __init__(self, douban_user, instagram_user):
        self.douban_user = douban_user
        self.instagram_user = instagram_user
        self.last_sync_time = int(time.time())
