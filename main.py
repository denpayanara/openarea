import re
import ssl
from urllib import request, parse

# URL取得

url = 'https://network.mobile.rakuten.co.jp/assets/js/area.saikyo-plan-project.bundle.js'

ctx = ssl.create_default_context()

ctx.options |= 0x4

with request.urlopen(url, context=ctx) as r:
    urls = re.findall(r'"(/assets/json/area-project-\d{6}-\d{6}.json)"', r.read().decode('utf-8'))

with open('data/url.text', mode='r') as f:
    before_url = f.read()

print(urls[0] == before_url)

print(type(urls[0]), type(before_url))
