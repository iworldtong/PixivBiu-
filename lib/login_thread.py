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
 
    def __init__(self, cfg, parent=None):
        super(LoginThread, self).__init__()
        self.cfg = cfg

        self.max_try = self.cfg['max_try']
        self.headers = self.cfg['headers']
        self.params = self.cfg['params']
        self.datas = self.cfg['datas']
        self.cfg['session'].proxies = self.cfg['proxies']
        self.cfg['session'].headers = self.headers
        self.cfg['session'].cookies = http.cookiejar.LWPCookieJar(filename='cookies')

    def __del__(self):
        self.wait()
 
    def run(self):
        msg = self.login(self.cfg['pixiv_id'], self.cfg['password'])
        self._signal.emit(msg)
 
    def callback(self, msg):
        pass
        # self._signal.emit(msg)



    def get_profile(self):
        bs = get_bs(self.cfg['session'], self.cfg['url']['profile'], self.max_try)
        div_bs = bs.find('div',{'class':'_user-icon size-170 cover-texture'})

        if div_bs is not None:
            url = div_bs.get('style').split('\'')[-2]
            img_type = url.split('/')[-1].split('.')[-1]
            if img_type in ['jpg', 'png', 'jpeg']:
                self.profile_fn = os.path.join(self.cfg['cache_dir'], 'profile.'+img_type)
                self.headers['Referer'] = self.cfg['url']['profile']
                download_from_url(url, self.headers, self.profile_fn, self.profile_fn+'.txt', max_try=10, sleep_download_time=1)
            return True
        else:
            return False

    def check_premium(self):       
        bs = get_bs(self.cfg['session'], self.cfg['url']['pixiv'], self.max_try)
        #content = self.session.post(self.root_url, params=self.params).text
        for script in bs.find_all("script"):
            text = script.text
            if 'premium' in text and 'dataLayer' in text:                
                if text[text.find('premium')+10:text.find('premium')+13] == 'yes':
                    self.premium = True
                    return True
                else:
                    self.premium = False
                    return False

    def get_postkey(self):
        # get login page
        res = self.cfg['session'].get(self.cfg['url']['login'], params=self.params)
        # get post_key
        pattern = re.compile(r'name="post_key" value="(.*?)">')
        r = pattern.findall(res.text)
        self.datas['post_key'] = r[0]


    def already_login(self):
        # Request the user configuration interface to determine if it is logged in   
        try:   
            login_code = self.cfg['session'].get(self.cfg['url']['usrset'], allow_redirects=False).status_code                
            return True if login_code == 200 else False
        except Exception as e:
            print_log(str(e))
            return False

    def login(self, pixiv_id, password):
        print_log('logging in...')
        # set postkey
        try:
            self.get_postkey()
        except:
            pass

        self.datas['pixiv_id'] = self.cfg['pixiv_id']
        self.datas['password'] = self.cfg['password']

        # send post request to simulated login
        try:
            content = self.cfg['session'].post(self.cfg['url']['login'], data=self.datas).content
        except Exception as e:
            print_log('Failed.')
            return 'failed'

        if self.get_profile():
            # save cookies
            self.cfg['session'].cookies.save(filename=self.cfg['cookies_fn'], ignore_discard=True, ignore_expires=True)
            print_log('Successfully logged in.')
            # check premium
            if self.check_premium():
                print_log('Hello ' + self.datas['pixiv_id'] + ' (premium)!')    
                return 'premium'
            else:
                print_log('Hello ' + self.datas['pixiv_id'] + '!')     
                return 'norm'
        else:
            print_log('Login failed.')
            return 'failed'








