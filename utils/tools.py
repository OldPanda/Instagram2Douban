import json
import time

def flatten_dict(d):
    def items():
        for key, value in d.items():
            if isinstance(value, dict):
                for subkey, subvalue in flatten_dict(value).items():
                    yield subkey, subvalue
            else:
                yield key, value

    return dict(items())


def oauth_data_to_doc(data):
    """ convert oauth2 data to mongodb document
    Args:
        data: a dictionary
    Returns:
        new_user: a dictionary
    """
    data["instagram"] = flatten_dict(data["instagram"])

    douban_attr = ["uid", "access_token", "expires_in", "refresh_token", "name", "signature", "alt", "desc", "loc_name"]
    instagram_attr = ["id", "access_token", "username", "bio", "full_name", "website", "profile_picture"]

    new_user = {"douban":{}, "instagram":{}, "last_sync_time": ""}
    for attr in douban_attr:
        new_user["douban"][attr] = data["douban"][attr]
    for attr in instagram_attr:
        new_user["instagram"][attr] = data["instagram"][attr]
    new_user["last_sync_time"] = str(int(time.time()))

    return new_user

def imgs_to_list(data):
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
