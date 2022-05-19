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
    new_save_name = use_dir + time.strftime("%Y-%m-%d_%H%M%S", time.localtime()) + str(int((time.time()*1000)) % 1000) + suffix_name
    result = bucket.put_object_from_file(new_save_name, input_path_name)
    image_url = f"https://{bucket_name}.{regin}.aliyuncs.com/" + new_save_name
    # HTTP返回码。
    print('http status: {0} {1}'.format(result.status, image_url))
    # # 请求ID。请求ID是请求的唯一标识，强烈建议在程序日志中添加此参数。
    # print('request_id: {0}'.format(result.request_id))
    return new_save_name


def get_md5_02(file_path):
    f = open(file_path, 'rb')
    md5_obj = hashlib.md5()
    while True:
        d = f.read(8096)
        if not d:
            break
        md5_obj.update(d)
    hash_code = md5_obj.hexdigest()
    f.close()
    md5 = str(hash_code).lower()
    return md5


def run():
    filepath_dic = {}
    mnemonic_str = "major skull dinner crucial trip weird thumb grunt absent note motion primary"
    # obj = NftApi(mnemonic_str=mnemonic_str, network=Net.MAIN.value)
    obj = NftApi(mnemonic_str=mnemonic_str, network=Net.TEST.value)
    description = "test !!!!!!!!!!!!!!! sdfsfsdfsd. !!!!!!!!!!!!!!!!!!!!!!"
    royalty_rate = "15"
    margin_amount = "0.1"
    btm_asset = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

    error_out_f = open("error.log", "a")
    error_out_f.write("new upload task!\n")
    flag = True

    name = "BearRabbit"
    for i in range(100, 101):
        if flag:
            flag = False
            continue

        code = str(i)
        pic_name = "a.png"
        if pic_name in filepath_dic.keys():
            filepath = filepath_dic[pic_name]
        else:
            filepath = oss_upload(pic_name, suffix_name=".jpg")
            filepath_dic[pic_name] = filepath

        i = 0
        while i < 5:
            i = i + 1
            try:
                content_md5 = get_md5_02(pic_name)
                data = obj.issue_nft(name + code, filepath, content_md5, royalty_rate, btm_asset, margin_amount, description)

                print(data)
                if int(data["code"]) == 200 and data["data"]["nft_asset"]:
                    print(f"upload {name} {code} {pic_name} successily!")
                    break
                else:
                    print(f"error {name} {code} {pic_name} failed!")
                    line = ','.join([str(x) for x in [name, code, pic_name]])
                    error_out_f.write(line + "\n")
                time.sleep(1)
            except Exception as ex:
                print(ex)
            time.sleep(1)


    error_out_f.close()


if __name__ == "__main__":
    run()



