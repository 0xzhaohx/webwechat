#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

import sys
import threading
from time import sleep
import time

from PyQt4 import QtCore, QtGui, uic

from api.msg import Msg

reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.1.2.ui"

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
        #self.synct = WeChatSync(self.api)
        #self.synct.start()
        timer = threading.Timer(5, self.sync)
        timer.setDaemon(True)
        timer.start()

    def print_child(self):
        self.children()

    def init_contact(self):
        self.api.webwx_init()
        self.userNameLabel.setText((self.api.user['NickName']))
        for contact in self.api.contact_list:
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            self.contactListWidget.addItem(QtCore.QString.fromUtf8(dn))
        self.contactListWidget.clicked.connect(self.contact_cell_clicked)
        self.contactListWidget.itemSelectionChanged.connect(self.contact_itemSelectionChanged)

    def init_member(self):
        self.api.webwx_get_contact()
        for member in self.api.member_list:
            dn = member['RemarkName']
            if not dn:
                dn = member['NickName']
            self.memberListWidget.addItem(QtCore.QString.fromUtf8(dn))

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
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(dn))
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)
        counter = self.messages.count()
        for index in range(counter):
            item = self.messages.takeItem(0)
            #delete item

    def member_cell_clicked(self):
        current_row =self.memberListWidget.currentRow()
        contact = self.api.member_list[current_row]
        self.current_select_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(dn))
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)

    def send_button_click(self):
        contact = self.current_select_contact
        msg = str(self.draft.toPlainText())
        gsm = Msg(1, msg, self.current_select_contact['UserName'])
        self.api.webwx_send_msg(gsm)
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        formated_msg = ('%s (%s) %s') % (msg, st, self.api.user['NickName'])
        item = QtGui.QListWidgetItem()
        item.setText(QtCore.QString.fromUtf8(formated_msg))
        item.setTextAlignment(3)
        self.messages.addItem(item)

        self.draft.setText("")

    def webwx_sync_process(self, data):
        if not data:
            return False
        #TODO FIX BUG data['BaseResponse']['Ret'] NOT WORK
        ret_code = data['BaseResponse']['Ret']
        add_msg_count = data['AddMsgCount']

        if ret_code == 0:
            pass
        else:
            return False

        if add_msg_count == 0:
            return True

        msg_list = data['AddMsgList']

        for msg in msg_list:
            from_user_name = msg['FromUserName']
            to_user_name = msg['ToUserName']
            print('from user %s,to user %s', (from_user_name, to_user_name))
            if not self.current_select_contact:
                continue
            if from_user_name == self.current_select_contact['UserName']:
                st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
                formated_msg = ('%s (%s) %s') % (st, self.api.user['NickName'], msg['Content'])
                item = QtGui.QListWidgetItem()
                item.setText(QtCore.QString.fromUtf8(formated_msg))
                item.setTextAlignment(1)
                self.messages.addItem(item)

    def sync(self):
        while (True):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            print('sync %s' %(st))
            (code, selector) = self.api.sync_check()
            if code == -1 and selector == -1:
                print("self.api.sync_check() error")
            else:
                if code != '0':
                    pass
                elif code == '0' and selector == '0':
                    print("nothing")
                else:
                    if selector != '0':
                        sync_response = self.api.webwx_sync()
                        #print("WeChatSync.run#webwx_sync:")
                        #print(sync_response)
                        self.webwx_sync_process(sync_response)
            sleep(8)

'''
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
            (code,selector) = self.api.sync_check()
            if code == -1 and selector == -1:
                print("self.api.sync_check() error")
            else:
                if code != '0':
                    pass
                elif code == '0' and selector == '0':
                    print("nothing")
                else:
                    if selector != '0':
                        sync_response = self.api.webwx_sync()
                        print("WeChatSync.run#webwx_sync:")
                        print(sync_response)
            sleep(10)
'''

'''
if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)

    if(True):
        wechat = WeChat()
        wechat.show()
        sys.exit(app.exec_())
'''