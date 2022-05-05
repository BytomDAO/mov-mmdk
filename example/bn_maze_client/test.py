# coding=utf-8
'''
图片转换: 可以传 图片数据  或者 图片链接
上传到oss
'''
import sys
import oss2
import urllib3

img_directory = "prod-t-nft/"
accessKey = "LTAI5tAUpW14UfwMj4gGfBbT"  # 通过账号获得accessKey
secretAccessKey = "MlJe7Z1WMb3mncxwsPPjqUJYMpED9Q"  # 通过账号获得secretAccessKey


def storage(file_name, file_path):
    # print('file_name = ', file_name)
    # 阿里云主账号AccessKey拥有所有API的访问权限，风险很高。强烈建议您创建并使用RAM账号进行API访问或日常运维，请登录 https://ram.console.aliyun.com 创建RAM账号。
    auth = oss2.Auth(accessKey, secretAccessKey)
    bucket = oss2.Bucket(auth, 'http://oss-cn-shanghai.aliyuncs.com', 'bycoin')
    # requests.get返回的是一个可迭代对象（Iterable），此时Python SDK会通过Chunked Encoding方式上传。
    # input = requests.get('http://www.aliyun.com')
    ret = bucket.put_object_from_file(img_directory + file_name, file_path)
    oss_img = ret.resp.response.url
    return oss_img


if __name__ == '__main__':
    import requests

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
    }
    # re = requests.get(
    #     'https://cdn.poizon.com/client_upload/92175400_byte15736861_dur0_2aadb20036a37cb786576847bc5afff5_1598572882087_du_android_w576h1024.mp4',
    #     headers=headers, verify=False)
    # # print(re.content)
    # print(storage('test.mp4', re.content))

    print(storage('a.png', 'a.png'))
