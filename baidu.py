import json
import os
import re

import execjs
import requests
from func_timeout import func_set_timeout
from jsonpath import jsonpath

from languages import baidu_fanyi_api_languages


class BaiDuFanYi:
    languages = baidu_fanyi_api_languages
    origin = 'https://fanyi.baidu.com'
    recoder = 'baidu_params.txt'
    headers = {
        "cookie": "BIDUPSID=13BB48A4E6262BD4F6F5187EF014C939; PSTM=1599303432; BAIDUID=13BB48A4E6262BD4AD5F255B6A839201:FG=1; BDORZ=B490B5EBF6F3CD402E515D22BCDA1598;",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36"
    }

    @classmethod
    # @func_set_timeout(3)
    def langdetect(self, q):
        url = f'{self.origin}/langdetect'

        data = {
            'query': q
        }
        r = requests.post(url=url, data=data, headers=self.headers)
        res = r.json()
        return res.get('lan')

    # 获取token和gtk
    @classmethod
    def get_token_and_gtk0(self):
        response = requests.get(url=self.origin, headers=self.headers)
        pattern_token = re.compile(r"window\['common'\]\W*?=\W*?{\W*?.*?token.*?:.*?'(\w+)',")
        pattern_gtk = re.compile(r"window.gtk\W*?=\W*?'(.*?)'")
        str = response.content.decode()
        return pattern_token.search(str).group(1), pattern_gtk.search(str).group(1)

    # 获取token和gtk
    @classmethod
    def get_token_and_gtk(self):
        if os.path.exists(self.recoder):
            with open(self.recoder, 'r', encoding='utf8') as f:
                line = f.read().strip()
                if line:
                    data = json.loads(line)
                else:
                    data = self.r4params()
        else:
            data = self.r4params()
        return data

    @classmethod
    def r4params(self):
        r = requests.get(url=self.origin, headers=self.headers)
        pattern_token = re.compile(r"window\['common'\]\W*?=\W*?{\W*?.*?token.*?:.*?'(\w+)',")
        pattern_gtk = re.compile(r"window.gtk\W*?=\W*?'(.*?)'")
        str = r.content.decode()
        token, gtk = pattern_token.search(str).group(1), pattern_gtk.search(str).group(1)
        data = dict(token=token, gtk=gtk)
        self.recode_gtk_token(data)
        return data

    @classmethod
    def recode_gtk_token(self, data):
        with open(self.recoder, 'w', encoding='utf8') as f:
            f.write(json.dumps(data))

    # 获取sign
    @classmethod
    def get_sign(self, query, gtk):
        with open('baidu_fangi.js', 'r', encoding='utf-8') as f:
            ctx = execjs.compile(f.read())
        return ctx.call('get_sign', query, gtk)

    @classmethod
    def translate(self, q, to='zh'):
        lang = self.langdetect(q)
        token_and_gtk_data = self.get_token_and_gtk()
        token = token_and_gtk_data.get('token')
        gtk = token_and_gtk_data.get('gtk')
        sign = self.get_sign(q, gtk)
        data = {
            'from': lang,
            'to': to,
            'query': q,
            'transtype': 'realtime',
            'simple_means_flag': '3',
            'sign': sign,
            'token': token,
            'domain': 'common',
        }
        url = f"{self.origin}/v2transapi"
        r = requests.post(url=url, data=data, headers=self.headers)
        res = r.json()
        text = jsonpath(res, '$.trans_result.data[0].dst')[0]
        from_lang = jsonpath(res, '$.trans_result.from')[0]
        to_lang = jsonpath(res, '$.trans_result.to')[0]
        return dict(
            text=text,
            query=q,
            from_lang=from_lang,
            to_lang=to_lang,
            from_langCN=self.languages[from_lang],
            to_langCN=self.languages[to_lang]
        )


if __name__ == "__main__":
    q = 'He is promoted to be the manager'
    lan = BaiDuFanYi.translate(q)
    print(lan)
