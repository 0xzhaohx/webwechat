'''
Created on 2018年3月25日

@author: zhaohongxing
'''
#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
import os

class WechatConfig(object):

    def __init__(self):
        self.user_home = os.environ['HOME']
        self.app_home = self.user_home + '/.wechat/'
        