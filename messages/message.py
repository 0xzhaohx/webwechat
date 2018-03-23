#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

class Message(object):

    def __init__(self,from_user_name,msg_type,msg_body,msg_time):
        self.from_user_name= from_user_name
        self.msg_type= msg_type
        self.msg_body= msg_body
        self.msg_time= msg_time