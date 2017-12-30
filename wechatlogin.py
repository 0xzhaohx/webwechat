#!/usr/bin/python
# -*- coding:UTF-8 -*-


import sys
import os

from PyQt4 import QtGui, uic,QtCore

from wechat import WeChat
from api.WeChatAPI import WeChatAPI

qtCreatorFile = "resource/ui/wechatlogindialog.ui"

LoginWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChatLoginDialog(QtGui.QDialog, LoginWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        LoginWindow.__init__(self)
        self.api = WeChatAPI()
        self.setupUi(self)
        self.loginButton.clicked.connect(self.login)
        self.generate_qrcode()
        self.set_qr_code_image()

    def set_qr_code_image(self):
        file = os.environ['HOME']+"/.wechat/qrcode.jpg"
        image = QtGui.QImage()
        if image.load(file):
            self.qrLabel.setPixmap(QtGui.QPixmap.fromImage(image))
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
