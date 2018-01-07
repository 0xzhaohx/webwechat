#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

import sys
import re
import threading
from time import sleep
import time

from PyQt4 import QtCore, QtGui, uic

from api.msg import Msg

reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.1.3.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    def __init__(self,api):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.api = api
        self.setupUi(self)
        self.contact_map = {'-1':-1}
        self.member_map = {'-1':-1}
        self.api.login()
        self.init_contact()
        self.init_member()
        self.init_reader()
        self.memberWidget.setVisible(False)
        self.readerWidget.setVisible(False)
        self.current_select_contact = None
        '''
        first invoke
        '''
        group_contact_list = []
        for contact in self.api.contact_list:
            if contact['UserName'].find('@@') >= 0:
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                group_contact_list.append(group)

        params = {
            'BaseRequest': self.api.base_request,
            'Count': len(group_contact_list),
            'List': group_contact_list
        }
        self.api.webwx_batch_get_contact(params)
        '''
        second invoke
        '''
        group_contact_list = []
        for member in self.api.member_list:
            snsf = member['SnsFlag']
            if snsf and snsf > 0:
                group_contact_list.append(member)
        group_contact_list.sort(key=lambda member: member['SnsFlag'])
        params = {
            'BaseRequest': self.api.base_request,
            'Count': len(group_contact_list),
            'List': group_contact_list
        }
        dictt = self.api.webwx_batch_get_contact(params)
        '''        '''
        for contact in dictt['ContactList']:
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            user_name = contact['UserName']
            user_name_item = QtGui.QTableWidgetItem()
            user_name_item.setText(QtCore.QString.fromUtf8(user_name))
            currentRow = self.contactWidget.rowCount()
            self.contactWidget.insertRow(currentRow)
            self.contactWidget.setItem(currentRow,0,user_name_item)
            remark_nick_name_item = QtGui.QTableWidgetItem()
            remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.contactWidget.setItem(currentRow,1,remark_nick_name_item)

        #self.chatWidget.setVisible(False)

        self.contactButton.clicked.connect(self.contact_button_clicked)
        self.memberButton.clicked.connect(self.member_button_clicked)

        self.sendButton.clicked.connect(self.send_button_click)
        #self.synct = WeChatSync(self.api)
        #self.synct.start()
        timer = threading.Timer(5, self.sync)
        timer.setDaemon(True)
        timer.start()

    def init_contact(self):
        self.api.webwx_init()
        self.userNameLabel.setText((self.api.user['NickName']))
        self.contactWidget.setColumnCount(4)
        llist = self.api.chat_set
        for contact in self.api.contact_list:
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            user_name = contact['UserName']
            user_name_item = QtGui.QTableWidgetItem()
            user_name_item.setText(QtCore.QString.fromUtf8(user_name))
            currentRow = self.contactWidget.rowCount()
            self.contactWidget.insertRow(currentRow)
            self.contactWidget.setItem(currentRow,0,user_name_item)
            remark_nick_name_item = QtGui.QTableWidgetItem()
            remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.contactWidget.setItem(currentRow,1,remark_nick_name_item)
        self.contactWidget.itemClicked.connect(self.contact_item_clicked)

    def init_member(self):
        self.api.webwx_get_contact()
        self.memberWidget.setColumnCount(4)
        for member in self.api.member_list:
            dn = member['RemarkName']
            if not dn:
                dn = member['NickName']

            user_name = member['UserName']
            user_name_item = QtGui.QTableWidgetItem()
            user_name_item.setText(QtCore.QString.fromUtf8(user_name))
            currentRow = self.memberWidget.rowCount()
            self.memberWidget.insertRow(currentRow)
            self.memberWidget.setItem(currentRow, 0, user_name_item)
            remark_nick_name_item = QtGui.QTableWidgetItem()
            remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.memberWidget.setItem(currentRow,1,remark_nick_name_item)

        self.memberWidget.itemClicked.connect(self.member_item_clicked)

    def init_reader(self):
        pass
        #self.readerListWidget.addItem("readers")
        #self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def contact_button_clicked(self):
        self.memberWidget.setVisible(False)
        self.contactWidget.setVisible(True)

    def contact_itemSelectionChanged(self):
        print("changed")

    def read_button_clicked(self):
        self.memberWidget.setVisible(False)
        self.contactWidget.setVisible(False)
        self.readerWidget.setVisible(True)

    def member_button_clicked(self):
        self.memberWidget.setVisible(True)
        self.contactWidget.setVisible(False)

    def read_button_clicked(self):
        pass

    def get_contact(self,user_name):
        for contact in self.api.contact_list:
            if user_name == contact['UserName']:
                return contact

    def get_member(self,user_name):
        for member in self.api.member_list:
            if user_name == member['UserName']:
                return member

    def contact_item_clicked(self):
        current_row = self.contactWidget.currentRow()
        curuent_item = self.contactWidget.currentItem()
        user_name = self.contactWidget.item(current_row, 0).text();

        tips_item = self.contactWidget.item(current_row, 2);
        if tips_item:
            tips_item.setText('')
        #message_count = self.contactWidget.item(current_row, 3).text();
        #if message_count:
        #    count = int(message_count)

        contact = self.get_contact(user_name)
        if not contact:
            contact = self.get_member(user_name)
        self.current_select_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']

        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(dn))
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)
        self.messages.setText('')

    def member_item_clicked(self):
        current_row =self.memberWidget.currentRow()
        user_name = self.memberWidget.item(current_row,0).text();
        contact = self.get_member(user_name)
        self.current_select_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(dn))
        self.messages.setText("")
        #self.widget.setVisible(True)
        #self.label_2.setVisible(False)

    def send_button_click(self):
        contact = self.current_select_contact
        msg = str(self.draft.toPlainText())
        gsm = Msg(1, msg, self.current_select_contact['UserName'])
        self.api.webwx_send_msg(gsm)
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s: %s') % (st, self.api.user['NickName'],msg)
        self.messages.append(QtCore.QString.fromUtf8(format_msg))
        self.draft.setText('')
        '''
        
        row_count = self.contactWidget.rowCount()
        find = False
        for i in range(row_count):
            user_name = self.contactWidget.item(i, 0).text()
            if user_name and user_name == contact['UserName']:
                find = True
                tips_item = self.contactWidget.item(i, 2)
                if tips_item:
                    tips = tips_item.text()
                    tips_item.setText(str(int(tips) + 1))
                else:
                    tips_item = QtGui.QTableWidgetItem()
                    tips_item.setText('1')
                    self.contactWidget.setItem(i, 2, tips_item)
                break;
        if find == False:
            self.contactWidget.insertRow(row_count+1)
            user_name_item = QtGui.QTableWidgetItem()
            user_name_item.setText(contact['UserName'])
            self.contactWidget.setItem(i, 0, user_name_item)
            #
            remark_nick_name_item = QtGui.QTableWidgetItem()
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.contactWidget.setItem(row_count+1, 1, remark_nick_name_item)
            #tips
            tips_item = QtGui.QTableWidgetItem()
            tips_item.setText('1')
            self.contactWidget.setItem(row_count+1, 2, tips_item)

        '''

    def webwx_sync_process(self, data):
        if not data:
            return False
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
                format_msg = ('(%s) %s: %s') % (st, self.api.user['NickName'], msg['Content'])
                self.messages.append(QtCore.QString.fromUtf8(format_msg))
            else:
                #TODO ADD TIPS
                row_count = self.contactWidget.rowCount()
                for i in range(row_count):
                    user_name = self.contactWidget.item(i,0).text()
                    if user_name and user_name == from_user_name:
                        tips_item = self.contactWidget.item(i, 2)
                        if tips_item:
                            tips = tips_item.text()
                            tips_item.setText(str(int(tips)+1))
                        else:
                            tips_item = QtGui.QTableWidgetItem()
                            tips_item.setText('1')
                            self.contactWidget.setItem(i, 2, tips_item)
                        break;

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
            sleep(11)

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