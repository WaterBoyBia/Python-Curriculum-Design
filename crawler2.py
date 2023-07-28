import requests
import json
import random
import pymysql
import sys
import datetime
import time
from imp import reload
from multiprocessing.dummy import Pool as ThreadPool


def datetime_to_timestamp_in_milliseconds(d):
    def current_milli_time(): return int(round(time.time() * 1000))

    return current_milli_time()


reload(sys)


def LoadUserAgents(uafile):
    uas = []
    with open(uafile, 'rb') as uaf:
        for ua in uaf.readlines():
            if ua:
                uas.append(ua.strip()[:-1])
    random.shuffle(uas)
    return uas


uas = LoadUserAgents("user_agents.txt")
head = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
    'Referer': 'http://space.bilibili.com/45388',
    'Origin': 'http://space.bilibili.com',
    'Host': 'space.bilibili.com',
    'AlexaToolbar-ALX_NS_PH': 'AlexaToolbar/alx-4.0',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
}

# 输入IP地址
proxies = {
    'http': 'http://120.26.110.59:8080',
    'http': 'http://120.52.32.46:80',
    'http': 'http://218.85.133.62:80',
}
time1 = time.time()

urls = []

'''
利用m来对所要爬取的用户id进行随机选取

'''

for m in range(1, 2):

    for i in range(m * 100, (m + 1) * 100):
        url = 'https://space.bilibili.com/' + str(i)
        urls.append(url)


    def getsource(url):
        payload = {
            '_': datetime_to_timestamp_in_milliseconds(datetime.datetime.now()),
            'mid': url.replace('https://space.bilibili.com/', '')
        }
        ua = random.choice(uas)
        head = {
            'User-Agent': ua,
            'Referer': 'https://space.bilibili.com/' + str(i) + '?from=search&seid=' + str(random.randint(10000, 50000))
        }
        mid = payload['mid']

        # 使用post会报错
        jscontent = requests \
            .session() \
            .get('https://api.bilibili.com/x/space/acc/info?mid=%s&jsonp=jsonp' % mid,
                 headers=head,
                 data=payload
                 ) \
            .text

        time2 = time.time()
        try:
            jsDict = json.loads(jscontent)
            status_code = jsDict['code'] if 'code' in jsDict.keys() else False
            if status_code == 0:
                if 'data' in jsDict.keys():
                    jsData = jsDict['data']
                    mid = jsData['mid']
                    name = jsData['name']
                    sex = jsData['sex']
                    rank = jsData['rank']
                    face = jsData['face']
                    regtimestamp = jsData['jointime']
                    regtime_local = time.localtime(regtimestamp)
                    regtime = time.strftime("%Y-%m-%d %H:%M:%S", regtime_local)

                    birthday = jsData['birthday'] if 'birthday' in jsData.keys() else 'nobirthday'
                    sign = jsData['sign']
                    level = jsData['level']
                    OfficialVerifyType = jsData['official']['type']
                    OfficialVerifyDesc = jsData['official']['desc']
                    vipType = jsData['vip']['type']
                    vipStatus = jsData['vip']['status']
                    coins = jsData['coins']
                    print("Succeed get user info: " + str(mid) + "\t" + str(time2 - time1))
                    try:
                        res = requests.get(
                            'https://api.bilibili.com/x/relation/stat?vmid=' + str(mid) + '&jsonp=jsonp').text
                        viewinfo = requests.get(
                            'https://api.bilibili.com/x/space/upstat?mid=' + str(mid) + '&jsonp=jsonp').text
                        js_fans_data = json.loads(res)
                        js_view_data = json.loads(viewinfo)
                        following = js_fans_data['data']['following']
                        fans = js_fans_data['data']['follower']
                    except:
                        following = 0
                        fans = 0

                else:
                    print('no data now')
                try:
                    print(jsDict)
                    # 输出b站用户信息
                    conn = pymysql.connect(
                        host='localhost', user='root', passwd='123456', db='bilibili', charset='utf8')
                    cur = conn.cursor()
                    cur.execute('INSERT INTO bilibili_user_info(mid, name, sex, rank, face, regtime, \
                                birthday, sign, level, OfficialVerifyType, OfficialVerifyDesc, vipType, vipStatus, \
                                coins, following, fans) \
                    VALUES ("%s","%s","%s","%s","%s","%s","%s","%s",\
                            "%s","%s","%s","%s","%s", "%s","%s","%s")'
                                %
                                (mid, name, sex, rank, face, regtime, \
                                 birthday, sign, level, OfficialVerifyType, OfficialVerifyDesc, vipType, vipStatus, \
                                 coins, following, fans))
                    conn.commit()
                except Exception as e:
                    print(e)
            else:
                print("Error: " + url)
        except Exception as e:
            print(e)
            pass

if __name__ == "__main__":
    pool = ThreadPool(1)
    try:
        results = pool.map(getsource, urls)
    except Exception as e:
        print(e)

    pool.close()
    pool.join()
