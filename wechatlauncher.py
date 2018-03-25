#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-


import os
import sys
import threading
from time import sleep

from PyQt4 import QtGui, uic

from com.ox11.wechat.api.requests.WeChatAPI import WeChatAPI
from com.ox11.wechat.wechat import WeChat
from PyQt4.Qt import QIcon

qtCreatorFile = "resource/ui/wechatlauncher.ui"

LauncherWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChatLauncher(QtGui.QDialog, LauncherWindow,threading.Thread):

    time_out = False

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        LauncherWindow.__init__(self)
        threading.Thread.__init__(self,name='wechat login')
        self.setDaemon(True)
        self.user_home = os.environ['HOME']
        self.app_home = self.user_home + '/.wechat/'
        self.api = WeChatAPI()
        self.logint = WeChatLogint(self,self.api)
        self.setupUi(self)
        self.setWindowIcon(QIcon("icons/hicolor/32x32/apps/electronic-wechat.png"))
        self.setWindowIconText("Wechat 0.3-8")
        self.loginButton.clicked.connect(self.login)
        self.generate_qrcode()
        self.set_qr_code_image()

    def qr_time_out(self):
        WeChatLauncher.time_out = True

    def set_qr_code_image(self):
        qrcode_path = self.app_home+"/qrcode.jpg"
        qr_image = QtGui.QImage()
        if qr_image.load(qrcode_path):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(qr_image))
            timer = threading.Timer(5, self.qr_time_out)
            timer.start()

            #auto_login_timer = threading.Timer(0, self.login())
            #auto_login_timer.start()
            self.logint.start()
        else:
            pass

    def login(self):
        login_state = self.api.wait4login()
        if self.api.redirect_uri:
            login_state = True
        else:
            login_state = self.api.wait4login(0)
            if self.api.redirect_uri:
                login_state = True
            else:
                login_state = False

        if login_state:
            self.accept()

    def generate_qrcode(self):
        uuid = self.api.get_uuid()
        self.api.generate_qrcode()


class WeChatLogint(threading.Thread):

    def __init__(self,logind,api):
        threading.Thread.__init__(self,name='wechat login')
        self.setDaemon(True)
        self.logind = logind
        self.api = api

    def run(self):

        while(not (True == WeChatLauncher.time_out)):
            #print(WeChatLauncher.time_out)
            #self.logind.login()
            sleep(1)

if __name__ =="__main__":

    #QtGui.QTextCodec.setCodecForTr(QtGui.QTextCodec.codecForName("utf8"))
    #QtGui.QTextCodec.setCodecForCStrings(QtGui.QTextCodec.codecForLocale())
    app = QtGui.QApplication(sys.argv)
    launcher = WeChatLauncher()
    launcher.show()
    if QtGui.QDialog.Accepted == launcher.exec_():
        window = WeChat(launcher.api)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
