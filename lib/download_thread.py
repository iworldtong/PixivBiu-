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

from lib import *


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
            mt = self.ms_download_by_illust(self, illust)
            mt.start()
            mt_list.append(mt)

        # wait all work to be finished
        for mt in mt_list:
            mt.join()


    def run_by_usr(self):
        pass


    def run_by_tag(self): 
        # work by tags
        # json_result = self.api.search_illust(self.cfg['key'], search_target='partial_match_for_tags')
        
        for page_i in range(self.cfg['page_start'], self.cfg['page_num']+self.cfg['page_start']):
            print('keyword: %s,page num: %d' %(self.cfg['key'], page_i))
            msg, illusts = fetch_page(self.cfg['key'], page_i)

            if msg != '搜索结果获取成功':
                print('\terror: '+msg)
                continue 

            self.run_by_page_ms(illusts)

            time.sleep(self.cfg['sleep_download_time'])

            # if json_result.next_url is not None:
            #     next_qs = self.api.parse_qs(json_result.next_url)
            #     json_result = self.api.search_illust(**next_qs)
            # else:
            #     break

            if self._quit:
                break

        self._signal.emit('done')


    def callback(self, msg):
        if msg == 'stop':
            self._quit = True


    class ms_download_by_illust(threading.Thread):
        def __init__(self, father, illust):
            threading.Thread.__init__(self)            
            self.father = father
            self.illust = illust

        def url2name(self, url):
            title = url.split('/')[-1].split('.')[0]
            url_basename = os.path.basename(url)
            extension = os.path.splitext(url_basename)[1]
            name = "%s_%d%s" % (title, self.illust.total_bookmarks, extension)
            name = validate_title(name)
            return name

        def run(self):   
            try:
                self.illust = self.father.api.illust_detail(self.illust['id'])['illust']
                page_cnt = self.illust['page_count']
                if page_cnt == 1:
                    image_url = self.illust.meta_single_page.get('original_image_url', 
                                                                self.illust.image_urls.large)
                    self.download(image_url, path=self.father.download_dir)
                else:
                    for i in range(page_cnt):
                        image_url = self.illust.meta_pages[i]['image_urls'].get('original', 
                                                                self.illust.meta_pages[i]['image_urls']['large'])
                        self.download(image_url, path=self.father.download_dir)      
                
                # if self.illust.total_bookmarks > self.father.cfg['min_popular']:
                #     image_url = self.illust.image_urls.large
                #     image_url = self.illust.meta_single_page.get('original_image_url', self.illust.image_urls.large)
                #     name = self.url2name(image_url)                    
                #     self.download(image_url, path=self.father.download_dir, name=name)

                #     if isinstance(self.illust.meta_single_page, list):
                #         for i, j in enumerate(self.illust.meta_single_page):  
                #             image_url = j['image_urls']['original']  
                #             name = self.url2name(image_url)
                #             self.download(image_url, path=self.father.download_dir, name=name)
                    
            except Exception as e:
                print(e)

        def download(self, image_url, path):
            name = self.url2name(image_url) 
            try:
                fl = os.listdir(path)
                old_f = None
                for f in fl:
                    if name in f:
                        old_f = f   
                
                if old_f is None:
                    self.father.api.download(image_url, path=path, name=name) 
                    print('\tdownload: '+name)
                else:
                    old_mark = int(old_f.split('.')[0].split('_')[-1])
                    if self.illust.total_bookmarks != old_mark:
                        new_f = old_f.replace(str(old_mark), str(self.illust.total_bookmarks))
                        os.rename(os.path.join(path, old_f),
                                  os.path.join(path, new_f))

                        print('\trename: %s -> %s' %(old_f, new_f))
                    else:
                        print('\tskip: '+name)

            except Exception as e:
                print('\tfailed: '+name)
                pass                
            


