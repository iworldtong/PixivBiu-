#!/usr/bin/env python
from PyQt5.QtCore import *

from bs4 import BeautifulSoup
import http.cookiejar
import datetime,time
import threading
import requests
import urllib
import re
import os
import socket



def validate_title(title):
    ''' 判断windows下改文件名是否合法并修改 '''
    rstr = r"[\/\\\:\*\?\"\<\>\|]"  # '/ \ : * ? " < > |'
    new_title = re.sub(rstr, "", title)  # 替换为下划线
    return new_title


class DownloadThread(QThread):
    # python3,pyqt5与之前的版本有些不一样
    # 通过类成员对象定义信号对象
    _signal = pyqtSignal(str)
 
    def __init__(self, api, cfg, parent=None):
        super(DownloadThread, self).__init__()
        self.api = api
        self.cfg = cfg

        self._quit = False

        self.download_dir = os.path.join(cfg['save_dir'], validate_title(cfg['key']))
        if not os.path.exists(self.download_dir):
            os.makedirs(self.download_dir)
        
    def __del__(self):
        self.wait()

    def run(self):

        if self.cfg['type']=='tag':
            self.run_by_tag()
        else:
            self.run_by_usr()


    def run_by_page_ms(self, illusts):
        mt_list = []
        for illust in illusts:
            mt = self.ms_download_by_items(self, illust)
            mt.start()
            mt_list.append(mt)

        # wait all work to be finished
        for mt in mt_list:
            mt.join()


    def run_by_usr(self):
        pass


    def run_by_tag(self): 
        # work by tags
        page_i = 1

        json_result = self.api.search_illust(self.cfg['key'], search_target='partial_match_for_tags')
        while True:
            print('page num: %d' %(page_i))
            page_i += 1

            self.run_by_page_ms(json_result['illusts'])
            time.sleep(self.cfg['sleep_download_time'])

            if json_result.next_url is not None:
                next_qs = self.api.parse_qs(json_result.next_url)
                json_result = self.api.search_illust(**next_qs)
            else:
                break

            if self._quit:
                break

        self._signal.emit('done')

 
    def callback(self, msg):
        if msg == 'stop':
            self._quit = True

    class ms_download_by_items(threading.Thread):
        def __init__(self, father, illust):
            threading.Thread.__init__(self)            
            self.father = father
            self.illust = illust

        def url2name(self, url, title):
            url_basename = os.path.basename(url)
            extension = os.path.splitext(url_basename)[1]
            name = "%s%s" % (title, extension)
            name = validate_title(name)
            return name

        def run(self):   
            try:
                if self.illust.total_bookmarks > self.father.cfg['min_popular']:
                    image_url = self.illust.image_urls.large
                    name = self.url2name(image_url, str(self.illust.id))
                    self.father.api.download(image_url, path=self.father.download_dir, name=name)     

                    if isinstance(self.illust.meta_single_page, list):
                        for i, j in enumerate(self.illust.meta_single_page):  
                            image_url = j['image_urls']['large']  
                            name = self.url2name(image_url, str(self.illust.id)+'_'+str(i+1))
                            self.father.api.download(image_url, path=self.father.download_dir, name=name) 
            except Exception as e:
                print(e)
                
            


