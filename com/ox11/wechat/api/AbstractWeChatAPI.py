'''
Created on 2018年3月25日

@author: zhaohongxing
'''
#!/usr/bin/python2.7
# -*- coding:UTF-8 -*-


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

    def get_icon(self):
        pass