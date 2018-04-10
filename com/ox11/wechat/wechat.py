#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''

import sys
import os
import re
import threading
from time import sleep
import time

from PyQt4 import QtCore, QtGui, uic
import xml.dom.minidom

from api.msg import Msg
from PyQt4.Qt import QIcon, Qt
from PyQt4.QtGui import QStandardItemModel, QFileDialog, QMenu, QAction,\
    QTableView, QVBoxLayout, QStandardItem, QPushButton, QSpacerItem,\
    QRadioButton
from PyQt4.QtCore import QSize, pyqtSlot, pyqtSignal
import json

reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.5.ui"

WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    '''
        webwx_init
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->webwx_getcontact
        ->first call webwx_batch_getcontact
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->second call webwx_batch_getcontact
    '''
    def __init__(self,wxapi):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.config = {
           
        }
        self.user_home = os.path.expanduser('~')
        self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = '%s/default/default.png'%(self.head_home)
        self.current_chat_contact = None
        self.msg_cache = {}
        self.prepare4Environment()
        self.wxapi = wxapi
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.wxapi.login()
        self.wxapi.webwx_init()
        self.setup_user()
        self.batch_get_contact()
        self.wxapi.webwx_get_contact()
        self.sessionTableModel = QStandardItemModel(1,4)
        self.memberTableModel = QStandardItemModel(1,4)
        self.readerTableModel = QStandardItemModel()
        
        self.memberListWidget = None
        self.memberWidget.setVisible(False)
        self.readerWidget.setVisible(False)
        self.init_session()
        self.init_member()
        self.init_reader()
        
        self.chatWidget.setVisible(False)
        
        self.sessionWidget.setIconSize(QSize(40,40))
        self.sessionWidget.setModel(self.sessionTableModel)
        self.sessionWidget.setColumnHidden(0,True)
        self.sessionWidget.setColumnWidth(1, 40);
        self.sessionWidget.setColumnWidth(3, 40);
        self.memberWidget.setModel(self.memberTableModel)
        self.memberWidget.setIconSize(QSize(40,40))
        self.memberWidget.setColumnHidden(0,True)
        self.memberWidget.setColumnWidth(1, 40);
        self.memberWidget.setColumnWidth(3, 40);
        self.readerWidget.setModel(self.readerTableModel)

        self.sessionButton.clicked.connect(self.session_button_clicked)
        self.memberButton.clicked.connect(self.member_button_clicked)

        self.sendButton.clicked.connect(self.send_msg)
        self.selectImageFileButton.clicked.connect(self.select_document)
        self.currentChatUser.clicked.connect(self.current_chat_user_click)
        self.addMenu4SendButton()
        self.addMenu4SettingButton()
        #self.synct = WeChatSync(self.wxapi)
        #self.synct.start()
        timer = threading.Timer(5, self.sync)
        timer.setDaemon(True)
        timer.start()
        
    def addMenu4SendButton(self):
        menu = QMenu()
        enterAction = QAction(QtCore.QString.fromUtf8("按Enter發送消息"),self)
        menu.addAction(enterAction)
        self.sendSetButton.setMenu(menu)
        
    def addMenu4SettingButton(self):
        menu = QMenu()
        aboutAction = QAction(QtCore.QString.fromUtf8("關於"),self)
        menu.addAction(aboutAction)
        self.settingButton.setMenu(menu)
        
    def do_logout(self):
        print("logout..............")
    
    def batch_get_contact(self):
        groups = []
        for contact in self.wxapi.session_list:
            if contact['UserName'].find('@@') >= 0:
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                groups.append(group)

        params = {
            'BaseRequest': self.wxapi.base_request,
            'Count': len(groups),
            'List': groups
        }
        session_response = self.wxapi.webwx_batch_get_contact(params)
        
        if session_response['Count'] and session_response['Count'] > 0:
            session_list = session_response['ContactList']
            for x in session_list:
                for ss in self.wxapi.session_list:
                    if ss["UserName"] == x["UserName"]:
                        ss = x
                        break
            session_list.sort(key=lambda mm: mm['AttrStatus'],reverse=True)
            #self.wxapi.session_list.extend(session_list)
    
    def prepare4Environment(self):
        if os.path.exists(self.app_home):
            self.clear()
        else:
            os.makedirs(self.app_home)
            
        if os.path.exists(self.contact_head_home):
            self.clear()
        else:
            os.makedirs(self.contact_head_home)
            
        if os.path.exists(self.cache_home):
            pass
        else:
            os.makedirs(self.cache_home)
        
        if os.path.exists(self.head_home):
            pass
        else:
            os.makedirs(self.head_home)
            
        if os.path.exists(self.cache_image_home):
            pass
        else:
            os.makedirs(self.cache_image_home)
    '''
                删除下载的头像文件
    '''
    def clear(self):
        for i in os.listdir(self.contact_head_home):
            head_path = os.path.join(self.contact_head_home,i)
            if os.path.isfile(head_path):
                os.remove(head_path)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        print("dragEnterEvent")

    def dragMoveEvent(self, event):
        print("dragMoveEvent")
    
    def is_image(self,path):
        if not path:
            return False
        if path.endswith("jpg") or path.endswith("jpeg") or path.endswith("png"):
            return True
        
    def dropEvent(self, event):
        #print("dropEvent")
        if event.mimeData().hasUrls():
            #遍历输出拖动进来的所有文件路径
            for url in event.mimeData().urls():
                file_name = str(url.toLocalFile())
                if self.is_image(file_name):
                    self.draft.append("<img src=%s width=80 height=80>"%(file_name))
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
        user_icon_file = self.contact_head_home + self.wxapi.user['UserName'] + ".jpg"
        user_head_image = QtGui.QImage()
        if user_head_image.load(user_icon_file):
            self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))
        else:
            if user_head_image.load(self.default_head_icon):
                self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))

    
    def append_contact_row(self,contact,data_model,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        # user name item
        user_name = contact['UserName']
        user_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
        cells.append(user_name_item)
        
        user_head_icon_path = self.contact_head_home + contact['UserName']+".jpg"
        item = QtGui.QStandardItem(QIcon(user_head_icon_path),"")
        cells.append(item)
        
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        # user remark or nick name
        remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
        cells.append(remark_nick_name_item)
        #
        tips_count_item = QtGui.QStandardItem()
        cells.append(tips_count_item)
        if "APPEND" == action:
            data_model.appendRow(cells)
        elif "INSERT" == action and row >= 0:
            data_model.insertRow(row,cells)
        else:
            data_model.appendRow(cells)
        
        
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
        for contact in self.wxapi.session_list:
            self.append_contact_row(contact,self.sessionTableModel)
            
        
        for session in sorted([x for x in self.wxapi.member_list if x["AttrStatus"] and x["AttrStatus"] > 0],key=lambda ct: ct["AttrStatus"],reverse=True):
            exist = False
            for contact in self.wxapi.session_list:
                if contact["UserName"] == session["UserName"]:
                    exist = True
            if not exist:
                self.append_contact_row(session,self.sessionTableModel)
            '''
            '''
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
            self.append_contact_row(member,self.memberTableModel)
            
        self.memberWidget.clicked.connect(self.member_item_clicked)

    def init_reader(self):
        pass
        #self.readerListWidget.addItem("readers")
        #self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def session_button_clicked(self):
        self.memberWidget.setVisible(False)
        self.sessionWidget.setVisible(True)

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
        user_name_o = self.sessionTableModel.data(user_name_index)

        tip_index = self.sessionTableModel.index(current_row,3)
        tips_item = self.sessionTableModel.data(tip_index)
        if tips_item:
            self.sessionTableModel.setData(tip_index, "")
        #if message_count:
        #    count = int(message_count)
        user_name = str(user_name_o.toString())
        contact = self.get_contact(user_name)
        if not contact:
            contact = self.get_member(user_name)
        self.current_chat_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        if user_name.find('@@') >= 0:
            self.currentChatUser.setText(("%s (%d)")%(QtCore.QString.fromUtf8(dn),contact["MemberCount"]))
        else:
            self.currentChatUser.setText(QtCore.QString.fromUtf8(dn))
        self.messages.setText('')
        for (key,messages_list) in self.msg_cache.items():
            if user_name == key:
                for message in messages_list:
                    msg_type = message['MsgType']
                    if msg_type:
                        if msg_type == 2 or msg_type == 51 or msg_type == 52:
                            continue
                        if msg_type == 1:
                            self.text_msg_handler(message)
                        elif msg_type == 3:
                            self.image_msg_handler(message)
                        elif msg_type == 34:
                            self.voice_msg_handler(message)
                        elif msg_type == 49:
                            self.app_msg_handler(message)
                        elif msg_type == 10002:
                            self.sys_msg_handler(message)
                        else:
                            self.default_msg_handler(message)
                break

    def current_chat_user_click(self):
        if False and self.memberListWidget:
            print("visible ddd%s:"+str(self.memberListWidget.isHidden()))
            if self.memberListWidget.isHidden():
                rect = self.geometry()
                self.memberListWidget.resize(QSize(MemberListWidget.WIDTH,rect.height()+self.frameGeometry().height()-self.geometry().height()))
                self.memberListWidget.move(self.frameGeometry().x()+self.frameGeometry().width(), self.frameGeometry().y())
                self.memberListWidget.exec_()
                print("show")
            else:
                self.memberListWidget.hide()
                print("hide")
        else:
            rect = self.geometry()
            print(rect.left(), rect.top())
            print(self.frameGeometry())
            print(rect.width(), rect.height())
            memebers = [self.current_chat_contact]
            if self.current_chat_contact['UserName'].find('@@') >= 0:
                memebers = self.current_chat_contact["MemberList"]
            self.memberListWidget = MemberListWidget(memebers,self.wxapi.member_list,self)
            self.memberListWidget.resize(QSize(MemberListWidget.WIDTH,rect.height()+self.frameGeometry().height()-self.geometry().height()))
            self.memberListWidget.move(self.frameGeometry().x()+self.frameGeometry().width(), self.frameGeometry().y())
            
            self.memberListWidget.Signal_OneParameter.connect(self.getSelectedUsers)
            self.memberListWidget.show()
            
    @pyqtSlot(str)
    def getSelectedUsers(self,users):
        '''
                        建群
        '''
        if not users:
            return
        print(str(users))
        #dictt = json.loads(str(users))
        user_list = str(users).split(";")
        member_list = []
        for s_user in user_list:
            if len(s_user) > 1:
                user = {}
                user['UserName']=s_user
                member_list.append(user)
        user = {}
        user['UserName']=self.current_chat_contact["UserName"]
        member_list.append(user)
        #i
        i = {}
        i['UserName']=self.wxapi.user["UserName"]
        #member_list.append(i)
        
        response_data = self.wxapi.webwx_create_chatroom(member_list)
        print("webwx_create_chatroom response:%s"%response_data)
        data_dict = json.loads(response_data)
        if data_dict["BaseResponse"]["Ret"] == 0:
            chat_room_name = data_dict["ChatRoomName"]
            data = {
                'BaseRequest': self.wxapi.base_request,
                'Count': 1,
                'List': [{"UserName":chat_room_name,"ChatRoomId":""}]
            }
            batch_response = self.wxapi.webwx_batch_get_contact(data)
            if batch_response['Count'] and batch_response['Count'] > 0:
                new_contact = batch_response['ContactList'][0]
                remark_name = ("%s,%s,%s")%(self.wxapi.user["NickName"],self.current_chat_contact["NickName"],"")
                new_contact["RemarkName"]=remark_name
                self.wxapi.member_list.append(new_contact)
                self.wxapi.webwx_get_head_img(new_contact["UserName"], new_contact["HeadImgUrl"])
                self.append_contact_row(new_contact,self.sessionTableModel,action="INSERT",row=0)
            
        
    def member_item_clicked(self):
        self.chatWidget.setVisible(True)
        self.label.setVisible(False)
        current_row =self.memberWidget.currentIndex().row()
        user_name_index = self.memberTableModel.index(current_row,0)
        user_name_o = self.memberTableModel.data(user_name_index)
        user_name = user_name_o.toString()
        contact = self.get_member(user_name)
        self.current_chat_contact = contact
        dn = contact['RemarkName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUser.setText(QtCore.QString.fromUtf8(dn))
        self.messages.setText('')
        if self.msg_cache.has_key(user_name):
            messages_list = self.msg_cache[user_name]
            for message in messages_list:
                self.messages.append(QtCore.QString.fromUtf8(message))
    '''
                把消息發送出去
    '''
    def send_msg(self):
        msg_text = str(self.draft.toPlainText())
        msg = Msg(1, msg_text, self.current_chat_contact['UserName'])
        response = self.wxapi.webwx_send_msg(msg)
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        self.messages.append(format_msg)
        self.messages.append(QtCore.QString.fromUtf8(msg_text))
        self.draft.setText('')
        #TODO FIX BUG
        if False:
            row_count = self.sessionTableModel.rowCount()
            find = False
            for row_number in range(row_count):
                user_name_index = self.sessionTableModel.index(row_number,0)
                user_name_obj = self.sessionTableModel.data(user_name_index)
                user_name = user_name_obj.toString()
                if user_name and user_name == self.current_chat_contact['UserName']:
                    find = True
                    tip_index = self.sessionTableModel.index(row_number,3)
                    tips_count_obj = self.sessionTableModel.data(tip_index)
                    if tips_count_obj:
                        tips_count = tips_count_obj.toInt()
                        if tips_count:
                            count = tips_count[0]
                            self.sessionTableModel.setData(tip_index, str(count+1))
                        else:
                            self.sessionTableModel.setData(tip_index, "1")
                    else:
                        count_tips_item = QtGui.QStandardItem("1")
                        self.sessionTableModel.setItem(row_number, 3, count_tips_item)
                    #提昇from_user_name在會話列表中的位置
                    #move this row to the top of the sessions
                    taked_row = self.sessionTableModel.takeRow(row_number)
                    self.sessionTableModel.insertRow(0 ,taked_row)
                    break;
            if find == False:
                cells = []
                # user name item
                user_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
                cells.append(user_name_item)
                
                item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
                cells.append(item)
                
                dn = self.current_chat_contact['RemarkName']
                if not dn:
                    dn = self.current_chat_contact['NickName']
                # user remark or nick name
                remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
                cells.append(remark_nick_name_item)
                
                count_tips_item = QtGui.QStandardItem("1")
                cells.append(count_tips_item)
                
                self.sessionTableModel.insertRow(0,cells)
        self.up_2_top()
    '''
        把圖片發送出去
    '''
    def upload_send_msg_image(self,contact,image):
        upload_response = self.wxapi.webwx_upload_media(contact,image)
        json_upload_response = json.loads(upload_response)
        media_id = json_upload_response['MediaId']
        msg = Msg(3, str(media_id), self.current_chat_contact['UserName'])
        send_response = self.wxapi.webwx_send_msg_img(msg)
        self.up_2_top()
        return send_response
        
    def up_2_top(self):
        #提昇from_user_name在會話列表中的位置
        #move this row to the top of the sessions
        current_row = self.sessionWidget.currentIndex().row()
        taked_row = self.sessionTableModel.takeRow(current_row)
        self.sessionTableModel.insertRow(0 ,taked_row)
        self.sessionWidget.selectRow(0)
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
        if not self.current_chat_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
            self.messages.append(QtCore.QString.fromUtf8("請在手機端收聽語音"))
        else:
            pass
    '''
        把語音消息加入到聊天記錄裏
    '''
    def video_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_chat_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
            self.messages.append(QtCore.QString.fromUtf8("請在手機端觀看視頻"))
        else:
            pass
    '''
        把文本消息加入到聊天記錄裏
    '''
    def text_msg_handler(self,msg):
        if not self.current_chat_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        from_user_name = msg['FromUserName']
        
        if from_user_name == self.wxapi.user["UserName"]:
            from_user = self.wxapi.user
        else:
            from_user = self.get_contact(from_user_name)
        #如果為群，則消息來源顯示from_member_name
        from_user_display_name = from_member_name= None
        from_user_name = msg['FromUserName']
        msg_content = msg['Content']
        #如果是群消息
        if from_user_name.find('@@') >= 0:
            index = msg_content.index(":")
            
            if index > 0:
                from_user_display_name = from_member_name = msg_content[0:index]
                msg_content = msg_content[index:len(msg_content)]
                
            members = from_user["MemberList"]
            for member in members:
                if from_member_name == member['UserName']:
                    from_user_display_name = member['RemarkName'] if member.has_key("RemarkName") else ""
                    if not from_user_display_name:
                        from_user_display_name = member['NickName'] if member.has_key("NickName") else ""
                    break
        else:
            from_user_display_name = from_user['RemarkName']
            if not from_user_display_name:
                from_user_display_name = from_user['NickName']
                
        if not from_user_display_name:
            from_user_display_name = from_user_name
        format_msg = ('(%s) %s:') % (st, from_user_display_name)
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8("%s\r\n%s"%(format_msg,msg_content)))
        else:
            pass
        
    def download_msg_img(self,msg_id):
        data = self.wxapi.webwx_get_msg_img(msg_id)
        if not data:
            return False
        img_cache_folder = ('%s/cache/img/'%(self.app_home))
        msg_img = img_cache_folder+msg_id+'.jpg'
        with open(msg_img, 'wb') as image:
            image.write(data)
        return True
        
    '''
        把文本消息加入到聊天記錄裏
    '''
    def image_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_chat_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        msg_id = msg['MsgId']
        self.wxapi.webwx_get_msg_img(msg_id)
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
            
            msg_img = ('<img src=%s/%s.jpg>'%(self.cache_image_home,msg_id))
            self.messages.append(msg_img)
        else:
            pass
    '''
        系統消息處理
    '''
    def sys_msg_handler(self,msg):
        from_user_name = msg['FromUserName']
        if not self.current_chat_contact:
            pass
        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
        xml_content = msg['Content']
        if xml_content:
            xml_content = xml_content.replace("&gt;",">")
            xml_content = xml_content.replace("&lt;","<")
            xml_content = xml_content.replace("<br/>","")
        
        doc = xml.dom.minidom.parseString(xml_content)
        replacemsg_nodes = doc.getElementsByTagName("replacemsg")
        #old_msgid
        #TODO 用old msg id 從歷史中刪去
        if replacemsg_nodes:
            replacemsg = str(replacemsg_nodes[0].firstChild.data)
        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
        
        # 如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(("%s\r\n%s")%(format_msg,replacemsg)))
        else:
            pass
        
    def app_msg_handler(self,msg):
        '''把應用消息加入到聊天記錄裏，應該指的是由其他應用分享的消息
        '''
        from_user_name = msg['FromUserName']
        if not self.current_chat_contact:
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
        format_msg = ('(%s) %s:') % (st, from_user_name)
        
        '''
            如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            self.messages.append(QtCore.QString.fromUtf8(format_msg))
            self.messages.append(QtCore.QString.fromUtf8(('%s %s %s')%(title,desc,app_url)))
        else:
            pass
        
    '''
    '''       
    def put_msg_cache(self,msg):
        from_user_name = msg['FromUserName']
        if self.msg_cache.has_key(from_user_name):
            messages_list = self.msg_cache[from_user_name]
        else:
            messages_list = []
        messages_list.append(msg)
        self.msg_cache[from_user_name] = messages_list
        #TODO ADD TIPS
        '''
                        增加消息數量提示（提昇此人在會話列表中的位置）
        '''
        exist = False#此人是否在會話列表中
        row_count = self.sessionTableModel.rowCount()
        for row in range(row_count):
            index = self.sessionTableModel.index(row,0)
            user_name_o = self.sessionTableModel.data(index)
            user_name = user_name_o.toString()
            #user_name = self.sessionTableModel.item(i,0).text()
            if user_name and user_name == from_user_name:
                exist = True
                tip_index = self.sessionTableModel.index(row,3)
                tips_count_obj = self.sessionTableModel.data(tip_index)
                if tips_count_obj:
                    tips_count = tips_count_obj.toInt()
                    if tips_count:
                        count = tips_count[0]
                        self.sessionTableModel.setData(tip_index, str(count+1))
                    else:
                        self.sessionTableModel.setData(tip_index, "1")
                else:
                    count_tips_item = QtGui.QStandardItem("1")
                    self.sessionTableModel.setItem(row, 3, count_tips_item)
                #提昇from_user_name在會話列表中的位置
                #move this row to the top of the sessions
                taked_row = self.sessionTableModel.takeRow(row)
                self.sessionTableModel.insertRow(0 ,taked_row)
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
            
            item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
            cells.append(item)
            
            # user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem(QtCore.QString.fromUtf8(dn))
            cells.append(remark_nick_name_item)
            
            count_tips_item = QtGui.QStandardItem("1")
            cells.append(count_tips_item)
            
            self.sessionTableModel.insertRow(0,cells)
    
    def webwx_sync_process(self, data):
        '''
        @param data
        MSTTYPE:
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
            print("msg body:%s"%str(msg))
            msg_type = msg['MsgType']
            if msg_type:
                from_user_name = msg['FromUserName']
                if msg_type == 2 or msg_type == 51 or msg_type == 52:
                    continue
                '''
                没有選擇和誰對話或者此消息的發送人和當前的對話人不一致，則把消息存放在message_cache中;
                如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
                '''
                if (not self.current_chat_contact) or from_user_name != self.current_chat_contact['UserName']:
                    self.put_msg_cache(msg)
                else:
                    if msg_type == 1:
                        self.text_msg_handler(msg)
                    elif msg_type == 3:
                        self.image_msg_handler(msg) 
                    elif msg_type == 34:
                        self.voice_msg_handler(msg)
                    elif msg_type == 49:
                        self.app_msg_handler(msg)
                    elif msg_type == 10002:
                        self.sys_msg_handler(msg)
                    else:
                        self.default_msg_handler(msg)

    def select_document(self):
        fileDialog = QFileDialog(self)
        if fileDialog.exec_():
            fileNames = fileDialog.selectedFiles()
            for fileName in fileNames:
                fileName = str(fileName)
                if self.is_image(fileName):
                    send_response = self.upload_send_msg_image(self.current_chat_contact,fileName)
                    json_send_response = json.loads(send_response)
                    
                    msg_id = json_send_response["MsgID"]
                    #send success append the image to history;failed append to draft 
                    if msg_id:
                        self.wxapi.webwx_get_msg_img(msg_id)
                        st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
                        format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
                        self.messages.append(format_msg)
                        msg_img = ('<img src=%s/%s.jpg>'%(self.cache_image_home,msg_id))
                        self.messages.append(msg_img)
                    else:
                        fileName=QtCore.QString.fromUtf8(fileName)
                        self.draft.append("<img src=%s width=80 height=80>"%(fileName))
                else:
                    print(fileName)
                    
    def keyPressEvent(self,event):
        print("keyPressEvent")
        
    def sync(self):
        while (True):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            print('sync %s' %(st))
            (code, selector) = self.wxapi.sync_check()
            if code == -1 and selector == -1:
                print("self.wxapi.sync_check() error")
            else:
                if code != '0':
                    if code == '1101' and selector == '0':
                        print("session timeout")
                        self.do_logout()
                else:
                    if selector != '0':
                        sync_response = self.wxapi.webwx_sync()
                        #print("WeChatSync.run#webwx_sync:")
                        #print(sync_response)
                        self.webwx_sync_process(sync_response)
            sleep(11)
            
class MemberListWidget(QtGui.QDialog):
    WIDTH = 300
    Signal_OneParameter = pyqtSignal(str)
    
    def __init__(self,member_list,contacts,parent = None):
        super(MemberListWidget,self).__init__(parent)
        self.user_home = os.path.expanduser('~')
        self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = '%s/default/default.png'%(self.head_home)
        self.members = member_list
        self.contacts = contacts
        #self.setWindowFlags(Qt.FramelessWindowHint)#|Qt.Popup
        self.membersTable = QTableView()
        self.membersTable.verticalHeader().setDefaultSectionSize(60)
        self.membersTable.verticalHeader().setVisible(False)
        self.membersTable.horizontalHeader().setDefaultSectionSize(60)
        self.membersTable.horizontalHeader().setVisible(False)
        #More
        self.more = QPushButton(QtCore.QString.fromUtf8('顯示更多'))
        self.verticalSpacer = QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        
        self.membersTableModel = QStandardItemModel(1,4)
        self.initinal_member_list_widget(self.members)
        mainLayout=QVBoxLayout()
        mainLayout.addWidget(self.membersTable)
        mainLayout.addWidget(self.more)
        mainLayout.addItem(self.verticalSpacer)
        self.setLayout(mainLayout)
        
    def initinal_member_list_widget(self,member_list):
        #self.membersTableModel.setHorizontalHeaderItem(0,QStandardItem("0000"))
        self.append_row(member_list, self.membersTableModel)
        self.membersTable.setModel(self.membersTableModel)
        self.membersTable.setIconSize(QSize(40,40))
        self.membersTable.clicked.connect(self.member_click)
        
    def member_click(self):
        print("member_clicked")
        self.memberListWindow = ContactListWindow(self.contacts,self)
        self.memberListWindow.resize(400,600)
        self.memberListWindow.Signal_OneParameter.connect(self.route)
        self.memberListWindow.show()
    
    @pyqtSlot(str)
    def route(self,objectt):
        self.Signal_OneParameter.emit(objectt)
        
    def append_row(self,members,data_model):
        ###############
        cells = []
        item = QtGui.QStandardItem(QtCore.QString.fromUtf8("+"))
        cells.append(item)
        for member in members[0:3]:
            user_head_path = self.contact_head_home + member['UserName']+".jpg"
            if not os.path.exists(user_head_path):
                user_head_path = self.default_head_icon
            dn = member['DisplayName']
            if not dn:
                dn = member['NickName']
            item = QtGui.QStandardItem(QIcon(user_head_path),QtCore.QString.fromUtf8(dn))
            cells.append(item)
        data_model.appendRow(cells)
        i = 3
        members_len = len(members)
        if members_len > 15:
            members_len = 15
        while i < members_len:
            cells = []
            for member in members[i:i+4]:
                user_head_path = self.contact_head_home + member['UserName']+".jpg"
                if not os.path.exists(user_head_path):
                    user_head_path = self.default_head_icon
                dn = member['DisplayName']
                if not dn:
                    dn = member['NickName']
                item = QtGui.QStandardItem(QIcon(user_head_path),QtCore.QString.fromUtf8(dn))
                cells.append(item)
            i = i + 4
            data_model.appendRow(cells)
    def update_memebers(self,member_list):
        pass
    
class ContactListWindow(QtGui.QDialog):
    WIDTH = 600
    Signal_OneParameter = pyqtSignal(str)
    
    def __init__(self,member_list,parent = None):
        super(ContactListWindow,self).__init__(parent)
        self.setModal(True)
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = '%s/default/default.png'%(self.head_home)
        self.members = member_list
        self.membersTable = QTableView()
        self.membersTable.verticalHeader().setDefaultSectionSize(60)
        self.membersTable.verticalHeader().setVisible(False)
        #self.membersTable.horizontalHeader().setDefaultSectionSize(60)
        self.membersTable.horizontalHeader().setVisible(False)
        #confirm
        self.confirm = QPushButton(QtCore.QString.fromUtf8("確定"),self)
        self.membersTableModel = QStandardItemModel(1,4)
        self.initinal_member_list_widget()
        mainLayout=QVBoxLayout()
        mainLayout.addWidget(self.membersTable)
        mainLayout.addWidget(self.confirm)
        self.setLayout(mainLayout)
        #connected
        self.membersTable.clicked.connect(self.member_item_clicked)
        self.confirm.clicked.connect(self.do_confirm)
        
    def initinal_member_list_widget(self):
        self.append_row(self.members, self.membersTableModel)
        self.membersTable.setModel(self.membersTableModel)
        self.membersTable.setIconSize(QSize(40,40))
        
    def append_row(self,members,data_model):
        for (i,member) in enumerate(members):
            cells = []
            user_name = member['UserName']
            user_name_cell = QtGui.QStandardItem(QtCore.QString.fromUtf8(user_name))
            cells.append(user_name_cell)
            
            user_head_path = self.contact_head_home + member['UserName']+".jpg"
            if not os.path.exists(user_head_path):
                user_head_path = self.default_head_icon
            dn = member['DisplayName']
            if not dn:
                dn = member['NickName']
            item = QtGui.QStandardItem(QIcon(user_head_path),QtCore.QString.fromUtf8(dn))
            cells.append(item)
            data_model.appendRow(cells)
            rb = QRadioButton("0000",self)
            self.membersTable.setIndexWidget(data_model.index(i,3),rb)
    
    def member_item_clicked(self):
        selections = self.membersTable.selectionModel()
        selectedIndexes = selections.selectedIndexes()
        self.confirm.setText(QtCore.QString.fromUtf8("確定(%s)"%len(selectedIndexes)))
        
    def do_confirm(self):
        selections = self.membersTable.selectionModel()
        selectedIndexes = selections.selectedIndexes()
        selected_user_names = ""
        for index in selectedIndexes:
            row = index.row()
            index = self.membersTableModel.index(row,0)
            user_name_obj = self.membersTableModel.data(index)
            if user_name_obj:
                user_name = user_name_obj.toString()
                user = {}
                user['UserName']=str(user_name)
                selected_user_names=selected_user_names+(user_name)
                selected_user_names=selected_user_names+(";")
        if len(selected_user_names) > 0:
            dictt = {}
            dictt['UserNames']=selected_user_names
            self.Signal_OneParameter.emit(selected_user_names)
        
        self.close()
