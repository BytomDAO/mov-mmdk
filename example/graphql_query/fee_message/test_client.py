
import requests
import json
d_str = '{"abc":"c"}'
d = {"abc":"c"}
r = requests.post("http://127.0.0.1:5010/test", json=d)
print(r.json())

