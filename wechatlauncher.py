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


class WeChatLauncher(QtGui.QDialog, LauncherWindow):

    timeout = False

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        LauncherWindow.__init__(self)
        #threading.Thread.__init__(self,name='wechat launcher')
        #self.setDaemon(True)
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.wxapi = WeChatAPI()
        self.launcher_thread = WeChatLauncherThread(self,self.wxapi)
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/electronic-wechat.png"))
        self.setWindowIconText("Wechat 0.3-8")
        self.loginButton.clicked.connect(self.do_login)
        self.generate_qrcode()
        self.load_qr_code_image()

    def set_qr_timeout(self):
        WeChatLauncher.timeout = True

    def load_qr_code_image(self):
        qrcode_path = self.app_home+"/qrcode.jpg"
        qr_image = QtGui.QImage()
        if qr_image.load(qrcode_path):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(qr_image))
            timer = threading.Timer(25, self.set_qr_timeout)
            timer.start()

            #auto_login_timer = threading.Timer(0, self.login())
            #auto_login_timer.start()
            self.launcher_thread.start()
        else:
            pass

    def do_login(self):
        login_state = self.wxapi.wait4login()
        if self.wxapi.redirect_uri:
            login_state = True
        else:
            login_state = self.wxapi.wait4login(0)
            if self.wxapi.redirect_uri:
                login_state = True
            else:
                login_state = False

        if login_state:
            self.accept()

    def generate_qrcode(self):
        uuid = self.wxapi.get_uuid()
        self.wxapi.generate_qrcode()


class WeChatLauncherThread(threading.Thread):

    def __init__(self,launcher,wxapi):
        threading.Thread.__init__(self,name='wechat launcher thread')
        self.setDaemon(True)
        self.launcher = launcher
        self.wxapi = wxapi

    def run(self):

        while(False == WeChatLauncher.timeout):
            #print(WeChatLauncher.timeout)
            self.launcher.do_login()
            
            sleep(1)

if __name__ =="__main__":

    #QtGui.QTextCodec.setCodecForTr(QtGui.QTextCodec.codecForName("utf8"))
    #QtGui.QTextCodec.setCodecForCStrings(QtGui.QTextCodec.codecForLocale())
    app = QtGui.QApplication(sys.argv)
    launcher = WeChatLauncher()
    launcher.show()
    if QtGui.QDialog.Accepted == launcher.exec_():
        window = WeChat(launcher.wxapi)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
