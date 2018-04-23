#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''
import os

class WechatConfig(object):

    def __init__(self):
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        