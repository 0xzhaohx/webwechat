#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''


class Msg(object):
    msg_type = {
        '1':'文本消息',
        '3':'图片消息',
        '34':'语音消息',
        '37':'好友确认消息',
        '40':'POSSIBLEFRIEND_MSG',
        '42':'共享名片',
        '43':'视频消息',
        '47':'动画表情',
        '48':'位置消息',
        '49':'分享链接',
        '50':'VOIPMSG',
        '51':'微信初始化消息',
        '52':'VOIPNOTIFY',
        '53':'VOIPINVITE',
        '62':'小视频',
        '9999':'SYSNOTICE',
        '10000':'系统消息',
        '10002':'撤回消息',
    }
    def __init__(self,type,content,to_user_name):
        '''
        :param type:
            1:txt msg
            3:image msg
        :param content:
        :param to_user_name:
        '''
        self.type = type
        if type == 1:
            self.content = content
        elif type == 3:
            self.media_id = content
        else:
            pass
            
        #self.from_user_name = from_user_name
        self.to_user_name = to_user_name

        self.local_id = ''
        self.client_msg_id = ''