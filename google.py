import os
import re
from urllib.parse import urlencode

import execjs
import requests

from languages import google_translate_api_languages


class GoogleTranslater:
    languages = google_translate_api_languages
    recoder = 'tkk.txt'
    referer = 'https://translate.google.cn/'

    api = f'{referer}translate_a/single?dt=at&dt=bd&dt=ex&dt=ld&dt=md&dt=qca&dt=rw&dt=rm&dt=sos&dt=ss&dt=t&'

    headers = {
        'accept': '*/*',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'dnt': '1',
        'referer': referer,
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.162 Safari/537.36',
    }

    @classmethod
    def get_tk(self, q):
        with open('google_translate.js', 'r', encoding='utf8') as f:
            js_str = f.read()
        TKK = self.get_TKK()
        ctx = execjs.compile(js_str)
        res = ctx.call("get_tk", q, TKK)
        tk = res.replace('&tk=', '')
        return tk

    @classmethod
    def translate_data(self, q, to_lang='zh-cn'):
        tk = self.get_tk(q)
        params = {
            'client': 'webapp',
            'sl': 'auto',
            'tl': to_lang,
            'hl': 'zh-CN',
            'pc': '1',
            'otf': '1',
            'ssel': '0',
            'tsel': '0',
            'xid': '45662847',
            'kc': '1',
            'tk': tk,
            'q': q
        }

        qs = urlencode(params)
        url = self.api + qs
        r = requests.get(url=url, headers=self.headers)
        data = r.json()
        return data

    @classmethod
    def get_TKK(self):
        if not os.path.exists(self.recoder):
            tkk = self.get_tkk_from_html()
        else:
            with open(self.recoder, 'r', encoding='utf8') as f:
                tkk = f.read().strip()
                if not tkk:
                    tkk = self.get_tkk_from_html()
        return tkk

    @classmethod
    def recode_tkk(self, tkk):
        with open(self.recoder, 'w', encoding='utf8') as f:
            f.write(tkk)

    @classmethod
    def get_tkk_from_html(self):
        url = self.referer
        r = requests.get(url=url, headers=self.headers)
        html = r.text
        tkk = re.findall(r"tkk:.(\d+\.\d+).+,", html)[0]
        self.recode_tkk(tkk)
        return tkk

    @classmethod
    def translate(self, q, to_lang='zh-cn'):
        translate_data = self.translate_data(q, to_lang)
        from_lang = translate_data[2]
        t1 = translate_data[0]
        ts = [i[0] for i in t1 if i[0]]
        text = ''.join(ts)
        return dict(
            text=text,
            query=q,
            from_lang=from_lang,
            to_lang=to_lang,
            from_langCN=self.languages[from_lang],
            to_langCN=self.languages[to_lang],
        )


if __name__ == "__main__":
    q = 'The water is polluted. And the fishes are dying.'
    # q = ' It makes us excited. That is good.'
    data = GoogleTranslater.translate(q, to_lang='zh-cn')
    print(data)

