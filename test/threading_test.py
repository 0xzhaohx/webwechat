#!/usr/bin/python
# -*- coding:UTF-8 -*-

import threading
from time import ctime,sleep

def sync():
    print('sync')

timer = threading.Timer(5, sync)
timer.start()