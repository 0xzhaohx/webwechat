#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月1日

@author: zhaohongxing
'''

import os

class QQExpression(object):
    
    def __init__(self):
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.expression_home = "resource/expression"
        self.expressions = {}
        self.emotions = {}
        self.expression_initinal()
        self.emotion_initinal()
        
    def expression_initinal(self):
        pp = "/home/zhaohongxing/workspace/python/webwechat/resource/i18n/expression.properties";
        if not os.path.exists(pp):
            return
        
        p = open(pp,"r")
        for line in p.readline():
            line = line
            print(line)
            if line.find('=') > 0 and not line.startswith('#'):
                kv = line.split('=')
                self.expressions[kv[0]]=kv[1]
    
    def emotion_initinal(self):
        for e in os.listdir("/home/zhaohongxing/workspace/python/webwechat/"+self.expression_home):
            file_path = os.path.join("/home/zhaohongxing/workspace/python/webwechat/"+self.expression_home, e)  
            if os.path.isfile(file_path):
                self.emotions[e]=e
            
    def expression_2_emotion(self,emotion):
        if self.expressions.has_key(emotion):
            data = self.expressions.get(emotion)
            return data
        else:
            return None
        
if __name__ =="__main__":
    ex = QQExpression()
    print(ex.expressions)
    print(ex.expression_2_emotion('21.gif'))
        