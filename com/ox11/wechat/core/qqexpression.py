#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月1日

@author: zhaohongxing
'''

import os

class QQExpression(object):
    
    expressions = {
        ""
    }

    def __init__(self):
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.expression_home = "resource/expression"
        self.expressions = {}
        
    def expression_initinal(self):
        for e in os.listdir("/home/zhaohongxing/workspace/python/webwechat/"+self.expression_home):
            file_path = os.path.join("/home/zhaohongxing/workspace/python/webwechat/"+self.expression_home, e)  
            if os.path.isfile(file_path):
                self.expressions[e]=e
            
    def expression_2_image(self,emotion):
        if self.expressions.has_key(emotion):
            data = self.expressions.get(emotion)
            return data
        else:
            return None
        
if __name__ =="__main__":
    ex = QQExpression()
    ex.expression_initinal()
    print(ex.expression_2_image('21.gif'))
        