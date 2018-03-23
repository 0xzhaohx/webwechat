#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-


import os
import sys
import threading
from time import sleep

from PyQt4 import QtGui, uic

from api.requests.WeChatAPI import WeChatAPI
from wechat import WeChat

qtCreatorFile = "resource/ui/wechatlogindialog.ui"

LoginWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChatLoginDialog(QtGui.QDialog, LoginWindow,threading.Thread):

    time_out = False

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        LoginWindow.__init__(self)
        threading.Thread.__init__(self,name='wechat login')
        self.setDaemon(True)
        self.api = WeChatAPI()
        self.logint = WeChatLogint(self,self.api)
        self.setupUi(self)
        self.loginButton.clicked.connect(self.login)
        self.generate_qrcode()
        self.set_qr_code_image()

    def qr_time_out(self):
        WeChatLoginDialog.time_out = True

    def set_qr_code_image(self):
        file = os.environ['HOME']+"/.wechat/qrcode.jpg"
        image = QtGui.QImage()
        if image.load(file):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(image))
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
        print(not WeChatLoginDialog.time_out)

        while(not (True == WeChatLoginDialog.time_out)):
            #print(WeChatLoginDialog.time_out)
            #self.logind.login()
            sleep(1)

if __name__ =="__main__":

    #QtGui.QTextCodec.setCodecForTr(QtGui.QTextCodec.codecForName("utf8"))
    #QtGui.QTextCodec.setCodecForCStrings(QtGui.QTextCodec.codecForLocale())
    app = QtGui.QApplication(sys.argv)
    loginDialog = WeChatLoginDialog()
    loginDialog.show()
    if QtGui.QDialog.Accepted == loginDialog.exec_():
        window = WeChat(loginDialog.api)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
