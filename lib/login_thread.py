#!/usr/bin/env python
from PyQt5.QtCore import *

from bs4 import BeautifulSoup
import http.cookiejar
import datetime, time
import requests
import urllib
import re
import os



def print_log(msg='', end='\n'):
    now = datetime.datetime.now()
    t = str(now.year) + '/' + str(now.month) + '/' + str(now.day) + ' ' \
      + str(now.hour).zfill(2) + ':' + str(now.minute).zfill(2) + ':' + str(now.second).zfill(2)
    print('[' + t + '] ' + str(msg), end=end) 

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


def download_from_url(url, headers, save_path, log_txt, max_try=5, sleep_download_time=1):
    cnt_try = 0
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

                time.sleep(cnt_try)                
                print_log('\tError in downloading: ' + str(e))
                print_log('\tReconnecting... num: ' + str(cnt_try))



class LoginThread(QThread):
    # python3,pyqt5与之前的版本有些不一样
    # 通过类成员对象定义信号对象
    _signal = pyqtSignal(str)
 
    def __init__(self, info, api):
        super(LoginThread, self).__init__()
        self.info = info
        self.api = api

    def __del__(self):
        self.wait()
 
    def run(self):
        msg = self.login(self.info['uid'], self.info['pwd'])
        self._signal.emit(msg)
 
    def callback(self, msg):
        self._signal.emit(msg)

    def get_profile(self, json_result):
        profile_url = json_result.user.profile_image_urls.medium
        url_basename = os.path.basename(profile_url)
        extension = os.path.splitext(url_basename)[1]
        name = 'profile.' + extension

        self.api.download(profile_url, path='./cache', name=name)


    def login(self, uid, pwd):
        try:
            self.api.login(uid, pwd)

            json_result = self.api.user_detail(self.api.user_id)

            self.get_profile(json_result)
            if json_result.profile.is_premium:
                return 'premium'
            else:
                return 'normal'

        except Exception as e:
            return 'false'
        
        








