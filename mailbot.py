#!/usr/bin/env python
#-*- coding:utf8 -*-

'''
yagmail to send mail
imapclient to download mail
'''


import yagmail
import imaplib
import email
from email import generator
from io import StringIO
import mailparser
import json
import os

from slogging import slog
from config import CONFIG

class MailBot(object):
    def __init__(self):
        self.sender = None
        self.downloader = None
        self.username  =  CONFIG.get('mail_config').get('username')
        self.password  =  CONFIG.get('mail_config').get('password')
        self.smtp_host =  CONFIG.get('mail_config').get('smtp_host')
        self.smtp_port =  CONFIG.get('mail_config').get('smtp_port')
        self.imap_host =  CONFIG.get('mail_config').get('imap_host')
        self.imap_port =  CONFIG.get('mail_config').get('imap_port')

        return

    def login(self, send = True, recv = False,trytimes = 4):
        if recv == True:
            if not self.downloader_login(trytimes):
                slog.warning("mail downloader login fialed")
                return False

        if send == True:
            if not self.sender_login(trytimes):
                slog.warning("mail sender login failed")
                return False
    
        slog.info("mail send:{0}  recv:{1} login success".format(send, recv))
        return True

    # imap recv mail
    def downloader_login(self, trytimes = 3):
        for i in range(0, trytimes):
            try:
                downloader = imaplib.IMAP4_SSL(self.imap_host)
                downloader.login(self.username, self.password)
                slog.info('downloader login {0} success'.format(self.imap_host))
                self.downloader = downloader
                return True
            except Exception as e:
                slog.warning('downloader login {0} failed:{1}'.format(self.imap_host, e))

        return False
 
    # smtp send mail
    def sender_login(self, trytimes = 3):
        for i in range(0, trytimes):
            try:
                if self.smtp_port == 587:
                    yag = yagmail.SMTP(user = self.username, password = self.password, host = self.smtp_host, port = self.smtp_port, smtp_starttls=True, smtp_ssl=False)
                    self.sender = yag
                else:
                    yag = yagmail.SMTP(user = self.username, password = self.password, host = self.smtp_host, port = self.smtp_port)
                    self.sender = yag
                slog.info("sender login success to {0}".format(self.smtp_host))
                return True
            except Exception as e:
                slog.warning("sender login failed:{0}".format(e))

        return False
    
    def make_pic_inline(self, pic_path):
        return yagmail.inline(pic_path)
    
    def send_mail(self, email_adr, subject, contents):
        '''
        contents = [
                'This is the body, and here is just text http://somedomain/image.png',
                'You can find an audio file attached.',
                './chuxianyoulikai_yuxi.mp3',
                yagmail.inline('./cat1.jpg')]
        '''
        if not self.sender:
            slog.warning("mail_sender not logining")
            return False
        try:
            self.sender.send(email_adr, subject, contents)
            slog.info("send email to {0} success".format(email_adr))
            return True
        except Exception as e:
            slog.warning("send email to {0} failed:{1}".format(email_adr, e))
            return False

    def send_mail_without_trycatch(self, email_adr, subject, contents):
        '''
        contents = [
                'This is the body, and here is just text http://somedomain/image.png',
                'You can find an audio file attached.',
                './chuxianyoulikai_yuxi.mp3',
                yagmail.inline('./cat1.jpg')]
        '''
        if not self.sender:
            slog.warning("mail_sender not logining")
            return False
        self.sender.send(email_adr, subject, contents)
        slog.info("send email to {0} finished".format(email_adr))
        return True
 
    
    def recv_mail(self):
        if not self.downloader:
            slog.warning("downloader not login")
            return False
    
        self.downloader.select() # Select inbox or default namespace
        (retcode, messages) = self.downloader.search(None, '(UNSEEN)')
        if retcode != 'OK':
            slog.warning("read mail from server failed")
            return False
    
        if not os.path.exists("./downmail"):
            os.mkdir("./downmail")
    
        for num in messages[0].split():
            slog.info('Processing: {0}'.format(num))
            typ, data = self.downloader.fetch(num.decode('utf-8'),'(RFC822)')
            # 标记已读
            sr = self.downloader.store(num, '+FLAGS', '\Seen')
            # 标记删除
            #sr = downloader.store(num, '+FLAGS', '\\Deleted')
            email_message = email.message_from_string(data[0][1].decode('utf-8'))
    
            # mail to string
            fp = StringIO()
            g = generator.Generator(fp, mangle_from_=True, maxheaderlen=60)
            g.flatten(email_message)
            email_text = fp.getvalue()
    
            # mail_string to json_string
            pmail = mailparser.parse_from_string(email_text)
            email_json = pmail.mail_json
            # mail to json obj
            email_data = json.loads(email_json)
    
            # 处理邮件
            self.handle_mail(email_data)
    
            subject = email_data.get('subject')
            body = email_data.get('body')
            slog.info("get mail: subject[{0}] body.size[{1}]".format(subject, len(body)))
    
            filename = './downmail/{0}.eml'.format(subject)
            with open(filename, 'w') as fout:
                gr = generator.Generator(fout)
                gr.flatten(email_message)
                #fout.write(email_text)
                fout.close()
    
            filename_j = './downmail/{0}.json'.format(subject)
            with open(filename_j, 'w') as fjout:
                fjout.write(json.dumps(email_data, indent=4, ensure_ascii=False))
                fjout.close()
    
            slog.info("save {0} ok,\n".format(filename))
    
        return True

    def recv_mail_weibo(self, subject_pattern, from_email_pattern):
        if not self.downloader:
            slog.warning("downloader not login")
            if not self.login():
                return
    
        self.downloader.select() # Select inbox or default namespace
        (retcode, messages) = self.downloader.search(None, '(UNSEEN)')
        if retcode != 'OK':
            slog.warning("read mail from server failed")
            return False
    
        for num in messages[0].split():
            slog.info('Processing: {0}'.format(num))
            typ, data = self.downloader.fetch(num.decode('utf-8'),'(RFC822)')
            email_message = email.message_from_string(data[0][1].decode('utf-8'))
    
            # mail to string
            fp = StringIO()
            g = generator.Generator(fp, mangle_from_=True, maxheaderlen=60)
            g.flatten(email_message)
            email_text = fp.getvalue()
    
            # mail_string to json_string
            pmail = mailparser.parse_from_string(email_text)
            email_json = pmail.mail_json
            # mail to json obj
            email_data = json.loads(email_json)
            subject = email_data.get('subject')
            if subject.find(subject_pattern) == -1:
                continue
            from_email = email_data.get('from')[0] # list
            if from_email_pattern not in from_email:
                continue

            # 标记已读
            sr = self.downloader.store(num, '+FLAGS', '\Seen')
            # 标记删除
            #sr = downloader.store(num, '+FLAGS', '\\Deleted')
            
            # find target email
            body = email_data.get('body')
            slog.info("read email: subject:{0} body size:{1}".format(subject, len(body)))
            vcode = body.split('\n')[0]
            return vcode
    
        return ''

    
    def handle_mail(self, email_data):
        subject = email_data.get('subject')
        body = email_data.get('body')
        from_email = email_data.get('from')[0]
        slog.info("recv email from {0} subject is :{1}".format(from_email[1], subject))
        # do something handle email
        return
    
    def get_weibo_vcode(self, subject_pattern, from_email_pattern):
        return self.recv_mail_weibo(subject_pattern, from_email_pattern)

def main():
    mbot = MailBot()
    if not mbot.login(recv = False, trytimes = 10):
        slog.warning("login mail failed")
        return

    #vcode = mbot.get_weibo_vcode("weibo_vcode", "nikinumber4@163.com")
    #slog.info("get weibo vcode:{0}".format(vcode))

    # test send
    email_adr = 'smaug.jiao@topnetwork.org'
    subject = 'test from python'
    contents = [
            'This is the body, and here is just text http://somedomain/image.png',
            'You can find an audio file attached.',
            mbot.make_pic_inline('./sample.png'),
            '\n\n\n',
            'mail end']
    ret = mbot.send_mail(email_adr, subject, contents)
    #ret = mbot.send_mail_without_trycatch(email_adr, subject, contents)
    if ret:
        slog.info("send mail ok")
    else:
        slog.warning("send mail fail")
 

if __name__ == "__main__":
    main()

