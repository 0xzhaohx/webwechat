#!/usr/bin/python
# -*- conding:UTF-8 -*-


class Msg(object):
    def __init__(self,type,content,to_user_name):
        '''
        :param type:
            1:txt msg
        :param content:
        :param from_user_name:
        :param to_user_name:
        '''
        self.type = type
        self.content = content
        #self.from_user_name = from_user_name
        self.to_user_name = to_user_name

        self.local_id = ''
        self.client_msg_id = ''