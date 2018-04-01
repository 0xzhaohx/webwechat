'''
Created on 2018年3月25日

@author: zhaohongxing
'''
#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-


class User(object):

    def __init__(self,uid,userName,nickName):
        self.uid = uid
        '''
            user_name start with @,is a contact
            user_name start with @@,is a group
        '''
        self.user_name = userName
        self.nick_ame = nickName
        self.head_image_url = ''
        self.remark_name = ''
        self.contact_list = []
        self.member_count = 0
        self.member_list = []
        self.pyInitial = ''
        self.pyQuanPin = ''
        self.remarkPYInitial=''
        self.remarkPYQuanPin=''
        self.hideInputBarFlag=0
        self.starFriend=0
        self.sex=1
        self.signature=''
        self.appAccountFlag=0
        self.verifyFlag=0
        '''
        contact_flag=1,is a private contact
        contact_flag=0,is a public contact
        
        '''
        self.contact_flag=0
        self.webWxPluginSwitch=0
        self.headImgFlag=0
        self.snsFlag=17
