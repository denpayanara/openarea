import json
import os
import re
import ssl
import sys
import time
from urllib import request, parse

import geopandas as gpd
# from linebot import LineBotApi
# from linebot.models import TextSendMessage
import pandas as pd
import tweepy

# 郵便番号データ
with open('zip_code_nara.json') as f:
    json_zip = json.load(f)

# 郵便番号から住所を取得する関数

def get_addr(zipcode):

    addr = ''

    for v in json_zip:

        try:
            if  v['zip_code'] == zipcode:

                addr = v['pref'] + v['city'] + v['sname']

                # 郡名削除
                addr = re.sub('生駒郡|宇陀郡|北葛城郡|磯城郡|高市郡|山辺郡|吉野郡', '', addr)

        # 存在しない場合の処理
        except:
            addr = None

    return addr

# URL取得

url = 'https://network.mobile.rakuten.co.jp/assets/js/area.saikyo-plan-project.bundle.js'

ctx = ssl.create_default_context()

ctx.options |= 0x4

with request.urlopen(url, context=ctx) as r:
    urls = re.findall(r'"(/assets/json/area-project-\d{6}-\d{6}.json)"', r.read().decode('utf-8'))

json_data = list()

if urls != 0:

    # 前回の値と異なれば実行

    with open('data/url.text', mode='r') as f:
        before_url = f.read()

    if before_url != urls[0]:

        for i, url in enumerate(urls):
            
            with request.urlopen(f'https://network.mobile.rakuten.co.jp/{url}') as f:

                data = json.loads(f.read().decode('utf-8'))

                for d in data:

                    d['flag'] = i # flag = 0 が今回更新データ
                    
                    json_data.append(d)
                
            time.sleep(1)

    else:
        print('前回と同じデータの為プログラムを終了します。')
        sys.exit()

else:
    print('URLを取得できていません。')
    sys.exit()

list_nara = list()

for j in json_data:

    try:

        if j['Prefecture'] == '奈良県':

            print(j['City'])

            j['addr'] = get_addr(int(j['PostalCode']))

            # 郡名削除
            j['City']  = re.sub('生駒郡|宇陀郡|北葛城郡|磯城郡|高市郡|山辺郡|吉野郡', '', j['City'])

            list_nara.append(j)
            
    except:
        pass

# 奈良県の更新された件数をカウント

count_nara = 0

# Twitterの140文字制限：約12件あるとアウト

addr_4G = '【4G】\n'

addr_5G = '【5G】\n'

for d in list_nara:

    if d['flag'] == 0:

        count_nara +=1

        if d['Type'] == '4G':

            addr_4G += d['addr'].replace('奈良県', '') + '\n'

        else:

            addr_5G += d['addr'].replace('奈良県', '') + '\n'    

message = f'基地局設置情報ページが更新されました。\n\n奈良県は{count_nara}件です。\n\n{addr_4G+addr_5G}\nhttps://network.mobile.rakuten.co.jp/area/saikyo-plan-project/?l-id=area_saikyo-plan-project\n#楽天モバイル #bot'

print(message)

# SNSへ通知

# Twitter
api_key = os.environ['API_KEY']
api_secret = os.environ['API_SECRET_KEY']
access_token = os.environ['ACCESS_TOKEN']
access_token_secret = os.environ['ACCESS_TOKEN_SECRET']

auth = tweepy.OAuthHandler(api_key, api_secret)
auth.set_access_token(access_token, access_token_secret)

api = tweepy.API(auth)
client = tweepy.Client(consumer_key = api_key, consumer_secret = api_secret, access_token = access_token, access_token_secret = access_token_secret,)

# ツイート
# client.create_tweet(text = message, )

# # LINE アクセストークン忘れた
# line_bot_api = LineBotApi(os.environ['LINE_CHANNEL_ACCESS_TOKEN'])

# # 送信
# line_bot_api.broadcast(messages = [TextSendMessage(text = message),])

# 最新のURLを保存

with open('data/url.text', mode='w') as f:
    f.write(urls[0])

# 開局エリアのポリゴン作成

print('開局エリアのポリゴンを作成します...')

gdf_area_0 = gpd.read_file('A002005212020DDSWC29.geojson').fillna('')

df_nara = pd.DataFrame(list_nara)

gdf_area_1 = gpd.GeoDataFrame()

for index, row in df_nara.iterrows():

    # print(row['addr'])

    merge_data = pd.merge(gdf_area_0[gdf_area_0['addr'].str.contains(row['addr'])].reset_index(drop=True), df_nara, on='addr')

    gdf_area_1 = pd.concat([gdf_area_1, merge_data])

# 同一地域の融合
# 4Gと5Gは同一のID

gdf_dissolve = gdf_area_1.dissolve(by=['ID', 'Type', 'Date'], as_index=False)

# gdf_dissolve.columns

gdf_area_2 = gdf_dissolve[['ID', 'Date', 'Type', 'PostalCode', 'Prefecture', 'City', 'addr', 'geometry']]

gdf_area_2.to_file('data/開局エリア.geojson', driver='GeoJSON', index=False)
