#!/usr/bin/env python
#-*- coding:utf8 -*-

import os
import random
import copy
import re
import sys
from datetime import datetime, timedelta
import time
import json
import base64
import threading
import string

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By 


import requests
from requests.adapters import HTTPAdapter
from requests_toolbelt import MultipartEncoder
from urllib.parse import urlencode
from urllib.parse import urlparse

from mailbot import MailBot
from slogging import slog
from config import CONFIG

def decorator_try_except(func):
    def new_func(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            slog.warning("Got error! {0}".format(repr(e)))
            return 'EEE'
    return new_func

class TOPARGUS(object):
    def __init__(self, username, password, host, name, net_info, mydriver = None):
        slog.info('TOPARGUS init')
        self.username = username
        self.password = password
        self.host = host
        self.url_prefix = 'http://{0}:{1}@{2}'.format(self.username, self.password, self.host)
        self.name = name
        self.net_info = net_info

        # start mailbot ,try to login
        self.mailbot = MailBot().login(10)
        self.ss = requests.Session()
        self.ss.auth = (username, password)
        self.ss.mount('http://', HTTPAdapter(max_retries=3))
        self.ss.mount('https://', HTTPAdapter(max_retries=3))

        if mydriver == None:
            #_____________________启动参数___________________________
            options = webdriver.ChromeOptions()
            options.add_argument('headless')
            options.add_argument('disable-gpu')
            #options.add_argument("window-size=1220,1080")
            options.add_argument("window-size=1440,1280")
            options.add_argument("start-maximized")
            options.add_argument("no-sandbox")

            #_____________________代理参数___________________________
            desired_capabilities = options.to_capabilities()
            desired_capabilities['acceptSslCerts'] = True
            desired_capabilities['acceptInsecureCerts'] = True
            desired_capabilities['proxy'] = {
                "httpProxy": None,
                "ftpProxy": None,
                "sslProxy": None,
                "noProxy": None,
                "proxyType": "MANUAL",
                "class": "org.openqa.selenium.Proxy",
                "autodetect": False,
            }

            #_____________________启动浏览器___________________________
            self.driver = webdriver.Chrome(
                options=options,
                #executable_path=CHROME_DRIVER_PATH,
                desired_capabilities = desired_capabilities)
            self.driver.set_page_load_timeout(30)
            #self.driver.manage().window().maximize()
        else:
            self.driver = mydriver
        return


    def __del__(self):                                                                                         
        slog.info('TOPARGUS uninit')
        try:
            """ Destroy the web browser """
            self.driver.close()
            self.driver.quit()
        except Exception as e:
            slog.warning("quit Exception: ", e)
        finally:
            return

    def get_topargus_name(self):
        return self.name

    def get_topargus_net_info(self):
        return self.net_info

    def wait_for_ajax_data(self, wait = 0):                                                                              
        """                                                                                                    
        Waiting for the loading of ajax data filed to table
        """                                                                                                    
        try:                                                                                                   
            WebDriverWait(self.driver, wait, 0.5).until(EC.presence_of_element_located((By.CLASS_NAME, 'xxxxx')))
            return True                                                                                        
        except:                                                                                                
            return False                                                                                       
    def default_index(self):
        url = '{0}/index.html'.format(self.url_prefix)
        return url

    def randomString(self, stringLength=5):
        """Generate a random string of fixed length """
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(stringLength))

    def load_url(self, url, wait = 0):
        slog.info("访问 url:{0}".format(url))
        try:                                                                                                   
            self.driver.get(url)
        except Exception as e:                                                                                 
            slog.warning("url:{0} cannot be reached:{1}".format(url,e))
            return False, None

        if not os.path.exists('./temp'):
            os.mkdir('./temp')
        page = './temp/{0}.png'.format(self.randomString(10))
        if wait != 0:
            self.wait_for_ajax_data(wait)
        self.driver.save_screenshot(page)
        return True, page

    def home(self):
        slog.info("加载首页")
        url = '{0}/index.html'.format(self.url_prefix)
        return self.load_url(url = url, wait = 10)

    def system(self, cpu = False, send_bandwidth = False, recv_bandwidth = False):
        slog.info("加载系统情况页面")
        if cpu == True:
            url = '{0}/system.html?field=cpu'.format(self.url_prefix)
            self.load_url(url = url)

        if send_bandwidth == True:
            url = '{0}/system.html?field=send_bandwidth'.format(self.url_prefix)
            self.load_url(url = url)

        if recv_bandwidth== True:
            url = '{0}/system.html?field=recv_bandwidth'.format(self.url_prefix)
            self.load_url(url = url)

        return True,None

    def alarm(self, low = False, middle = False, high = True, all_alarm = False):
        slog.info("加载告警事件页面")
        if all_alarm == True:
            url = '{0}/alarm.html'.format(self.url_prefix)
            return self.load_url(url = url, wait = 10)

        if high == True:
            url = '{0}/alarm.html?priority=2'.format(self.url_prefix)
            return self.load_url(url = url, wait = 10)

        if middle == True:
            url = '{0}/alarm.html?priority=1'.format(self.url_prefix)
            return self.load_url(url = url, wait = 10)

        if low == True:
            url = '{0}/alarm.html?priority=0'.format(self.url_prefix)
            return self.load_url(url = url, wait = 10)
        
        return False, None

    def packet(self, dest_node_id = None):
        slog.info("加载收包情况页面")
        url = '{0}/packet.html'.format(self.url_prefix)
        if dest_node_id:
            url = '{0}/packet.html?dest_node_id={1}'.format(self.url_prefix, dest_node_id)
        return self.load_url(url = url, wait = 30)

    def network(self, network_id = None):
        slog.info("加载P2P网络情况页面")
        url = '{0}/network.html'.format(self.url_prefix)
        if network_id:
            url = '{0}/network.html?network_id={1}'.format(self.url_prefix, network_id)
        return self.load_url(url = url, wait = 30)

    def go_top(self):
        self.driver.execute_script('var q=document.documentElement.scrollTop=0')
        time.sleep(2)

    # 没有使用 selenium 
    def alarm_api(self):
        end = int(time.time() * 1000)
        begin = end - 10 * 60 * 1000   # latest 10 min
        url = 'http://{0}/api/web/system_alarm_info?public_ip_port=&priority=2&begin={1}&end={2}&limit=200&page=1'.format(self.host, begin, end)
        my_headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Host': self.host,
                    'Referer': self.url_prefix + '/index.html',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                    }
        '''
        {"error":"OK","results":{"size":0,"system_alarm_info":[]},"status":0,"total":0}
        '''

        results = None
        try:
            res = self.ss.get(url, headers = my_headers)
            if res.status_code == 200:
                results = res.json().get('results')
        except Exception as e:
            slog.warning("catch exception:{0}".format(e))

        slog.debug("get result:{0}".format(json.dumps(results)))
        return results

    # 没有使用 selenium 
    def node_info_api(self):
        url = 'http://{0}/api/web/node_info/?status=offline'.format(self.host)
        my_headers = {
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Host': self.host,
                    'Referer': self.url_prefix + '/index.html',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                    }
        '''
        {"error":"OK","results":{"node_info":[],"node_size":0},"status":0}
        '''

        results = None
        try:
            res = self.ss.get(url, headers = my_headers)
            if res.status_code == 200:
                results = res.json().get('results')
        except Exception as e:
            slog.warning("catch exception:{0}".format(e))

        slog.debug("get result:{0}".format(json.dumps(results)))
        return results

    # 没有使用 selenium 
    def packet_drop_api(self):
        end = int(time.time() * 1000)
        begin = end - 10 * 60 * 1000   # latest 10 min
        url = 'http://{0}/api/web/packet_drop/?begin={1}&end={2}'.format(self.host, begin, end)
        my_headers = {
                    'Accept': 'application/json, text/javascript, */*; q=0.01',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Host': self.host,
                    'Referer': self.url_prefix + '/index.html',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36',
                    'X-Requested-With': 'XMLHttpRequest',
                    }
        '''
        {"error":"OK","results":[[1579441355398,1.8],[1579441415398,3.6],[1579441475398,0.0]],"status":0}
        '''

        results = None
        try:
            res = self.ss.get(url, headers = my_headers)
            if res.status_code == 200:
                results = res.json().get('results')
        except Exception as e:
            slog.warning("catch exception:{0}".format(e))

        slog.debug("get result:{0}".format(json.dumps(results)))
        return results




@decorator_try_except
def run_api(topargus, mbot):
    '''
    def alarm_api(self):
    def node_info_api(self):
    def packet_drop_api(self):
    '''
    slog.debug("run_api alive")
    subject = 'TOPARGUS 高优先级告警事件！'
    contents = [
            'TOPARGUS_host: {0}'.format(topargus.default_index()),
            'TOPARGUS_name: {0}'.format(topargus.get_topargus_name()),
            'TOPARGUS_info: {0}'.format(topargus.get_topargus_net_info()),
            ]

    results = topargus.alarm_api()
    if results:
        #if results.get('system_alarm_info') and len(results.get('system_alarm_info')) > 0:
        if True:
            slog.warning('get alarm high level info')
            ret = topargus.alarm(high = True)  # (True, filename)
            ret = list(ret)
            if len(ret) == 2 and ret[1] != None:
                if ret[1].endswith('png'):  # picture
                    pic = mbot.make_pic_inline(ret[1])
                    contents.append("[节点离线]")
                    contents.append(pic)
                    contents.append("\n\n\n")


    results = topargus.node_info_api()
    if results:
        #if results.get('node_info') and len(results.get('node_info')) > 0:
        if True:
            slog.warning('get offline node_info')
            contents.append("[离线节点列表]")
            contents.append(json.dumps(results.get('node_info')))
            contents.append("\n\n\n")
    
    # results = topargus.packet_drop_api()

    contents.append("MAIL END")
    ret = mbot.send_mail(CONFIG.get('target_email_adr'), subject, contents)
    if ret:
        slog.info('send alarm_api mail to {0} ok'.format(json.dumps(CONFIG.get('target_email_adr'))))
        return True
    else:
        slog.warning('send alarm_api mail to {0} error'.format(json.dumps(CONFIG.get('target_email_adr'))))
        return False

def th_api(topargus, mbot):
    while True:
        #time.sleep(10 * 60)  # 10 min
        time.sleep(5 * 60)  # 10 min
        run_api(topargus, mbot)
    return

# add dingtalk robot api
def send_info_dingding(sendstr, receiver = None):
    if receiver:
        receiverlist = receiver.split(',')
    else:
        receiverlist = []
    webhook = 'https://oapi.dingtalk.com/robot/send?access_token=7fef13e2296ec23c243ea452f43f2d977924c06aa4b218ca3802b33d7d3ba07b'
    header = {"Content-Type": "application/json"}
    text_data = json.dumps({"msgtype": "text",
            "at": {
                  "atMobiles": receiverlist,
            "isAtAll": False
           },
            "text":
                {"content": "{}".format(sendstr)}
            })


    title = "# **-----top-argus monitor system-----**\n\n"
    markdown_data = json.dumps({
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": title + sendstr
        },
        "at": {
           "atMobiles": receiverlist,
           "isAtAll": False
        }
        })

    try:
        r = requests.post(webhook, headers = header, data = markdown_data, timeout = 10)
        print(r.text)
    except Exception as e:
        print('catch exception:{0}'.format(e))

@decorator_try_except
def run_page(topargus, mbot):
    slog.debug("run_page alive")
    subject = 'TOPARGUS 常规定时监控'
    contents = [
            'TOPARGUS_host: {0}'.format(topargus.default_index()),
            'TOPARGUS_name: {0}'.format(topargus.get_topargus_name()),
            'TOPARGUS_info: {0}'.format(topargus.get_topargus_net_info()),
            ]

    ret = topargus.home()
    ret = list(ret)
    if len(ret) == 2 and ret[1] != None:
        if ret[1].endswith('png'):  # picture
            pic = mbot.make_pic_inline(ret[1])
            contents.append("[首页]")
            contents.append(pic)
            contents.append("\n\n\n")

            # add for dingtalk robot
            mainnet_html_dir = '/usr/local/smaug/nginx/webapp/mainnet/home.png'
            from shutil import copyfile
            copyfile(ret[1], mainnet_html_dir)
            mainnet_url = 'http://142.93.126.168/mainnet/home.png'
            markdown_text = '''## 全网丢包率情况\n
![](http://142.93.126.168/mainnet/home.png)\n
详情查看: [http://smaug:smaug_6666@142.93.126.168/index.html](http://smaug:smaug_6666@142.93.126.168/index.html)'''
            send_info_dingding(markdown_text, None):


    ret = topargus.alarm()
    ret = list(ret)
    if len(ret) == 2 and ret[1] != None:
        if ret[1].endswith('png'):  # picture
            pic = mbot.make_pic_inline(ret[1])
            contents.append("[告警页面]")
            contents.append(pic)
            contents.append("\n\n\n")

    ret = topargus.packet()
    ret = list(ret)
    if len(ret) == 2 and ret[1] != None:
        if ret[1].endswith('png'):  # picture
            pic = mbot.make_pic_inline(ret[1])
            contents.append("[收包情况]")
            contents.append(pic)
            contents.append("\n\n\n")

    ret = topargus.network()
    ret = list(ret)
    if len(ret) == 2 and ret[1] != None:
        if ret[1].endswith('png'):  # picture
            pic = mbot.make_pic_inline(ret[1])
            contents.append("[P2P网络]")
            contents.append(pic)
            contents.append("\n\n\n")

    contents.append("MAIL END")
    ret = mbot.send_mail(CONFIG.get('target_email_adr'), subject, contents)
    if ret:
        slog.info('send alarm_api mail to {0} ok'.format(json.dumps(CONFIG.get('target_email_adr'))))
        return True
    else:
        slog.warning('send alarm_api mail to {0} error'.format(json.dumps(CONFIG.get('target_email_adr'))))
        return False


def th_page(topargus, mbot):
    while True:
        #time.sleep(60 * 60)  # 60 min
        time.sleep(30)  # 60 min
        run_page(topargus, mbot)
    return


def run_topargus_spider(topargus_info, driver, mbot):
    status   = topargus_info.get('status')
    name     = topargus_info.get('name')
    host     = topargus_info.get('host')
    net_info = topargus_info.get('net_info')
    if status != 'true':
        slog.warn("topargus host:{0} name:{1} status false".format(host, name))
        return

    slog.info("spider run for topargus host:{0} name:{1}".format(host, name))
    username = topargus_info.get('username')
    password = topargus_info.get('password')

    topargus = TOPARGUS(username = username, password = password, host = host, name = name, net_info  = net_info, mydriver = driver)

    api_th = threading.Thread(target = th_api, args = (topargus, mbot, ))
    api_th.start()
    slog.info('api thread start')

    page_th = threading.Thread(target = th_page, args = (topargus, mbot, ))
    page_th.start()
    slog.info('page thread start')

    return True

def init_driver():
    #_____________________启动参数___________________________
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    options.add_argument('disable-gpu')
    #options.add_argument("window-size=1220,1080")
    options.add_argument("window-size=1440,1280")
    options.add_argument("start-maximized")
    options.add_argument("no-sandbox")

    #_____________________代理参数___________________________
    desired_capabilities = options.to_capabilities()
    desired_capabilities['acceptSslCerts'] = True
    desired_capabilities['acceptInsecureCerts'] = True
    desired_capabilities['proxy'] = {
        "httpProxy": None,
        "ftpProxy": None,
        "sslProxy": None,
        "noProxy": None,
        "proxyType": "MANUAL",
        "class": "org.openqa.selenium.Proxy",
        "autodetect": False,
    }

    #_____________________启动浏览器___________________________
    mydriver = webdriver.Chrome(
        options=options,
        #executable_path=CHROME_DRIVER_PATH,
        desired_capabilities = desired_capabilities)
    mydriver.set_page_load_timeout(30)
    #driver.manage().window().maximize()
    return mydriver



def main():
    mbot = MailBot()
    if not mbot.login(recv = False, trytimes = 10):
        slog.error("mail login failed")
        return False

    slog.info('mail login ok')
    print('mail login ok')


    mydriver = init_driver()
    if not mydriver:
        slog.warn('chrome driver load error')
        return False

    topargus_host = CONFIG.get('topargus_host')
    for item in topargus_host:
        run_topargus_spider(item, mydriver, mbot)

    print("TOPARGUS 系统监控中...")
    slog.info("TOPARGUS 系统监控中...")
    while True:
        time.sleep(1)

    return True



if __name__ == '__main__':
    main()
