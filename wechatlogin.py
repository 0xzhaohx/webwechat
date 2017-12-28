#!/usr/bin/python
# -*- conding:utf-8 -*-


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
        login = self.api.wait4login()
        if not self.api.redirect_uri:
            login = True
        else:
            login = self.api.wait4login(0)
            if not self.api.redirect_uri:
                login = True
            else:
                login = False

        if login:
            return self.accept()
        else:
            return self.reject()

    def generate_qrcode(self):
        uuid = self.api.get_uuid()
        self.api.generate_qrcode()


if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)
    loginDialog = WeChatLoginDialog()
    loginDialog.show()
    if QtGui.QDialog.Accepted == loginDialog.exec_():
        window = WeChat()
        window.show()
        window.api = loginDialog.api
        sys.exit(app.exec_())
    else:
        sys.exit(0)
