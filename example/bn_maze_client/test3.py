# coding=utf-8
import time
import hashlib
import oss2
import os
import codecs
import json


from mov_sdk.nft_api import NftApi, Net


def load_json(filename):
    """
    Load data from json file in temp path.
    """
    if os.path.exists(filename):
        with codecs.open(filename, mode="r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    else:
        return {}


def oss_upload(input_path_name, suffix_name=".png"):
    js_data = load_json("key.json")
    regin = "oss-cn-shanghai"
    accessKeyId = js_data["accessKeyId"]
    accessKeySecret = js_data["accessKeySecret"]
    bucket_name = "bycoin"
    use_dir = "prod-t-nft/"

    url_path = f'http://{regin}.aliyuncs.com'
    auth = oss2.Auth(accessKeyId, accessKeySecret)
    bucket = oss2.Bucket(auth, url_path, bucket_name)
    #new_save_name = use_dir + time.strftime("%Y-%m-%d_%H%M%S", time.localtime()) + str(int((time.time()*1000)) % 1000) + suffix_name
    new_save_name = "prod-t-nft/2022-05-20_142439939.jpg"
    result = bucket.put_object_from_file(new_save_name, input_path_name)
    image_url = f"https://{bucket_name}.{regin}.aliyuncs.com/" + new_save_name
    # HTTP返回码。
    print('http status: {0} {1}'.format(result.status, image_url))
    # # 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
    # print('request_id: {0}'.format(result.request_id))
    return new_save_name

print(oss_upload("Earth-Rabbit.jpg", suffix_name=".jpg"))
