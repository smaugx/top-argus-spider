#!/usr/bin/env python
#-*- coding:utf8 -*-

import os

def check_alive():
    cmd = 'ps -ef |grep -a topargus_spider.py |grep -av grep'
    ret = os.popen(cmd).readlines()
    if not ret:
        print("topargus_spider.py not alive, will restart")
        start_cmd = 'cd /root/smaug/top-argus-spider && source vv/bin/activate && nohup python topargus_spider.py > /dev/null & 2>&1'
        os.popen(start_cmd)
        print('restart topargus_spider.py ok')
    return

if __name__ == '__main__':
    check_alive()


