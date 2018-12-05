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

def print_log(msg='', end='\n'):
    now = datetime.datetime.now()
    t = str(now.year) + '/' + str(now.month) + '/' + str(now.day) + ' ' \
      + str(now.hour).zfill(2) + ':' + str(now.minute).zfill(2) + ':' + str(now.second).zfill(2)
    print('[' + t + '] ' + str(msg), end=end) 

def download_from_url(url, headers, save_path, log_txt, max_try=5, sleep_download_time=1):
    cnt_try = 0
    socket.setdefaulttimeout(10) 
    while max_try > cnt_try:
        try:                            
            req = urllib.request.Request(url, headers=headers)                        
            page = urllib.request.urlopen(req)
            content = page.read()

            with open(save_path, 'wb') as f:
                f.write(content)            
            time.sleep(sleep_download_time)
            return True
        except Exception as e:
            cnt_try += 1
            if cnt_try > max_try:
                if not os.path.isfile(log_txt):
                    with open(log_txt, 'w') as f:
                        pass
                with open(log_txt, 'a') as f:
                    f.write(url + '\n')
                    print('\tDownload progress on <' + url + '> failed!')
                    print('\t', e)
                return False
            else:           
                # !!! 不完善的地方     
                if '404' in str(e):                    
                    if   'jpg' in url: url = url.replace('jpg', 'png')
                    elif 'png' in url: url = url.replace('png', 'jpg')
                    if cnt_try == 1:
                        max_try *= 2
                        continue
                elif 'timed out' in str(e):
                    cnt_try = 0

                time.sleep(cnt_try)                
                print_log('\tError in downloading: ' + str(e))
                print_log('\tReconnecting... num: ' + str(cnt_try))

def get_bs(session, url, max_try=5):
    cnt_try = 0
    while max_try > cnt_try:
        try:
            #content = self.session.get(url, allow_redirects=False).content 
            content = session.get(url).content 
            bs = BeautifulSoup(content, "lxml")
            # bs = BeautifulSoup(content)
            return bs
        except Exception as e:
            if cnt_try == max_try:
                raise e
            else:
                cnt_try += 1
                time.sleep(cnt_try)
                print_log('\t' + str(e) + '\n\tReconnecting... num: ' + str(cnt_try))
    return None


class DownloadThread(QThread):
    # python3,pyqt5与之前的版本有些不一样
    # 通过类成员对象定义信号对象
    _signal = pyqtSignal(str)
 
    def __init__(self, cfg, parent=None):
        super(DownloadThread, self).__init__()
        self.cfg = cfg
        self._quit = False
        self.worker_n = 10

        self.headers = self.cfg['headers']
        self.params = self.cfg['params']
        self.datas = self.cfg['datas']
        self.cfg['session'].proxies = self.cfg['proxies']
        self.cfg['session'].headers = self.headers

        self.max_try = self.cfg['max_try']
        self.sleep_download_time = self.cfg['sleep_download_time']

    def __del__(self):
        self.wait()

    def run(self):
        try:            
            self.cfg['session'].cookies.load(filename=self.cfg['cookies_fn'], ignore_discard=True)
        except Exception as e:
            self._signal.emit('nocookie')
            return None

        self.headers = self.cfg['headers']
        self.min_bookmarkCount = self.cfg['popular_lower']
        self.max_bookmarkCount = self.cfg['popular_upper']
        self.download_dir = os.path.join(self.cfg['save_dir'], 'download')
        self.cache_dir = self.cfg['cache_dir']

        if self.cfg['search_type']=='tag':
            self.run_by_tag()
        else:
            self.run_by_usr()

    def run_by_usr(self):
        for usr_i, usr in enumerate(self.cfg['search_list']):
            search_url = 'https://www.pixiv.net/member_illust.php?id=4752417'#self.cfg['url']['pixiv'] + '/member_illust.php?type=illust&id=' + str(usr)
            bs = get_bs(self.cfg['session'], search_url, self.max_try)
            li_bs = bs.findAll('li', {'class': 'bVmoIS4'})
            cnt_bs = bs.find('div', {'class': 'sc-kafWEX bThlrn'})
            print(search_url)
            print(bs)
            print(bs.find('div', {'id': 'root'}))
            print(li_bs)

            if li_bs is None:
                self._signal.emit('done')
                return None
            else:
                total_n = int(cnt_bs.text)

            # 目录、缓存等
            usr_d = validate_title(usr)
            self.cur_dir = os.path.join(self.download_dir, usr_d)
            if not os.path.exists(self.cur_dir):
                os.makedirs(self.cur_dir)
            self.cache_path = os.path.join(self.cache_dir, usr_d + '.txt')
            if not os.path.exists(self.cache_path):
                with open(self.cache_path, 'w') as f:
                    pass
            self.log_txt = os.path.join(self.cache_dir, 'log.txt')
            if not os.path.exists(self.log_txt):
                with open(self.log_txt, 'w') as f:
                    pass

            
            # work by pages
            cur_n = 0
            page_n = 0
            while True:
                page_n += 1
                search_url += str(page_n)
                bs = get_bs(self.cfg['session'], search_url, self.max_try)
                li_bs = bs.findAll('li', {'class': 'bVmoIS4'})
                if li_bs is None:
                    break

                for li in li_bs:
                    href = li.find('a', {'class': 'sc-hSdWYo NeoCZ'}).get('href')
                    print(href)
                    break
                break

        self._signal.emit('done')


    def run_by_tag(self): 
        # work by tags
        tag_n = len(self.cfg['search_list'])
        for tag_i, tag in enumerate(self.cfg['search_list']):
            total_n = self.get_tag_total_cnt(tag)
            # 目录、缓存等
            tag_d = validate_title(tag)
            self.cur_dir = os.path.join(self.download_dir, tag_d)
            if not os.path.exists(self.cur_dir):
                os.makedirs(self.cur_dir)
            self.cache_path = os.path.join(self.cache_dir, tag_d + '.txt')
            if not os.path.exists(self.cache_path):
                with open(self.cache_path, 'w') as f:
                    pass
            self.log_txt = os.path.join(self.cache_dir, 'log.txt')
            if not os.path.exists(self.log_txt):
                with open(self.log_txt, 'w') as f:
                    pass

            # work by pages
            page_n = 1
            cur_n = 0
            break_search = False
            while page_n is not None:
                search_url = self.cfg['url']['pixiv'] + '/search.php?s_mode=s_tag'
                if self.cfg['premium']:
                    search_url += '&order=popular_d'
                search_url += '&word=' + tag + '&p=' + str(page_n)
                bs = get_bs(self.cfg['session'], search_url, self.max_try)

                for input_bs in bs.find_all('input'):
                    data_items = input_bs.get('data-items')
                    if data_items != None:                        
                        break
                items = re.findall(r"[{](.*?)[}]", data_items)
                items_n = len(items)

                # work by workers
                for start in range(0, items_n, self.worker_n):
                    end = min(start+self.worker_n, items_n)
                    tmp_items = items[start:min(start+self.worker_n, items_n)]
                    mt_list = []
                    for item in tmp_items:
                        # item info
                        illustId = int(re.findall(r"\"illustId\":\"(.*?)\"", item)[0])
                        bookmarkCount_bs = re.findall(r"\"bookmarkCount\":(.*?),", item)
                        if bookmarkCount_bs is not None and len(bookmarkCount_bs) > 0:
                            bookmarkCount = int(bookmarkCount_bs[0])
                        else:
                            bookmarkCount = 0
                        if self.min_bookmarkCount is not None and self.min_bookmarkCount > bookmarkCount:
                            if self.cfg['premium']:
                                break_search = True
                            continue
                        if self.max_bookmarkCount is not None and self.max_bookmarkCount < bookmarkCount:
                            if self.cfg['premium']:
                                break_search = True
                            continue

                        # url info
                        if 1 > len(re.findall(r"\"url\":\"(.*?)\"", item)):
                            continue
                        small_url = str(re.findall(r"\"url\":\"(.*?)\"", item)[0]).replace('\\',  '')        
                        referer_url = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=' + str(illustId)    
                        url = 'https://i.pximg.net/img-original/img/' + small_url.split('/img/')[-1].replace('_master1200', '')
                                        
                        # save info
                        fname = str(bookmarkCount) + ' (' + str(illustId) +')' + '.' + url.split('.')[-1]
                        fpath = os.path.join(self.cur_dir, fname)

                        # Multithreading to speed up                    
                        mt = self.ms_download_by_items(self, illustId, fname, fpath, url, referer_url)
                        mt.start()
                        mt_list.append(mt)

                    # wait all work to be finished
                    for mt in mt_list:
                        mt.join()

                    # 根据当前工作轮数更新进度条
                    cur_n += end - start
                    msg = (100 * (tag_i + cur_n / total_n)) // tag_n
                    self._signal.emit(str(int(min(msg, 100))))

                    if self._quit:
                        self._signal.emit('done')
                        return None
                    
                if break_search:
                    cur_n = total_n
                    msg = (100 * (tag_i + cur_n / total_n)) // tag_n
                    self._signal.emit(str(int(min(msg, 100))))

                # check next page
                if self.check_next_page(bs):
                    page_n += 1
                else:
                    break

        self._signal.emit('done')

 
    def callback(self, msg):
        if msg == 'stop':
            self._quit = True

    def get_tag_total_cnt(self, tag):
        search_url = self.cfg['url']['pixiv'] + '/search.php?s_mode=s_tag'
        if self.cfg['premium']:
            search_url += '&order=popular_d'
        search_url += '&word=' + tag
        bs = get_bs(self.cfg['session'], search_url, self.max_try)
        total_n = int(bs.find('span',{'class':'count-badge'}).text[:-1])
        return total_n

    def check_next_page(self, bs):
        pc_bs = bs.find('div', {'class': 'pager-container'})
        if pc_bs != None:
            span_bs = pc_bs.find_all('span')
            if span_bs != None:
                for span in span_bs:
                    if span.get('class')[0] == 'next':
                        return True
        return False

    class ms_download_by_items(threading.Thread):
        def __init__(self, father, illustId, fname, fpath, url, referer_url=None):
            threading.Thread.__init__(self)            
            self.father = father            
            self.illustId = illustId
            self.fname = fname
            self.fpath = fpath
            self.url = url
            self.referer_url = referer_url

        def run(self):                                
            # load cache 
            with open(self.father.cache_path, 'r') as f: 
                cache = [line.strip() for line in f.readlines()]            

            # download
            with open(self.father.cache_path, 'a') as f:            
                if str(self.illustId) in cache:
                    print_log('\t\tImg id: ' + str(self.illustId) + ' already exists.')
                    return None                                
                try:
                    if self.referer_url is not None:
                        self.father.headers['Referer'] = self.referer_url
                    res = download_from_url(self.url, self.father.headers, self.fpath, self.father.log_txt, self.father.max_try, self.father.sleep_download_time)
                    time.sleep(self.father.sleep_download_time)
                    if res:
                        print_log('\t\tImg: ' + self.fname + ' downloaded.')  
                        f.write(str(self.illustId) + '\n')    
                        return True
                    else:
                        return False             

                except Exception as e:
                    with open(self.father.log_txt, 'a') as log_f:
                        log_f.write(str(e) + ' : ' + self.url + '\n')
                    print_log(str(e) + ' : ' + self.url)
                    return False


