#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

import sys
import os
import re
import threading
from time import sleep
import time

from PyQt4 import QtCore, QtGui, uic
import xml.dom.minidom

from api.msg import Msg
from PyQt4.Qt import QIcon, QModelIndex
from PyQt4.QtGui import QStandardItemModel
from PyQt4.QtCore import QVariant

reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.5.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    def __init__(self,wxapi):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.config = {
           
        }
        self.user_home = os.path.expanduser('~')
        self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.default_head_icon = 'default.png'
        self.current_select_contact = None
        self.messages_cache = {}
        self.contact_map = {'-1':-1}
        self.member_map = {'-1':-1}
        self.wxapi = wxapi
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/electronic-wechat.png"))
        self.wxapi.login()
        self.wxapi.webwx_init()
        self.setup_user()
        self.wxapi.webwx_get_contact()
        self.sessionTableModel = QStandardItemModel(1,4)
        self.memberTableModel = QStandardItemModel(1,4)
        self.readerTableModel = QStandardItemModel()
        self.memberWidget.setVisible(False)
        self.readerWidget.setVisible(False)
        self.init_session()
        self.init_member()
        self.init_reader()
        
        self.chatWidget.setVisible(False)
        
        self.sessionWidget.setModel(self.sessionTableModel)
        self.sessionWidget.setColumnHidden(0,True)
        self.memberWidget.setModel(self.memberTableModel)
        self.memberWidget.setColumnHidden(0,True)
        self.readerWidget.setModel(self.readerTableModel)

        self.sessionButton.clicked.connect(self.session_button_clicked)
        self.memberButton.clicked.connect(self.member_button_clicked)

        self.sendButton.clicked.connect(self.send_msg)
        #self.synct = WeChatSync(self.wxapi)
        #self.synct.start()
        timer = threading.Timer(5, self.sync)
        timer.setDaemon(True)
        timer.start()
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        print("dragEnterEvent")

    def dragMoveEvent(self, event):
        #print("dragMoveEvent")
        pass
    
    def isImage(self,path):
        if path:
            reg="(?i).+?\\.(jpg|jpeg\png\gif|bmp)"
            return path.match(reg)
    
    def dropEvent(self, event):
        #print("dropEvent")
        if event.mimeData().hasUrls():
            #遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():                
                print QtCore.QString.fromUtf8(str(url.toLocalFile()))
            event.acceptProposedAction()
        else:
            #super(Button,self).dropEvent(event)
            pass
    
    def load_image(self, img_path,use_default=True):
        image = QtGui.QImage()
        if image.load(img_path):
            return image
        else:
            if use_default:
                image.load(self.app_home)

    def setup_user(self):
        self.userNameLabel.setText((self.wxapi.user['NickName']))
        user_icon_file = self.app_home + "/heads/contact/" + self.wxapi.user['UserName'] + ".jpg"
        user_head_image = QtGui.QImage()
        if user_head_image.load(user_icon_file):
            self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))
        else:
            if user_head_image.load(self.app_home + "/heads/default/" +self.default_head_icon):
                self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))

    def init_session(self):
        '''
        contact table (5 columns)
        column 1:user name(will be hidden)
        column 2:head icon
        column 3:remark or nick name
        column 4:message count tips
        :return:
        '''
        #self.sessionWidget.setColumnCount(4)
        ''''''
        group_contact_list = []
        for contact in self.wxapi.member_list:
            if contact['AttrStatus'] and contact['AttrStatus'] > 0:
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                group_contact_list.append(group)

        params = {
            'BaseRequest': self.wxapi.base_request,
            'Count': len(group_contact_list),
            'List': group_contact_list
        }
        session_response = self.wxapi.webwx_batch_get_contact(params)
        
        session_list = session_response['ContactList']
        session_list.sort(key=lambda mm: mm['AttrStatus'],reverse=True)
        if session_response['Count'] and session_response['Count'] > 0:
            self.wxapi.session_list.extend(session_list)
       
        ''''''
        for contact in self.wxapi.session_list:
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            user_name = contact['UserName']
            currentRow = self.sessionTableModel.rowCount()
            self.sessionTableModel.insertRow(currentRow)
            #user name item
            user_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
            #user_name_item.setText(QtCore.QString.fromUtf8(user_name))
            self.sessionTableModel.setItem(currentRow,0,user_name_item)
            #head icon
            icon_label = QtGui.QLabel("");
            icon_path = self.app_home +"/heads/contact/"+contact['UserName']+".jpg"
            icon = QtGui.QImage()
            if icon.load(icon_path):
                icon_label.setPixmap(QtGui.QPixmap.fromImage(icon).scaled(40, 40));
            else:
                icon_path = self.app_home +"/heads/default/default.png"
                if icon.load(icon_path):
                    icon_label.setPixmap(QtGui.QPixmap.fromImage(icon).scaled(40, 40));
                    
            self.sessionTableModel.setItem(currentRow,1,QtGui.QStandardItem(QIcon(icon_path),""))
            #user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
            #remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.sessionTableModel.setItem(currentRow,2,remark_nick_name_item)

        self.sessionWidget.clicked.connect(self.session_item_clicked)

    def init_member(self):
        ''''''
        #self.memberTableModel.setColumnHidden(0,True)
        '''
        /*去掉每行的行号*/ 
        QHeaderView *headerView = table->verticalHeader();  
        headerView->setHidden(true);  
        '''
        
        self.memberWidget.setColumnHidden(1,True)
        group_contact_list = []
        for member in self.wxapi.member_list:
            group_contact_list.append(member)
        group_contact_list.sort(key=lambda mm: mm['PYInitial'])

        for member in group_contact_list:#.sort(key=lambda m: m['PYInitial'])
            dn = member['RemarkName']
            if not dn:
                dn = member['NickName']

            user_name = member['UserName']
            user_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
            #user_name_item.setText(QtCore.QString.fromUtf8(user_name))
            currentRow = self.memberTableModel.rowCount()
            self.memberTableModel.insertRow(currentRow)
            self.memberTableModel.setItem(currentRow, 0, user_name_item)
            # head icon
            icon_label = QtGui.QLabel("");
            icon_path = self.app_home + "/heads/contact/" + member['UserName'] + ".jpg"
            icon = QtGui.QImage()
            if icon.load(icon_path):
                icon_label.setPixmap(QtGui.QPixmap.fromImage(icon).scaled(40, 40));
            else:
                print('warning:icon load failed %s,use defalt' %(icon_path))
                icon_path = self.app_home +"/heads/default/default.png"
                
            self.memberTableModel.setItem(currentRow,1,QtGui.QStandardItem(QIcon(icon_path),""))

            # user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
            #remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.memberTableModel.setItem(currentRow,2,remark_nick_name_item)

        self.memberWidget.clicked.connect(self.member_item_clicked)

    def init_reader(self):
        pass
        #self.readerListWidget.addItem("readers")
        #self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def session_button_clicked(self):
        self.memberWidget.setVisible(False)
        self.sessionWidget.setVisible(True)

    def session_itemSelectionChanged(self):
        print("changed")

    def read_button_clicked(self):
        self.memberWidget.setVisible(False)
        self.sessionWidget.setVisible(False)
        self.readerWidget.setVisible(True)

    def member_button_clicked(self):
        self.memberWidget.setVisible(True)
        self.sessionWidget.setVisible(False)

    def get_contact(self,user_name):
        for contact in self.wxapi.session_list:
            if user_name == contact['UserName']:
                return contact

    def get_member(self,user_name):
        for member in self.wxapi.member_list:
            if user_name == member['UserName']:
                return member

    def session_item_clicked(self):
        self.chatWidget.setVisible(True)
        self.label.setVisible(False)
        current_row = self.sessionWidget.currentIndex().row()
        user_name_index = self.sessionTableModel.index(current_row,0)
        user_name = self.sessionTableModel.data(user_name_index)
        #user_name = str(self.sessionWidget.item(current_row, 0).text())

        tip_index = self.sessionTableModel.index(current_row,3)
        tips_item = self.sessionTableModel.data(tip_index)
        if tips_item:
            self.sessionTableModel.setData(tip_index, "")
        #message_count = self.sessionWidget.item(current_row, 3).text();
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
        #self.label_2.setVisible(False)
        if self.messages_cache.has_key(user_name):
            messages_list = self.messages_cache[user_name]
            for message in messages_list:
                msg_type = message['MsgType']
                if msg_type:
                    if msg_type == 1:
                        self.text_msg_handler(message)
                    elif msg_type == 52:
                        pass
                    elif msg_type == 2:
                        pass
                    elif msg_type == 3:
                        self.image_msg_handler(message)
                    elif msg_type == 34:
                        self.voice_msg_handler(message)
                    elif msg_type == 49:
                        self.app_msg_handler(message)
                    else:
                        self.default_msg_handler(message)
        else:
            self.messages.setText('')

    def member_item_clicked(self):
        self.chatWidget.setVisible(True)
        self.label.setVisible(False)
        current_row =self.sessionWidget.currentIndex().row()
        user_name_index = self.memberTableModel.index(current_row,0)
        user_name = self.memberTableModel.data(user_name_index,0)
        contact = self.get_member(user_name)
        self.current_select_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUserLabel.setText(QtCore.QString.fromUtf8(dn))
        if self.messages_cache.has_key(user_name):
            messages_list = self.messages_cache[user_name]
            for message in messages_list:
                self.messages.append(QtCore.QString.fromUtf8(message))
        else:
            self.messages.setText('')
    '''
        把消息發送出去
    '''
    def send_msg(self):
        msg = str(self.draft.toPlainText())
        gsm = Msg(1, msg, self.current_select_contact['UserName'])
        self.wxapi.webwx_send_msg(gsm)
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s: %s') % (st, self.wxapi.user['NickName'],msg)
        self.messages.append(QtCore.QString.fromUtf8(format_msg))
        self.draft.setText('')
        '''
        '''
        contact = self.current_select_contact
        row_count = self.sessionWidget.rowCount()
        find = False
        for i in range(row_count):
            user_name = self.sessionWidget.item(i, 0).text()
            if user_name and user_name == contact['UserName']:
                find = True
                '''
                tips_item = self.sessionWidget.item(i, 3)
                if tips_item:
                    tips = tips_item.text()
                    tips_item.setText(str(int(tips) + 1))
                else:
                    tips_item = QtGui.QTableWidgetItem()
                    tips_item.setText('1')
                    self.sessionWidget.setItem(i, 3, tips_item)
                '''
                break;
        if find == False:
            self.sessionWidget.insertRow(row_count+1)
            user_name_item = QtGui.QTableWidgetItem()
            user_name_item.setText(contact['UserName'])
            self.sessionWidget.setItem(i, 0, user_name_item)
            #
            remark_nick_name_item = QtGui.QTableWidgetItem()
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            remark_nick_name_item.setText(QtCore.QString.fromUtf8(dn))
            self.sessionWidget.setItem(row_count+1, 1, remark_nick_name_item)
            #tips
            tips_item = QtGui.QTableWidgetItem()
            tips_item.setText('1')
            self.sessionWidget.setItem(row_count+1, 2, tips_item)
        else:
            pass
    '''
        默認的消息處理handler
    '''
    def default_msg_handler(self,msg):
        self.text_msg_handler(msg)
    
    '''
        把語音消息加入到聊天記錄裏
    '''
    def voice_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_select_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s: %s') % (st, self.wxapi.user['NickName'], "請在手機端收聽語音")
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_select_contact and from_user_name == self.current_select_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
        else:
            pass
    '''
        把語音消息加入到聊天記錄裏
    '''
    def video_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_select_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s: %s') % (st, self.wxapi.user['NickName'], "請在手機端觀看視頻")
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_select_contact and from_user_name == self.current_select_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
        else:
            pass
    '''
        把文本消息加入到聊天記錄裏
    '''
    def text_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_select_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s: %s') % (st, self.wxapi.user['NickName'], msg['Content'])
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_select_contact and from_user_name == self.current_select_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
        else:
            pass
    '''
        把文本消息加入到聊天記錄裏
    '''
    def image_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_select_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        msg_id = msg['MsgId']
        self.wxapi.webwx_get_msg_img(msg_id)
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_select_contact and from_user_name == self.current_select_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
            
            msg_img = ('<img src=%s/cache/img/%s.jpg>'%(self.app_home,msg_id))
            self.messages.append(msg_img)
        else:
            pass
        
    '''
        把應用消息加入到聊天記錄裏，應該指的是由其他應用分享的消息
    '''
    def app_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_select_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        xml_content = msg['Content']
        if xml_content:
            xml_content = xml_content.replace("&gt;",">")
            xml_content = xml_content.replace("&lt;","<")
            xml_content = xml_content.replace("<br/>","")
        
        doc = xml.dom.minidom.parseString(xml_content)
        title_nodes = doc.getElementsByTagName("title")
        desc_nodes = doc.getElementsByTagName("des")
        app_url_nodes = doc.getElementsByTagName("url")
        if title_nodes:
            title = title_nodes[0].firstChild.data
        if desc_nodes:
            desc = desc_nodes[0].firstChild.data
        if app_url_nodes:
            app_url = app_url_nodes[0].firstChild.data
        format_msg = ('(%s) %s: %s %s %s') % (st, self.wxapi.user['NickName'], title,desc,app_url)
        
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_select_contact and from_user_name == self.current_select_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
        else:
            pass
        
    '''
    提昇from_user_name在會話列表中的位置
    '''
    def up_session_position(self,from_user_name):
        row_count = self.sessionWidget.rowCount()
        for i in range(row_count):
            user_name = self.sessionWidget.item(i,0).text()
            #在會話列表中找到此人
            if user_name and user_name == from_user_name:
                
                #刪除此行
                #self.sessionWidget.removeRow(i)
                break;
        return True
    '''
    '''       
    def put_msgcache(self,msg):
        from_user_name = msg['FromUserName']
        if self.messages_cache.has_key(from_user_name):
            messages_list = self.messages_cache[from_user_name]
        else:
            messages_list = []
        messages_list.append(msg)
        self.messages_cache[from_user_name] = messages_list
        
        #TODO ADD TIPS
        '''
            增加消息數量提示（提昇此人在會話列表中的位置）
        '''
        exist = False#此人是否在會話列表中
        row_count = self.sessionTableModel.rowCount()
        for cells in range(row_count):
            index = self.sessionTableModel.index(cells,0)
            user_name = self.sessionTableModel.data(index)
            #user_name = self.sessionTableModel.item(i,0).text()
            if user_name and user_name == from_user_name:
                exist = True
                tip_index = self.sessionTableModel.index(cells,3)
                count_tips_obj = self.sessionTableModel.data(tip_index)
                if count_tips_obj:
                    count_tips = count_tips_obj.toInt()
                    if count_tips:
                        count = count_tips[0]
                        self.sessionTableModel.setData(tip_index, str(count+1))
                        #count_tips_obj.setText(str(int(count_tips)+1))
                    else:
                        self.sessionTableModel.setData(tip_index, "1")
                        #count_tips_obj.setText('1')
                else:
                    count_tips_item = QtGui.QStandardItem("1")
                    self.sessionTableModel.setItem(cells, 3, count_tips_item)
                break;
        #have not received a message before（如果此人没有在會話列表中，則加入之）
        if not exist:
            contact = {}
            for member in self.wxapi.member_list:
                if member['UserName'] == from_user_name:
                    contact = member
                    break
            dn = contact['RemarkName']
            if not dn:
                dn = contact['NickName']
            user_name = contact['UserName']
            cells = []
            # user name item
            user_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
            cells.append(user_name_item)
            
            item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/electronic-wechat.png"),"")
            cells.append(item)
            
            # user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
            cells.append(remark_nick_name_item)
            
            count_tips_item = QtGui.QStandardItem("1")
            cells.append(count_tips_item)
            
            self.sessionTableModel.insertRow(0,cells)
    '''
        MSGTYPE_TEXT: 1,
        MSGTYPE_IMAGE: 3,
        MSGTYPE_VOICE: 34,
        MSGTYPE_VIDEO: 43,
        MSGTYPE_MICROVIDEO: 62,
        MSGTYPE_EMOTICON: 47,
        MSGTYPE_APP: 49,
        MSGTYPE_VOIPMSG: 50,
        MSGTYPE_VOIPNOTIFY: 52,
        MSGTYPE_VOIPINVITE: 53,
        MSGTYPE_LOCATION: 48,
        MSGTYPE_STATUSNOTIFY: 51,
        MSGTYPE_SYSNOTICE: 9999,
        MSGTYPE_POSSIBLEFRIEND_MSG: 40,
        MSGTYPE_VERIFYMSG: 37,
        MSGTYPE_SHARECARD: 42,
        MSGTYPE_SYS: 10000,
        MSGTYPE_RECALLED: 10002,  // 撤销消息
    '''
    def webwx_sync_process(self, data):
        if not data:
            return False
        ret_code = data['BaseResponse']['Ret']

        if ret_code == 0:
            pass
        else:
            return False

        add_msg_count = data['AddMsgCount']
        if add_msg_count == 0:
            return True

        msg_list = data['AddMsgList']

        for msg in msg_list:
            msg_type = msg['MsgType']
            from_user_name = msg['FromUserName']
            '''
            没有選擇和誰對話或者此消息的發送人和當前的對話人不一致，則把消息存放在message_cache中
            '''
            if (not self.current_select_contact) or from_user_name != self.current_select_contact['UserName']:
                self.put_msgcache(msg)
            else:
                '''
                    如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
                '''
                if msg_type:
                    if msg_type == 1:
                        self.text_msg_handler(msg)
                    elif msg_type == 2:
                        pass
                    elif msg_type == 3:
                        self.image_msg_handler(msg) 
                    elif msg_type == 34:
                        self.voice_msg_handler(msg)
                    elif msg_type == 49:
                        self.app_msg_handler(msg)
                    else:
                        self.default_msg_handler(msg)

    def sync(self):
        while (True):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            print('sync %s' %(st))
            (code, selector) = self.wxapi.sync_check()
            if code == -1 and selector == -1:
                print("self.wxapi.sync_check() error")
            else:
                if code != '0':
                    pass
                elif code == '0' and selector == '0':
                    print("nothing need to process")
                else:
                    if selector != '0':
                        sync_response = self.wxapi.webwx_sync()
                        #print("WeChatSync.run#webwx_sync:")
                        #print(sync_response)
                        self.webwx_sync_process(sync_response)
            sleep(11)

'''
class WeChatSync(threading.Thread):

    def __init__(self,wxapi):
        threading.Thread.__init__(self,name='wechat sync')
        self.wxapi = wxapi
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
            (code,selector) = self.wxapi.sync_check()
            if code == -1 and selector == -1:
                print("self.wxapi.sync_check() error")
            else:
                if code != '0':
                    pass
                elif code == '0' and selector == '0':
                    print("nothing")
                else:
                    if selector != '0':
                        sync_response = self.wxapi.webwx_sync()
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