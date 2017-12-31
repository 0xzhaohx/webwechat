#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
import threading
from time import sleep

from PyQt4 import QtCore, QtGui, uic

from api.msg import Msg

qtCreatorFile = "resource/ui/wechat-0.1.1.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    def __init__(self,api):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.api = api
        self.setupUi(self)
        self.api.login()
        self.init_contact()
        self.init_member()
        self.init_reader()
        self.memberListWidget.setVisible(False)
        self.readerListWidget.setVisible(False)
        self.current_select_contact = None

        #self.chatWidget.setVisible(False)

        self.contactButton.clicked.connect(self.contact_button_clicked)
        self.memberButton.clicked.connect(self.member_button_clicked)

        self.sendButton.clicked.connect(self.send_button_click)
        self.synct = WeChatSync(self.api)
        self.synct.start()

    def print_child(self):
        self.children()

    def init_contact(self):
        self.api.webwx_init()
        for contact in self.api.contact_list:
            self.contactListWidget.addItem(QtCore.QString.fromUtf8(contact['NickName']))
        self.contactListWidget.clicked.connect(self.contact_cell_clicked)
        self.contactListWidget.itemSelectionChanged.connect(self.contact_itemSelectionChanged)

    def init_member(self):
        self.api.webwx_get_contact()
        for member in self.api.member_list:
            self.memberListWidget.addItem(QtCore.QString.fromUtf8(member['NickName']))

        self.memberListWidget.clicked.connect(self.member_cell_clicked)

    def init_reader(self):
        self.readerListWidget.addItem("readers")
        self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def contact_button_clicked(self):
        self.memberListWidget.setVisible(False)
        self.contactListWidget.setVisible(True)

    def contact_itemSelectionChanged(self):
        print("changed")

    def read_button_clicked(self):
        self.memberListWidget.setVisible(False)
        self.contactListWidget.setVisible(False)
        self.readListWidget.setVisible(True)

    def member_button_clicked(self):
        self.memberListWidget.setVisible(True)
        self.contactListWidget.setVisible(False)

    def read_button_clicked(self):
        pass

    def contact_cell_clicked(self):
        current_row =self.contactListWidget.currentRow()
        contact = self.api.contact_list[current_row]
        self.current_select_contact = contact
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(contact['NickName']))
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)

    def member_cell_clicked(self):
        current_row =self.memberListWidget.currentRow()
        contact = self.api.member_list[current_row]
        self.current_select_contact = contact
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(contact['NickName']))
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)

    def send_button_click(self):
        contact = self.current_select_contact
        msg = str(self.draft.toPlainText())
        gsm = Msg(1,msg,contact['UserName'])
        print(contact)
        self.api.webwx_send_msg(gsm)
        self.messages.append(msg)

        self.draft.setText("")


class WeChatSync(threading.Thread):

    def __init__(self,api):
        threading.Thread.__init__(self,name='wechat sync')
        self.api = api
        self.setDaemon(True)

    def run(self):
        hosts = ['https://webpush.wx.qq.com/cgi-bin/mmwebwx-bin/synccheck',
                 'https://webpush.weixin.qq.com/cgi-bin/mmwebwx-bin/synccheck',
                 'https://webpush.wx2.qq.com/cgi-bin/mmwebwx-bin/synccheck',
                 'https://webpush.wx8.qq.com/cgi-bin/mmwebwx-bin/synccheck',
                 'https://webpush.web.wechat.com/cgi-bin/mmwebwx-bin/synccheck',
                 'https://webpush.web2.wechat.com/cgi-bin/mmwebwx-bin/synccheck'
                 ]
        while(True):
            '''
            for host in hosts:
                (code, selector) = self.api.sync_check(host)
                print("code=%s,selector=%s"%(code,selector))
            '''
            (code,selector) = self.api.sync_check()
            if code == -1 and selector == -1:
                print("self.api.sync_check() error")
            else:
                if code != 0 and selector != 0:
                    sync_response = self.api.webwx_sync()
                    print("webwx_sync:")
                    print(sync_response)
            sleep(5)

''''''
if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)

    if(True):
        wechat = WeChat()
        wechat.show()
        sys.exit(app.exec_())

