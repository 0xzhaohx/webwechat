#!/usr/bin/python
# -*- coding:utf-8 -*-

import sys
from PyQt4 import QtCore,QtGui,uic

qtCreatorFile = "resource/ui/wechat-1.1.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.api = None
        self.setupUi(self)

'''
if __name__ =="__main__":
    app = QtGui.QApplication(sys.argv)

    if(True):
        login_window = WeChat()
        login_window.show()
        sys.exit(app.exec_())

'''