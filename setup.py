# coding:utf-8

from setuptools import find_packages, setup
# or
# from distutils.core import setup

long_description = "mov_sdk"
setup(
    name='mov_sdk',  # 包名字
    version='1.0.1',  # 包版本
    author="ipqhjjybj",
    author_email='250657661@qq.com',  # 作者邮箱
    license="AGPL v3",
    url='https://www.8btc.com/',  # 包的主页
    description='MOV Trading SDK',  # 简单描述
    long_description=long_description,
    include_package_data=True,
    #packages=['mov_sdk'],
    packages=find_packages(exclude=["example"]),  # 包
    classifiers=[
        # 发展时期,常见的如下
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 3 - Alpha',

        # 开发的目标用户
        'Intended Audience :: Developers',

        # 属于什么类型
        'Topic :: Software Development :: Build Tools',

        # 目标 Python 版本
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ]
)
