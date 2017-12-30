#!/usr/bin/python
# -*- coding:UTF-8 -*-

import sys
from PyQt4 import QtCore,QtGui,uic
from api.WeChatAPI import WeChatAPI
from api.msg import Msg
import threading
from time import ctime,sleep

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
            self.contactListWidget.addItem(contact['NickName'])

        self.contactListWidget.addItem("contact")
        self.contactListWidget.clicked.connect(self.contact_cell_clicked)
        self.contactListWidget.itemSelectionChanged.connect(self.contact_itemSelectionChanged)

    def init_member(self):
        self.memberListWidget.addItem("members")
        self.memberListWidget.clicked.connect(self.contact_cell_clicked)

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
        print("cell_click")
        current_row =self.contactListWidget.currentRow()
        print(current_row)
        contact = self.api.contact_list[current_row]
        print(contact)
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)

    def member_cell_clicked(self):
        print("cell_click")
        self.widget.setVisible(True)
        self.label_2.setVisible(False)

    def send_button_click(self):
        current_item = self.contactListWidget.currentItem()
        current_row =self.contactListWidget.currentRow()
        contact = self.api.contact_list[current_row]
        print(current_row)
        print(current_item)
        msg = str(self.draft.toPlainText())
        gsm = Msg(1,msg,contact['UserName'])
        self.api.webwx_send_msg(gsm)
        self.messages.append(msg)

        self.draft.setText("")


class WeChatSync(threading.Thread):

    def __init__(self,api):
        threading.Thread.__init__(self,name='wechat sync')
        self.api = api
        self.setDaemon(True)

    def run(self):
        while(True):
            self.api.sync_check()
            print(str(ctime())+" sync:"+self.api.appid)
            sleep(5)

''''''
if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)

    if(True):
        wechat = WeChat()
        wechat.show()
        sys.exit(app.exec_())

