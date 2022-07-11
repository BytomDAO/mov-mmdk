# coding=utf-8
import json
from time import sleep
import time
import math
from threading import Lock
from copy import deepcopy, copy
from collections import defaultdict
from datetime import datetime, timedelta

from flask import Flask, request
from flask import jsonify

app = Flask(__name__)


@app.route('/test', methods=["POST"])
def test():
    data = request.get_data()
    print(data)
    # print(request.get_json())
    # if request.method == "POST":
    #     if data:
    #         js_data = json.loads(data)
    #         pay_id = js_data.get("pay_id")
    #         signed_data = js_data.get("signed_data")
    #         print("pay_id", pay_id)
    #         print("signed_data", signed_data)

    return jsonify({"abc": "abc"}), 200


@app.route('/t', methods=["GET"])
def t():
    return jsonify({"a": "a"}), 200


if __name__ == "__main__":
    # test trade_server
    app.run(host="0.0.0.0", port=5010)
