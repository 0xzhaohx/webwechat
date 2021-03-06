#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
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

class AbstractWeChatAPI(object):

    headers = {
        'User-Agent':'',
        'Content-Type':'application/json; charset=UTF-8',
        'Referer':'https://wx.qq.com'
    }
    response_keys = {
        'SYNC_KEY':'SyncKey',
        'USER':'User',
        'USER_NAME':'UserName',
        'FROM_USER_NAME':'FromUserName',
        'HEAD_IMG_URL':'HeadImgUrl',
        'NICK_NAME':'NickName',
        'REMARK_NAME':'RemarkName',
        'CHAT_ROOM_ID':'ChatRoomId',
        'CONTACT_LIST':'ContactList',
        'COUNT':'Count',
        'MEMBER_LIST':'MemberList',
        'MEMBER_COUNT':'MemberCount',
        'ATTR_STATUS':'AttrStatus',
        'MSG_TYPE':'MsgType',
        'MSG_ID':'MsgId',
        'CONTENT':'Content',
        'BASE_RESPONSE':'BaseResponse',
        'RET':'Ret',
        'ADD_MSG_COUNT':'AddMsgCount',
        'ADD_MSG_LIST':'AddMsgList',
    }

    def get_icon(self):
        pass