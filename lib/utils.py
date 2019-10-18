#!/usr/bin/env python
import os
from PyQt5 import QtWidgets
from bs4 import BeautifulSoup
import requests
import json


def load_qss_from_txt(widget, txt):
    with open(txt) as f:
        qss = f.readlines()
        qss =''.join(qss).strip('\n')
    widget.setStyleSheet(qss)


def fetch_page(keyword, page=1):
    url = 'https://api.pixivic.com/illustrations?'
    headers = {
        'Origin': 'https://pixivic.com',
        'Referer': 'https://pixivic.com/popSearch',
        'Sec-Fetch-Mode': 'cors',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36',
    }
    params = {
        'keyword': keyword,
        'page': page,
    }

    sess = requests.Session()
    sess.headers = headers
    content = sess.get(url, params=params).content 
    bs = BeautifulSoup(content, 'lxml')
    ret = bs.body.p.get_text()

    msg, data = None, None
    try:
        ret = json.loads(ret)
        msg = ret['message']
        data = ret['data']
    except Exception as e:
        msg = e
        
    return msg, data
