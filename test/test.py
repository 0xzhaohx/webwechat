#!/usr/bin/python
# -*-coding: UTF-8 -*-

import os
import time
import re

print time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print(os.environ['HOME'])

print os.path.expandvars('$HOME')

print(os.path.expanduser('~'))

os.system('/home/zhaohongxing/msg17ced3.mp3')
def cs_test():
    print("字")


def dict_test():
    contact_map = {}

    for i in range(4):
        contact_map[i]=i
        print(i)

    for key in contact_map.keys():
        print(key)

#dict_test()

pm = re.search(r'(\S+)(\s+?)([(])(\d+)([)])', 'abc44444444   (1)')
print(pm)
if pm:
    print(pm.group(1))
    print(pm.group(2))
    print(pm.group(3))
    print(pm.group(4))
    print(pm.group(5))