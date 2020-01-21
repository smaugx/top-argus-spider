#!/usr/bin/env python
#-*- coding:utf8 -*-


MAIL_CONFIG_qq = {
        "username"  : "123@qq.com",
        "password"  : "xxx",
        "smtp_host" : "smtp.qq.com",
        "imap_host" : "imap.qq.com",
        "imap_port" :  993,
        "smtp_port" : 465
        }

MAIL_CONFIG_163 = {
        "username"  : "123@163.com",
        "password"  : "xxx",
        "smtp_host" : "smtp.163.com",
        "imap_host" : "imap.163.com",
        "imap_port" : 993,
        "smtp_port" : 465
        }


MAIL_CONFIG_outlook = {
        "username"  : "123@xx",
        "password"  : "xxxx,",
        "smtp_host" : "smtp.office365.com",
        "imap_host" : "outlook.office365.com",
        "imap_port" : 993,
        "smtp_port" : 587
        }


topargus_host = [
        {
            'name': 'netv4'
            'status': 'false',
            'net_info': '主网',
            'username': 'test',
            'password': 'test',
            'host': '192.168.50.242',
        },
        {
            'name': 'betatest_rober2',
            'status': 'true',
            'net_info': '春节外网环境',
            'username': 'test',
            'password': 'test',
            'host': '64.225.3.94',
        },
        {
            'name': 'holidays_hosts',
            'status': 'true',
            'net_info': '春节公司内网环境',
            'username': 'test',
            'password': 'test',
            'host': '192.168.50.202',
        },
        ]

CONFIG = {
        'mail_config': MAIL_CONFIG_outlook,
        'target_email_adr': 'smaug.jiao@topnetwork.org',
        'topargus_host': topargus_host
        }
