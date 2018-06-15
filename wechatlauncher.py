#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''

import os
import sys
import threading
#from time import sleep
import time
import logging

from com.ox11.wechat.wechatte import WeChat
from wechatweb import WeChatWeb
import platform

from PyQt4.Qt import QIcon
from PyQt4 import QtGui, uic
from config import WechatConfig

qtCreatorFile = "resource/ui/wechatlauncher-1.0.ui"

LauncherWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

def getOSName():
    return platform.system()

def machine():
    if os.name == 'nt' and sys.version_info[:2] < (2,7):
        return os.environ.get("PROCESSOR_ARCHITEW6432",
               os.environ.get('PROCESSOR_ARCHITECTURE', ''))
    else:
        return platform.machine()

def osbits(machine=None):
    if not machine:
        machine =machine()
    machine2bits = {'AMD64': 64, 'x86_64': 64, 'i386': 32, 'x86': 32}
    return machine2bits.get(machine, None)

class WeChatLauncher(QtGui.QDialog, LauncherWindow):

    timeout = login_state = exitt = False
    LOG_FILE = './wechat.log'
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        LauncherWindow.__init__(self)
        #threading.Thread.__init__(self,name='wechat launcher')
        #self.setDaemon(True)
        self.loggingclear()
        
        logging.basicConfig(filename=WeChatLauncher.LOG_FILE,filemode='w',level=logging.DEBUG,format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')
        self.weChatWeb = WeChatWeb()
        self.config = WechatConfig()
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.setWindowIconText("WeChat 0.5")
        self.launcher_thread = WeChatLauncherThread(self,self.weChatWeb)
        self.generate_qrcode()
        self.launcher_thread.start()
        self.load_qr_code_image()

    def set_qr_timeout(self):
        WeChatLauncher.timeout = True

    def load_qr_code_image(self):
        qrcode_path = self.config.getAppHome()+"/qrcode.jpg"
        qr_image = QtGui.QImage()
        if qr_image.load(qrcode_path):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(qr_image))
            timer = threading.Timer(25, self.set_qr_timeout)
            timer.start()
        else:
            pass

    def login(self):
        code = self.weChatWeb.wait4login()
        print("code is %s"%code)
        if "200" == code:
            WeChatLauncher.login_state = True
        else:
            code = self.weChatWeb.wait4login(0)
            print("code is %s"%code)
            WeChatLauncher.login_state = (True if "200" == code else False)

        if WeChatLauncher.login_state:
            self.accept()

    def generate_qrcode(self):
        self.weChatWeb.generate_qrcode()

    def loggingclear(self):
        if os.path.exists(WeChatLauncher.LOG_FILE):
            with open(WeChatLauncher.LOG_FILE,'w') as lf:
                lf.seek(0)
                lf.truncate()
                logging.debug(time.time())

class WeChatLauncherThread(threading.Thread):

    def __init__(self,launcher,weChatWeb):
        threading.Thread.__init__(self,name='wechat launcher thread')
        self.setDaemon(True)
        self.launcher = launcher
        self.weChatWeb = weChatWeb

    def run(self):
        while(False == WeChatLauncher.timeout == WeChatLauncher.login_state):
            if(WeChatLauncher.exitt):
                break
            self.launcher.login()
            
            time.sleep(2)

if __name__ =="__main__":
    
    #QtGui.QTextCodec.setCodecForTr(QtGui.QTextCodec.codecForName("utf8"))
    #QtGui.QTextCodec.setCodecForCStrings(QtGui.QTextCodec.codecForLocale())
    app = QtGui.QApplication(sys.argv)
    if getOSName() == "Windows":
        logging.error("The OS name is Windows,will be exit!")
    launcher = WeChatLauncher()
    launcher.show()
    if QtGui.QDialog.Accepted == launcher.exec_():
        window = WeChat(launcher.weChatWeb)
        window.show()
        sys.exit(app.exec_())
    else:
        WeChatLauncher.exitt=True
        sys.exit(0)
