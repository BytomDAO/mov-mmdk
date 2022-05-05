import time
import hashlib
import oss2


from mov_sdk.nft_api import NftApi, Net


def oss_upload(input_path_name, suffix_name= ".png"):
    regin = "oss-cn-shanghai"
    accessKeyId = ""
    accessKeySecret = ""
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
    return image_url


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


# print(oss_upload("a.png"))
def run():
    filepath_dic = {}
    mnemonic_str = "major skull dinner crucial trip weird thumb grunt absent note motion primary"
    obj = NftApi(mnemonic_str=mnemonic_str, network=Net.TEST.value)
    description = "kxc"
    royalty_rate = "15"
    margin_amount = "0.1"
    btm_asset = 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'

    flag = True
    f = open("input.txt", "r")
    for line in f:
        if flag:
            flag = False
            continue

        name, code, pic_name = line.strip().split(',')
        if pic_name in filepath_dic.keys():
            filepath = filepath_dic[pic_name]
        else:
            filepath = oss_upload(pic_name, suffix_name=".png")
            filepath_dic[pic_name] = filepath

        content_md5 = get_md5_02(pic_name)
        data = obj.issue_nft(name, filepath, content_md5, royalty_rate, btm_asset, margin_amount, description)
        print(data)
    f.close()


if __name__ == "__main__":
    run()



