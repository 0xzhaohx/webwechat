#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

import random
import time
import urllib
import requests
import re
import xml.dom.minidom
import json
import os
import sys
from _socket import timeout

'''
1.ContactFlag:
    1是好友，值为3是公众号
2."UserName" 用户名称:
    一个"@"为好友，两个"@"为群组
3."Sex": 
    性别，0-未设置（公众号、保密），1-男，2-女
4."StarFriend": 是否为星标朋友  0-否  1-是
'''

def _decode_data(data):
    """
    @brief      decode array or dict to utf-8
    @param      data   array or dict
    @return     utf-8
    """
    if isinstance(data, dict):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            rv[key] = _decode_data(value)
        return rv
    elif isinstance(data, list):
        rv = []
        for item in data:
            item = _decode_data(item)
            rv.append(item)
        return rv
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data


class WeChatAPI(object):

    def __init__(self):
        self.hosts = {
            "weixin.qq.com":['login.weixin.qq.com','file.wx.qq.com','webpush.weixin.qq.com'],
            "wx2.qq.com":['login.wx2.qq.com','file.wx2.qq.com','webpush.wx2.qq.com'],
            "wx8.qq.com":['login.wx8.qq.com','file.wx8.qq.com','webpush.wx8.qq.com'],
            "qq.com":['login.wx.qq.com','file.wx.qq.com','webpush.wx.qq.com'],
            "wechat.com":['login.web.wechat.com','file.web.wechat.com','webpush.web.wechat.com'],
            "web2.wechat.com":['login.web2.wechat.com','file.web2.wechat.com','webpush.web2.wechat.com']
        }
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.status = -1#登陸與否
        self.file_host = None
        self.appid = 'wx782c26e4c19acffb'
        self.uuid = ''
        self.redirect_uri = None
        self.login_icon = True
        self.skey = ''
        #wxsid:weixin session id
        self.sid = ''
        #wxuin: weixin user identity number
        self.uin = ''
        self.webwx_data_ticket=''
        #pass_ticket: 通关文牒
        self.pass_ticket = ''
        self.is_grayscale = 0
        self.base_request = {}
        self.sync_key_dic = []
        self.sync_key = ''
        # device_id: 登录手机设备
        # web wechat 的格式为: e123456789012345 (e+15位随机数)
        # mobile wechat 的格式为: A1234567890abcde (A+15位随机数字或字母)
        self.device_id = 'e' + repr(random.random())[2:17]
        #the user had login
        self.user = []
        #會話列表
        self.session_list = []
        self.member_count = 0
        self.member_list = []
        #群組列表
        self.group_list = []
        self.fun = 'new'
        self.lang = 'zh_TW'
        self.timeout = 30
        self.session = requests.session()
        self.user_agent = (
            'Mozilla/5.0 (X11; Linux x86_64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/63.0.3239.108 Safari/537.36'
        )
        self.version='0.1'
        self.wxversion = 'v2'

    def get_uuid(self):
        url = "https://login.wx.qq.com/jslogin";
        params = {
            'appid': self.appid,
            'redirect_uri': 'https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxnewloginpage',
            'fun': self.fun,
            'lang': self.lang,
            '_': int(time.time())
        }
        url = url + "?" + urllib.urlencode(params)
        data = self.get(url)
        regx = r'wechat.QRLogin.code = (\d+); wechat.QRLogin.uuid = "(\S+?)"'
        if self.set_uuid(regx,data):
            pass
        else:
            regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
            if self.set_uuid(regx, data):
                pass
        '''
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            print("code:" + code + ",uuid:" + self.uuid)
        else:
        '''
        return data

    def set_uuid(self,regx,data):
        pm = re.search(regx, data)
        if pm:
            code = pm.group(1)
            self.uuid = pm.group(2)
            return True
        else:
            return False

    def generate_qrcode(self):
        url = "https://login.weixin.qq.com/qrcode/" + self.uuid;
        params = {
            't': 'webwx',
            '_': int(time.time())
        }
        data = self.post(url, params, stream=True)

        image = self.app_home+"/qrcode.jpg"
        with open(image, 'wb') as image:
            image.write(data)
            return image

    def webwx_stat_report(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatreport?fun=new&lang="+self.lang;
        params = {
            'BaseRequest': self.base_request,
            'Count': 0,
            'List': []
        }
        data = self.post(url, params)

        #print(data)
    '''
        tip = 0 已扫描
        tip = 1 未扫描
        turn
        408 timeout
        200
        201
    '''
    def wait4login(self,tip=1):
        url = "https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login" + "?loginicon="+str(self.login_icon)+"&tip=" + str(tip) + "&uuid=" + self.uuid + "&_" + str(int(time.time()))
        data = self.get(url)
        data = data.replace("\n","")
        data = data.replace("\r","")
        pm = re.search(r'wechat.code=(\d+);', data)
        if not pm:
            pm = re.search(r'window.code=(\d+);', data)
        code = pm.group(1)
        if code == '201':
            return True
        elif code == '200':
            pm = re.search(r'wechat.redirect_uri="(\S+?)";', data)
            if not pm:
                pm = re.search(r'window.redirect_uri="(\S+?)";', data)
            if not pm:
                return False
            rd_uri = pm.group(1) + '&fun='+self.fun + '&version=v2'
            self.redirect_uri = str(rd_uri)
            return True
        elif code == '408':
            print("error 408")
        else:
            print("unknow error")
        print("over------------------")
        return False

    '''
    return:
        <error>
            <ret>0</ret>
            <message>OK</message>
            <skey>xxx</skey>
            <wxsid>xxx</wxsid>
            <wxuin>xxx</wxuin>
            <pass_ticket>xxx</pass_ticket>
            <isgrayscale>1</isgrayscale>
        </error>
    '''
    def login(self):
        url = self.redirect_uri;
        data = self.get(url)
        doc = xml.dom.minidom.parseString(data)
        root = doc.documentElement
        for node in root.childNodes:
            for cn in node.childNodes:
                if node.nodeName == 'ret':
                    if cn.data != "0":
                        return False
                elif node.nodeName == 'skey':
                    self.skey = cn.data
                elif node.nodeName == 'wxsid':
                    self.sid = cn.data
                elif node.nodeName == 'wxuin':
                    self.uin = cn.data
                elif node.nodeName == 'pass_ticket':
                    self.pass_ticket = cn.data
                elif node.nodeName == 'isgrayscale':
                    self.is_grayscale = cn.data

        self.base_request = {
            'Uin': int(self.uin),
            'Sid': str(self.sid),
            'Skey': str(self.skey),
            'DeviceID': self.device_id,
        }
        return True

    def webwx_init(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxinit" + \
              '?pass_ticket=%s&r=%s&lang=%s' % (
                  self.pass_ticket, int(time.time()), self.lang
              )
        params = {
            'BaseRequest': self.base_request
        }
        headers = {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json; charset=UTF-8',
            'Connection': 'keep-alive',
            'Referer': 'https://wx.qq.com'
        }

        data = self.post(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        sessions_dict = json.loads(data, object_hook=_decode_data)
        self.user = sessions_dict['User']
        self.session_list = sessions_dict['ContactList']
        #download and setup logined user head img
        self.webwx_get_icon(self.user['UserName'], self.user['HeadImgUrl'])
        #TODO download the user head icon
        for contact in self.session_list:
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            if user_name.startswith('@'):
                self.webwx_get_icon(user_name,head_img_url)
            elif user_name.startswith('@@'):
                self.webwx_get_head_img(user_name,head_img_url)
            else:
                pass
        self.update_sync_key(sessions_dict)

        return sessions_dict

    def update_sync_key(self,dict):
        self.sync_key_dic = dict['SyncKey']

        def foo(x):
            return str(x['Key']) + '_' + str(x['Val'])

        self.sync_key = '|'.join(
            [foo(keyVal) for keyVal in self.sync_key_dic['List']])

    def webwx_status_notify(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxstatusnotify" + \
              '?pass_ticket=%s&lang=%s' % (
                  self.pass_ticket, self.lang
              )
        params = {
            'BaseRequest': self.base_request,
            'Code' : 3,
            'FromUserName': self.user['UserName'],
            'ToUserName': self.user['UserName'],
            'ClientMsgId': int(time.time())
        }
        headers = {
            'user-agent': self.user_agent,
            "content-type": "application/json; charset=UTF-8",
            'connection': 'keep-alive',
            "referer": "https://wx.qq.com"
        }
        data = self.post_json(url, params)
        return data

    def webwx_get_icon(self, user_name, head_img_url):
        url = 'https://wx.qq.com' + head_img_url
        data = self.get(url,stream=True)
        if not data:
            pass
        img_folder = ('%s/heads/'%(self.app_home))
        if not os.path.exists(img_folder):
            os.mkdir(img_folder)
        image = self.app_home + '/heads/contact/'+user_name+'.jpg'
        with open(image, 'wb') as image:
            image.write(data)
    '''
    用於取群
    '''
    def webwx_get_head_img(self,user_name,head_img_url):
        url = 'https://wx.qq.com/'+((head_img_url))
        data = self.get(url,stream=True)
        if not data:
            pass
        img_folder = ('%s/heads/contact/'%(self.app_home))
        if not os.path.exists(img_folder):
            os.mkdir(img_folder)
        image = img_folder+user_name+'.jpg'
        with open(image, 'wb') as image:
            image.write(data)

    def webwx_get_contact(self):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetcontact" + \
              '?pass_ticket=%s&lang=%s' % (
                  self.pass_ticket, self.lang
              )
        params = {
            'BaseRequest': self.base_request
        }
        headers = {
            'user-agent': self.user_agent,
            "content-type": "application/json; charset=UTF-8",
            'connection': 'keep-alive',
            "referer": "https://wx.qq.com"
        }

        data = self.post(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        contacts_dict = json.loads(data, object_hook=_decode_data)
        self.member_list = contacts_dict['MemberList']
        self.member_count = contacts_dict['MemberCount']
        # TODO download the user head icon
        for member in self.member_list:
            user_name = member['UserName']
            head_img_url = member['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            if user_name.startswith('@'):
                self.webwx_get_icon(user_name, head_img_url)
            elif user_name.startswith('@@'):
                self.webwx_get_head_img(user_name, head_img_url)
            else:
                pass
        return contacts_dict
    '''
    調用完webwx_init得到部分的有過聯天記錄的用户，再調用webwx_batch_get_contact可以護得完整的有過聯天記錄的用户列表
    params:
    1.
        params = {
            'BaseRequest': self.base_request,
            'Count': 1,
            'List': [
                {

                    'UserName': '',
                    'EncryChatRoomId': ''
                }

            ]
        }
    ###################################################
    2.
        params = {
            'BaseRequest': self.base_request,
            'Count': 1,
            'List': [
                {

                    'UserName': '',#群name.如：@@xxxxxx
                    'ChatRoomId': ''
                }

            ]
        }
    '''
    def webwx_batch_get_contact(self, params):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxbatchgetcontact" + \
              '?type=ex&r=%s&pass_ticket=%s' % (
                  int(time.time()),self.pass_ticket
              )

        data = self.post(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'))
        dictt = json.loads(data, object_hook=_decode_data)
        return dictt

    '''
        return wechat.synccheck={retcode:"xxx",selector:"xxx"}
        retcode:
            0:success
            1100:你在手机上登出了微信
            1101:你在其他地方登录了 WEB 版微信
            1102:你在手机上主动退出了
        selector:
            0:nothing
            2:new message?发送消息返回结果
            4:朋友圈有动态
            6:有消息返回结果
            7:webwxsync? or 进入/离开聊天界面?
            
    '''
    def sync_check(self,host=None):
        if not host:
            host = "https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck"
        params = {
            'r': int(time.time()),
            'skey': str(self.skey),
            'sid': str(self.sid),
            'uin': int(self.uin),
            'deviceid': str(self.device_id),
            'synckey': str(self.sync_key),
            '_': int(time.time())
        }

        headers = {
            'accept':'*/*',
            'accept-encoding':'gzip, deflate, br',
            'connection': 'keep-alive',
            "referer": "https://wx.qq.com/?&lang=zh_TW",
            'user-agent': self.user_agent
        }
        url = host + '?' + urllib.urlencode(params)
        data = self.get(url)
        #print("sync_check_response:")
        #print(data)
        pm = re.search(r'window.synccheck={retcode:"(\d+)",selector:"(\d+)"}', data)
        if pm:
            return (pm.group(1), pm.group(2))
        else:
            return (-1,-1)

    '''
    BaseResponse
    AddMsgCount:新增消息数
    AddMsgList：新增消息列表
    ModContactCount: 变更联系人数目
    ModContactList: 变更联系人列表
    SyncKey:新的synckey列表
    '''
    def webwx_sync(self):

        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsync" + \
            '?sid=%s&skey=%s&pass_ticket=%s' % (
                self.sid, self.skey, self.pass_ticket
            )
        params = {
            'BaseRequest': self.base_request,
            'SyncKey':self.sync_key_dic,
            'rr':~int(time.time())
        }
        headers = {
            'user-agent': self.user_agent,
            "content-type": "application/json; charset=UTF-8",
            "referer": "https://wx.qq.com"
        }

        data = self.post_json(url, params)
        dictt = json.loads(data, object_hook=_decode_data)
        if dictt['BaseResponse']['Ret'] == 0:
            self.update_sync_key(dictt)
        return dictt
    
    def webwx_send_emoticon(self,msg):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendemoticon" + \
              '?fun=sys&pass_ticket=%s' % (
                  self.pass_ticket
              )
        local_id = client_msg_id = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')

        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                "Type":msg.m_type,
                "Content":msg.content,
                "FromUserName":self.user['UserName'],
                "ToUserName":msg.to_user_name,
                "LocalID":local_id,
                "ClientMsgId":client_msg_id,
            }
        }
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://wx.qq.com"
        }

        data = self.post_json(url, params)
        return data
    
    def webwx_send_msg(self,msg):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg" + \
              '?pass_ticket=%s' % (
                  self.pass_ticket
              )
        local_id = client_msg_id = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')

        params = {
            'BaseRequest': self.base_request,
        }
        params_msg = {
            "Type":msg.m_type,
            "FromUserName":self.user['UserName'],
            "ToUserName":msg.to_user_name,
            "LocalID":local_id,
            "ClientMsgId":client_msg_id,
        }
        if msg.m_type == 1:
            params_msg["Content"]=msg.content,
        elif msg.m_type == 3:
            params_msg["MediaId"]=msg.media_id,
        else:
            pass
        params["Msg"]=params_msg
        headers = {
            'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)",
            "Content-Type": "application/json; charset=UTF-8",
            "Referer": "https://wx.qq.com"
        }

        data = self.post_json(url, params)
        return data

    def webwx_revoke_msg(self,msg):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxsendmsg" + \
              '?pass_ticket=%s' % (
                  self.pass_ticket
              )
        local_id = client_msg_id = str(int(time.time() * 1000)) + \
            str(random.random())[:5].replace('.', '')

        params = {
            'BaseRequest': self.base_request,
            'Msg': {
                "Type":msg.m_type,
                "Content":msg.content,
                "FromUserName":self.user['UserName'],
                "ToUserName":msg.to_user_name,
                "LocalID":local_id,
                "ClientMsgId":client_msg_id,
            }
        }
        headers = {
            'Connection':'keep-alive',
            'Content-Type': 'application/json; charset=UTF-8',
            'Referer': 'https://wx.qq.com',
            'User-Agent': self.user_agent
        }

        response = self.post_json(url=url, data=json.dumps(params, ensure_ascii=False).encode('utf8'), headers=headers)
        data = response.text
        response.close()
        return data
    
    def webwx_upload_media(self,to_contact,upload_file):
        url = "https://file.wx.qq.com/cgi-bin/mmwebwx-bin/webwxuploadmedia?f=json"
        self.options(url)
        fil = open(upload_file,'rb')
        f_name = os.path.basename(str(upload_file))
        files = {
            'filename':("%s"%(f_name),fil)
        }
        params = {
            'id':'WU_FILE_0',
            'name':'',
            'type':'image/jpeg',
            'lastModifiedDate':'',
            'size':'111',
            'mediatype':'pic',
            'UploadType':2,
            'pass_ticket':self.pass_ticket,
            'uploadmediarequest':{
                'BaseRequest': self.base_request,
                'ClientMediaId':1522484143966,
                'TotalLen':54992,
                'StartPos':0,
                'DataLen':54992,
                'MediaType':4,
                'FromUserName':self.user['UserName'],
                'ToUserName':to_contact['UserName']
            },
            'filename':f_name
        }
        response = self.post(url=url, data=params,files=files)
        return response
    
    '''
            根据MSG_ID下載圖片
    '''
    def webwx_get_msg_img(self,msg_id):
        url = "https://wx.qq.com/cgi-bin/mmwebwx-bin/webwxgetmsgimg" + \
              '?MsgID=%s&skey=%s&fun=download&type=slave' % (
                  msg_id,self.skey
              )
        data = self.get(url,stream=True)
        return data

    def get(self, url, data= {},stream=False):
        default_headers = {
            'Connection': 'keep-alive',
            'Referer': 'https://wx.qq.com/?&lang=zh_TW',
            'User-Agent': self.user_agent
        }

        while True:
            response = self.session.get(url=url, data=data, headers=default_headers)
            if stream:
                data = response.content
            else:
                response.encoding = 'utf-8'
                data = response.text
            response.close()
            return data
            '''
            try:
            except (KeyboardInterrupt, SystemExit):
                print("KeyboardInterrupt SystemExit")
            except:
                print("except")
            '''

    def post(self, url, data, headers={}, stream=False,files=None,timeout=10):
        default_headers = {
            'Connection': 'keep-alive',
            'Referer': 'https://wx.qq.com/?&lang=zh_TW',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': self.user_agent
        }

        for (key,value) in headers.items():
            default_headers[key]=value

        while True:
            try:
                if files:
                    response = self.session.post(url=url, data=data, headers=default_headers,files=files,timeout=timeout)
                else:
                    response = self.session.post(url=url, data=data, headers=default_headers)
                if stream:
                    data = response.content
                else:
                    response.encoding='utf-8'
                    data = response.text
                response.close()
                return data
            except (KeyboardInterrupt, SystemExit):
                raise
                return False
            except Exception,e:
                print(str(e))
                return False

    def post_json(self, url, data, headers={}):
        default_headers = {
            'Connection': 'keep-alive',
            'Referer': 'https://wx.qq.com/?&lang=zh_TW',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': self.user_agent
        }

        for (key,value) in headers.items():
            default_headers[key]=value

        while True:
            try:
                response = self.session.post(url=url, data=json.dumps(data, ensure_ascii=False).encode('utf8'), headers=default_headers)
                response.encoding='utf-8'
                data = response.text
                response.close()
                return data
            except (KeyboardInterrupt, SystemExit):
                raise
                return False
            except:
                return False
    
    def options(self, url, data=None, headers={}):
        default_headers = {
            'Connection': 'keep-alive',
            'Referer': 'https://wx.qq.com/?&lang=zh_TW',
            'Content-Type': 'application/json; charset=UTF-8',
            'User-Agent': self.user_agent
        }

        for (key,value) in headers.items():
            default_headers[key]=value

        try:
            response = self.session.options(url=url)
            response.encoding='utf-8'
            data = response.text
            response.close()
            return data
        except (KeyboardInterrupt, SystemExit):
            raise
            return False
        except:
            return False


if __name__ =="__main__":
    api = WeChatAPI()
    uuid = api.get_uuid()
    print("get uuid success")
    api.generate_qrcode()
    print("enerate_qrcode success")
    res = api.wait4login()
    if not api.redirect_uri:
        res = api.wait4login(0)
        print("wait4login:")
        print(res)
    res = api.login()
    init_response = api.webwx_init()
    #print(init_response)
    api.webwx_status_notify()
    api.webwx_get_contact()
    api.sync_check()
    #da = api.webwx_sync()





