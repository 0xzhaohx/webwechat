#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''

__date__='2018年3月25日'

import sip
sip.setapi('QString', 1)
sip.setapi('QVariant', 1)

import sys
import os
import threading
import re
from time import sleep
import time
from com.ox11.wechat.emotion import Emotion
from com.ox11.wechat.about import About
from com.ox11.wechat import property
from com.ox11.wechat.labeldelegate import LabelDelegate
from api.msg import Msg

import xml.dom.minidom
import json
import logging

from PyQt4.Qt import QIcon, QCursor, Qt, QTextImageFormat
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QStandardItemModel, QFileDialog, QMenu, QAction,\
    QTableView, QVBoxLayout, QPushButton, QSpacerItem
from PyQt4.QtCore import QSize, pyqtSlot, pyqtSignal, QPoint

reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.5.ui"


WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    I18N = "resource/i18n/resource.properties"
    
    EMOTION_DIR = "./resource/expression"
    
    LOG_FORMAT = '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s'
    '''
        webwx_init
        ->webwxstatusnotify()
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->webwx_getcontact
        ->first call webwx_batch_getcontact
        ->(webwx_geticon|webwx_batch_getheadimg)
        ->second call webwx_batch_getcontact
    '''
    
    initialed = pyqtSignal()
    
    def __init__(self,wxapi):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.config = {
           
        }
        logging.basicConfig(filename='./wechat.log',level=logging.DEBUG,format=WeChat.LOG_FORMAT)
        self.user_home = os.path.expanduser('~')
        self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = './resource/images/default.png'
        self.current_chat_contact = None
        self.msg_cache = {}
        #没有來得及處理的新消息
        self.new_msg_cache = []
        self.prepare4Environment()
        self.wxapi = wxapi
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.chatsModel = QStandardItemModel(0,4)
        self.friendsModel = QStandardItemModel(0,3)
        self.publicModel = QStandardItemModel()
        #after initial model,do login
        self.wxapi.login()
        
        self.wxinitial()
        #self.synct = WeChatSync(self.wxapi)
        #self.synct.start()
        timer = threading.Timer(5, self.synccheck)
        timer.setDaemon(True)
        timer.start()
        
        self.memberListWidget = None
        self.friendsWidget.setVisible(False)
        self.publicWidget.setVisible(False)
        self.profileWidget.setVisible(False)
        self.init_chats()
        self.init_friends()
        self.init_public()
        self.emotionscodeinitial()
        self.initialed.connect(self.process_new_msg_cache)
        self.initialed.emit()
        
        self.chatAreaWidget.setVisible(False)
        self.chatsWidget.setItemDelegate(LabelDelegate())
        self.chatsWidget.setIconSize(QSize(40,40))
        self.chatsWidget.setModel(self.chatsModel)
        self.chatsWidget.selectionModel().selectionChanged.connect(self.chat_item_clicked)
        self.chatsWidget.setColumnHidden(0,True)
        self.chatsWidget.setColumnHidden(3,True)
        self.chatsWidget.setColumnWidth(1, 70);
        self.chatsWidget.setColumnWidth(3, 30);
        #self.chatsWidget.horizontalHeader().setStretchLastSection(True)
        self.friendsWidget.setModel(self.friendsModel)
        self.friendsWidget.setIconSize(QSize(40,40))
        self.friendsWidget.setColumnHidden(0,True)
        self.friendsWidget.setColumnWidth(1, 70);
        self.friendsWidget.setColumnWidth(3, 30);
        self.publicWidget.setModel(self.publicModel)

        self.chatButton.clicked.connect(self.switch_chat)
        self.friendButton.clicked.connect(self.switch_friend)

        self.sendButton.clicked.connect(self.send_msg)
        self.emotionButton.clicked.connect(self.select_emotion)
        self.selectImageFileButton.clicked.connect(self.select_document)
        self.currentChatUser.clicked.connect(self.current_chat_user_click)
        self.showMemberButton.clicked.connect(self.showMembers)
        self.addMenu4SendButton()
        self.addMenu4SettingButton()
    
    def process_new_msg_cache(self):
        logging.debug('start process new_msg_cache')
        for msg in self.new_msg_cache:
            self.msg_handle(msg)
    
    def wxinitial(self):
        sessions_dict = self.wxapi.webwx_init()
        res = self.wxapi.webwxstatusnotify()
        self.setupwxuser()
        
        #TODO download the head image or icon of contact
        #fetch the icon or head image that init api response
        groups = []
        for contact in sessions_dict['ContactList']:
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            if user_name.startswith('@@'):
                #prepare arguments for batch_get_contact api
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                groups.append(group)
                #doanload head image
                self.wxapi.webwx_get_head_img(user_name,head_img_url)
            elif user_name.startswith('@'):
                self.wxapi.webwx_get_icon(user_name,head_img_url)
            else:
                pass
        #do downlaod icon
        self.wxapi.webwx_get_contact()
        self.synccheck(loop=False)
        params = {
            'BaseRequest': self.wxapi.base_request,
            'Count': len(groups),
            'List': groups
        }
        self.batch_get_contact(data=params)
    
    def addMenu4SendButton(self):
        menu = QMenu()
        enterAction = QAction(unicode("按Enter發送消息"),self)
        menu.addAction(enterAction)
        self.sendSetButton.setMenu(menu)
        
    def addMenu4SettingButton(self):
        menu = QMenu()
        createChatRoorAction = QAction(unicode("開始聊天"),self)
        menu.addAction(createChatRoorAction)
        notifySwitchAction = QAction(unicode("關閉通知"),self)
        menu.addAction(notifySwitchAction)
        soundSwitchAction = QAction(unicode("關閉聲音"),self)
        menu.addAction(soundSwitchAction)
        logoutAction = QAction(unicode("退出"),self)
        menu.addAction(logoutAction)
        aboutAction = QAction(unicode("關於"),self)
        menu.addAction(aboutAction)
        self.settingButton.setMenu(menu)
        
        aboutAction.triggered.connect(self.showAbout)
        
    def showAbout(self):
        about = About(self)
        about.show()
        
    def emotionscodeinitial(self):
        self.emotionscode = property.parse(WeChat.I18N).properties or {}
        
    def do_logout(self):
        print("logout..............")
    
    def batch_get_contact(self,data=None):
        if not data:
            groups = []
            for contact in self.wxapi.chat_list:
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
        else:
            params = data
            
        session_response = self.wxapi.webwx_batch_get_contact(params)
            
        if session_response['Count'] and session_response['Count'] > 0:
            session_list = session_response['ContactList']
            for x in session_list:
                for i,ss in enumerate(self.wxapi.chat_list):
                    if ss["UserName"] == x["UserName"]:
                        self.wxapi.chat_list[i] = x
                        break
            #chat_list.sort(key=lambda mm: mm['AttrStatus'],reverse=True)
            #self.wxapi.chat_list.extend(session_list)
        return session_response
    
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
    def clear(self):
        '''
        #删除下载的头像文件
        '''
        for i in os.listdir(self.contact_head_home):
            head_icon = os.path.join(self.contact_head_home,i)
            if os.path.isfile(head_icon):
                os.remove(head_icon)
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        print("dragEnterEvent")

    def dragMoveEvent(self, event):
        print("dragMoveEvent")
    
    def isImage(self,path):
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
                if self.isImage(file_name):
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

    def setupwxuser(self):
        userName = self.wxapi.user['NickName']
        self.userNameLabel.setText(unicode(userName))
        user_icon = self.contact_head_home + self.wxapi.user['UserName'] + ".jpg"
        user_head_image = QtGui.QImage()
        if user_head_image.load(user_icon):
            self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))
        else:
            if user_head_image.load(self.default_head_icon):
                self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))

    def emotioncode(self,msg):
        imagepattern=re.compile(r'src="([.*\S]*\.gif)"',re.I)
        ppattern = re.compile(r'<p style=".*\S">(.+?)</p>', re.I)
        pimages = []
        ps = ppattern.findall(msg)
        for p in ps:
            pimage = {}
            pimage["p"]=p
            images = imagepattern.findall(p,re.I)
            for image in images:
                #print("emotion:%s"%image)
                for key,emotioncode in self.emotionscode.items():
                    epath = os.path.join(WeChat.EMOTION_DIR,("%s.gif")%key)
                    imagemark = ('<img src="%s" />')%(epath)
                    if image ==epath:
                        #print('[%s]'%((emotioncode)))
                        pcode = p.replace(imagemark,'[%s]'%(unicode(emotioncode)))
                        #print("p coded:%s"%pcode)
                        pimage["p"]=pcode
                        break
            pimage["images"]=images
            pimages.append(pimage)
        return pimages
    
    def emotiondecode(self,msg):
        emotionPattern =re.compile(u"\[[\u4e00-\u9fa5]{1,3}\]")
        result=re.findall(emotionPattern,str(msg).decode("utf-8"))
        for emotion in result:
            #print emotion
            for key,val in self.emotionscode.items():
                if emotion ==("[%s]")%val:
                    epath = os.path.join(WeChat.EMOTION_DIR,("%s.gif")%key)
                    msg = msg.replace(emotion,("<img src=%s>")%(epath))
                    break
        return msg
        
    def append_chat(self,contact,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        # user name item
        user_name = contact['UserName']
        user_name_item = QtGui.QStandardItem(unicode(user_name))
        cells.append(user_name_item)
        
        user_head_icon = self.contact_head_home + user_name+".jpg"
        item = QtGui.QStandardItem(QIcon(user_head_icon),"")
        cells.append(item)
        
        dn = contact['RemarkName'] or contact['NickName']
        #if not dn:
            #dn = contact['NickName']
        # user remark or nick name
        remark_nick_name_item = QtGui.QStandardItem(unicode(dn))
        cells.append(remark_nick_name_item)
        #
        tips_count_item = QtGui.QStandardItem()
        cells.append(tips_count_item)
        if "APPEND" == action:
            self.chatsModel.appendRow(cells)
        elif "INSERT" == action and row >= 0:
            self.chatsModel.insertRow(row,cells)
        else:
            self.chatsModel.appendRow(cells)
            
    def append_friend(self,contact,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        # user name item
        user_name = contact['UserName']
        user_name_item = QtGui.QStandardItem(unicode(user_name))
        cells.append(user_name_item)
        
        user_head_icon = self.contact_head_home + user_name+".jpg"
        item = QtGui.QStandardItem(QIcon(user_head_icon),"")
        cells.append(item)
        
        _name = contact['RemarkName'] or contact['NickName']
        #if not dn:
            #dn = contact['NickName']
        # user remark or nick name
        _name_item = QtGui.QStandardItem(unicode(_name))
        cells.append(_name_item)
        #
        if "APPEND" == action:
            self.friendsModel.appendRow(cells)
        elif "INSERT" == action and row >= 0:
            self.friendsModel.insertRow(row,cells)
        else:
            self.friendsModel.appendRow(cells)
        
        
    def init_chats(self):
        '''
        contact table (5 columns)
        column 1:user name(will be hidden)
        column 2:head icon
        column 3:remark or nick name
        column 4:message count tips(will be hidden)
        :return:
        '''
        #self.chatsWidget.setColumnCount(4)
        ''''''
        for chat_contact in self.wxapi.chat_list:
            self.append_chat(chat_contact)
            
        '''
        for session in sorted([x for x in self.wxapi.friend_list if x["AttrStatus"] and x["AttrStatus"] > 0],key=lambda ct: ct["AttrStatus"],reverse=True):
            exist = False
            for contact in self.wxapi.chat_list:
                if contact["UserName"] == session["UserName"]:
                    exist = True
            if not exist:
                self.append_contact_row(session,self.chatsModel)
        '''
        #self.chatsWidget.clicked.connect(self.chat_item_clicked)

    def init_friends(self):
        ''''''
        #self.friendsModel.setColumnHidden(0,True)
        '''
        /***/
        /*去掉每行的行号*/ 
        QHeaderView *headerView = table->verticalHeader();  
        headerView->setHidden(true);  
        '''
        self.friendsWidget.setColumnHidden(1,True)
        group_contact_list = []
        for member in self.wxapi.friend_list:
            group_contact_list.append(member)
        group_contact_list.sort(key=lambda mm: mm['RemarkPYInitial'] or mm['PYInitial'])
        #group_contact_list.sort(key=lambda mm: mm['RemarkPYQuanPin'] or mm['PYQuanPin'])

        for member in group_contact_list:#.sort(key=lambda m: m['PYInitial'])
            self.append_friend(member)
            
        self.friendsWidget.clicked.connect(self.member_item_clicked)

    def init_public(self):
        pass
        #self.readerListWidget.addItem("readers")
        #self.readerListWidget.clicked.connect(self.contact_cell_clicked)

    def switch_chat(self):
        current_row =self.chatsWidget.currentIndex().row()
        if current_row > 0:
            self.chatAreaWidget.setVisible(True)
            self.label.setVisible(False)
        else:
            self.label.setVisible(True)
            self.chatAreaWidget.setVisible(False)
            
        self.chatsWidget.setVisible(True)
        self.friendsWidget.setVisible(False)
        self.profileWidget.setVisible(False)

    def public_button_clicked(self):
        self.friendsWidget.setVisible(False)
        self.chatsWidget.setVisible(False)
        self.publicWidget.setVisible(True)

    def switch_friend(self):
        current_row =self.friendsWidget.currentIndex().row()
        if current_row > 0:
            self.label.setVisible(False)
            self.profileWidget.setVisible(True)
        else:
            self.label.setVisible(True)
            self.profileWidget.setVisible(False)
            
        self.friendsWidget.setVisible(True)
        self.chatsWidget.setVisible(False)
        self.chatAreaWidget.setVisible(False)

    def get_contact(self,user_name):
        return self.get_member(user_name)

    def get_member(self,user_name):
        for member in self.wxapi.chat_list:
            if user_name == member['UserName']:
                return member
            
        for member in self.wxapi.friend_list:
            if user_name == member['UserName']:
                return member
            
    def chat_item_clicked(self):
        self.chatAreaWidget.setVisible(True)
        self.label.setVisible(False)
        #self.memberListWidget.destroy()
        current_row = self.chatsWidget.currentIndex().row()
        user_name_index = self.chatsModel.index(current_row,0)
        user_name_o = self.chatsModel.data(user_name_index)

        tip_index = self.chatsModel.index(current_row,3)
        tips_item = self.chatsModel.data(tip_index)
        if tips_item:
            self.chatsModel.setData(tip_index, "")
        head_tips_index = self.chatsModel.index(current_row,0)
        tips_item = self.chatsModel.data(head_tips_index)
        #if message_count:
        #    count = int(message_count)
        user_name = str(user_name_o.toString())
        if user_name.find("@@") >= 0:
            contact = self.get_member(user_name)
        else:
            contact = self.get_contact(user_name)
        self.current_chat_contact = contact
        dn = contact['RemarkName'] or contact['NickName']
        #if not dn:
        #    dn = contact['NickName']
        if user_name.find('@@') >= 0:
            self.currentChatUser.setText(("%s (%d)")%(unicode(dn),contact["MemberCount"]))
        else:
            self.currentChatUser.setText(unicode(dn))
        self.messages.setText('')
        msgss = self.msg_cache.get(user_name) or []
        if msgss:
            print("user_name %s,msgss size:%s"%(user_name,len(msgss)))
        #for (key,messages_list) in self.msg_cache.items():
        #for (key,messages_list) in msgss:
            #if user_name == key:
        for message in msgss:
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
                #break

    def showMembers(self):
        self.current_chat_user_click()
        
    def current_chat_user_click(self):
        memebers = [self.current_chat_contact]
        if self.current_chat_contact['UserName'].find('@@') >= 0:
            memebers = self.current_chat_contact["MemberList"]
        if self.memberListWidget:
            print("visible ddd%s:"+str(self.memberListWidget.isHidden()))
            if self.memberListWidget.isHidden():
                rect = self.geometry()
                #update memberlist
                self.memberListWidget.updatemembers(memebers)
                self.memberListWidget.resize(QSize(MemberListWidget.WIDTH,rect.height()+self.frameGeometry().height()-self.geometry().height()))
                self.memberListWidget.move(self.frameGeometry().x()+self.frameGeometry().width(), self.frameGeometry().y())
                self.memberListWidget.show()
            else:
                self.memberListWidget.hide()
        else:
            rect = self.geometry()
            print(rect.left(), rect.top())
            print(self.frameGeometry())
            print(rect.width(), rect.height())
            
            self.memberListWidget = MemberListWidget(memebers,self.wxapi.friend_list,self)
            self.memberListWidget.resize(QSize(MemberListWidget.WIDTH,rect.height()+self.frameGeometry().height()-self.geometry().height()))
            self.memberListWidget.move(self.frameGeometry().x()+self.frameGeometry().width(), self.frameGeometry().y())
            
            self.memberListWidget.membersChanged.connect(self.getSelectedUsers)
            self.memberListWidget.show()
            
    @pyqtSlot(str)
    def getSelectedUsers(self,users):
        '''
        #建群
        '''
        if not users:
            return
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
                self.wxapi.friend_list.append(new_contact)
                self.wxapi.webwx_get_head_img(new_contact["UserName"], new_contact["HeadImgUrl"])
                self.append_contact_row(new_contact,self.chatsModel,action="INSERT",row=0)
            
        
    def member_item_clicked(self):
        self.profileWidget.setVisible(True)
        self.chatAreaWidget.setVisible(False)
        self.label.setVisible(False)
        current_row =self.friendsWidget.currentIndex().row()
        user_name_index = self.friendsModel.index(current_row,0)
        user_name_o = self.friendsModel.data(user_name_index)
        user_name = user_name_o.toString()
        contact = self.get_member(user_name)
        if contact:
            user_icon = self.contact_head_home + contact['UserName'] + ".jpg"
            user_head_image = QtGui.QImage()
            if user_head_image.load(user_icon):
                self.avater_label.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(132, 132))
            else:
                if user_head_image.load(self.default_head_icon):
                    self.avater_label.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(132, 132))
            
            self.nickname_label.setText(unicode(contact['NickName']))
            self.signature_label.setText(unicode(contact['Signature']) if contact.has_key("Signature")  else "")
            self.remark_label.setText(unicode(contact['RemarkName']))
            self.province_label.setText(unicode(contact['RemarkName']))
        '''
        self.current_chat_contact = contact
        dn = contact['RemarkName'] or contact['NickName']
        if not dn:
            dn = contact['NickName']
        self.currentChatUser.setText(unicode(dn))
        self.messages.setText('')
        if self.msg_cache.has_key(user_name):
            messages_list = self.msg_cache[user_name]
            for message in messages_list:
                self.messages.append((message))
        '''
    def send_msg(self):
        '''
        #把消息發送出去
        '''
        msg_html = self.draft.toHtml()
        if not msg_html or len(msg_html) <= 0:
            return
        rr = re.search(r'<img src="([.*\S]*\.gif)"',msg_html,re.I)
        msgBody = ""
        if rr:
            pimages = self.emotioncode(msg_html)
            for pimage in pimages:
                p = pimage["p"]
                msgBody+=p
        else:
            msgBody = self.draft.toPlainText()
        #print("xxxx %s"%msgBody)
        #msg_text = str(self.draft.toPlainText())
        msgBody = unicode(msgBody)
        msg = Msg(1, msgBody, self.current_chat_contact['UserName'])
        response = self.wxapi.webwx_send_msg(msg)
        if not response or response is False:
            return False
        #if send success
        self.stick(select=True)
        #self.chatsWidget.selectRow(0)
        format_msg = self.msg_timestamp(self.wxapi.user['NickName'])
        self.messages.append(format_msg)
        msg_text = self.emotiondecode(msgBody) if rr else msgBody
        #msg_text = self.emotiondecode(msgBody)
        self.messages.append(unicode(msg_text))
        self.draft.setText('')
        #TODO FIX BUG
        if False:
            row_count = self.chatsModel.rowCount()
            find = False
            for row_number in range(row_count):
                user_name_index = self.chatsModel.index(row_number,0)
                user_name_obj = self.chatsModel.data(user_name_index)
                user_name = user_name_obj.toString()
                if user_name and user_name == self.current_chat_contact['UserName']:
                    find = True
                    tip_index = self.chatsModel.index(row_number,3)
                    tips_count_obj = self.chatsModel.data(tip_index)
                    if tips_count_obj:
                        tips_count = tips_count_obj.toInt()
                        if tips_count:
                            count = tips_count[0]
                            self.chatsModel.setData(tip_index, str(count+1))
                        else:
                            self.chatsModel.setData(tip_index, "1")
                    else:
                        count_tips_item = QtGui.QStandardItem("1")
                        self.chatsModel.setItem(row_number, 3, count_tips_item)
                    #提昇from_user_name在會話列表中的位置
                    #move this row to the top of the sessions
                    taked_row = self.chatsModel.takeRow(row_number)
                    self.chatsModel.insertRow(0 ,taked_row)
                    break;
            if find == False:
                cells = []
                # user name item
                user_name_item = QtGui.QStandardItem((user_name))
                cells.append(user_name_item)
                
                item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
                cells.append(item)
                
                dn = self.current_chat_contact['RemarkName'] or self.current_chat_contact['NickName']
                #if not dn:
                    #dn = self.current_chat_contact['NickName']
                # user remark or nick name
                remark_nick_name_item = QtGui.QStandardItem((dn))
                cells.append(remark_nick_name_item)
                
                count_tips_item = QtGui.QStandardItem("1")
                cells.append(count_tips_item)
                
                self.chatsModel.insertRow(0,cells)
    
    def upload_send_msg_image(self,contact,ffile):
        '''
        #把圖片發送出去
        '''
        upload_response = self.wxapi.webwx_upload_media(contact,ffile)
        json_upload_response = json.loads(upload_response)
        media_id = json_upload_response['MediaId']
        if self.isImage(ffile):
            msg = Msg(3, str(media_id), self.current_chat_contact['UserName'])
            send_response = self.wxapi.webwx_send_msg_img(msg)
        else:
            #parameter: appid,title,type=6,totallen,attachid(mediaid),fileext
            fileext = os.path.splitext(ffile)[1]
            if fileext and len(fileext) > 1 and fileext.startswith("."):
                fileext = fileext[1:(len(fileext))]
            content = "<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>%s</title><des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl><appattach><totallen>%d</totallen><attachid>%s</attachid><fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>"%(os.path.basename(ffile),os.path.getsize(ffile),media_id,fileext)
            msg = Msg(6, content, self.current_chat_contact['UserName'])
            send_response = self.wxapi.webwx_send_app_msg(msg)
        return send_response
        
    def stick(self,row=None,select=False):
        '''
        :param row the row which will be move to the top of the session table
        '''
        #提昇from_user_name在會話列表中的位置
        #move this row to the top of the session table
        if not row or row <= 0:
            row_count = self.chatsModel.rowCount()
            for _row in range(row_count):
                index = self.chatsModel.index(_row,0)
                user_name_o = self.chatsModel.data(index)
                user_name = user_name_o
                if user_name and user_name == self.current_chat_contact["UserName"]:
                    row = _row
                    break;
        if row > 1:
            taked_row = self.chatsModel.takeRow(row)
            self.chatsModel.insertRow(0 ,taked_row)
            if select:
                self.chatsWidget.selectRow(0)
        
    def get_user_display_name(self,msg):
        
        from_user_name = msg['FromUserName']
        
        if from_user_name == self.wxapi.user["UserName"]:
            from_user = self.wxapi.user
        else:
            from_user = self.get_contact(from_user_name)
        #如果為群，則消息來源顯示from_member_name
        from_user_display_name = from_member_name= None
        #如果是群消息
        msg_content = msg['Content']
        if from_user_name.find('@@') >= 0:
            print("get_user_display_name msg_content:%s"%msg_content)
            index = msg_content.find(":")
            
            if  msg_content.startswith("@") and index > 0:
                from_user_display_name = from_member_name = msg_content[0:index]
                msg_content = msg_content[index:len(msg_content)]
                
            members = from_user["MemberList"]
            for member in members:
                if from_member_name == member['UserName']:
                    from_user_display_name = member['RemarkName'] if member.has_key("RemarkName") else None or member['NickName'] if member.has_key("NickName") else None
                    if not from_user_display_name:
                        from_user_display_name = from_member_name
                    break
        else:
            from_user_display_name = from_user['RemarkName'] or from_user['NickName']
            #if not from_user_display_name:
                #from_user_display_name = from_user['NickName']
                
        if not from_user_display_name:
            from_user_display_name = from_user_name
        
        return from_user_display_name or from_user_name
    
    
    def msg_timestamp(self,userName):
        st = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        msg_timestamp = ('%s %s:') % (userName, st)
        return unicode(msg_timestamp)
    
    def default_msg_handler(self,msg):
        '''
        #默認的消息處理handler
        '''
        self.text_msg_handler(msg)
        
    def wxinitial_msg_handler(self,msg):
        '''
        #msg_type =51
        #微信初化消息處理handler，
        #我認為主要是初始化會話列表
        #用返回的數据更新會話列表
        '''
        statusNotifyUserName = msg["StatusNotifyUserName"]
        #
        #StatusNotifyCode = 2,4,5
        #4:初始化時所有的會話列表人員信息
        #2應該是新增會話，就是要把此人加入會話列表
        #5還不清楚
        #
        statusNotifyCode = msg["StatusNotifyCode"]
        if statusNotifyUserName:
            statusNotifyUserNames = statusNotifyUserName.split(",")
            lists = []
            for userName in statusNotifyUserNames:
                exist = False
                for tl in self.wxapi.chat_list:
                    if userName == tl["UserName"]:
                        exist = True
                        break
                if exist:
                    continue
                
                if userName.startswith("@@"):
                    #prepare arguments for batch_get_contact api
                    group = {}
                    group['UserName'] = userName
                    group['ChatRoomId'] = ''
                    lists.append(group)
            params = {
                'BaseRequest': self.wxapi.base_request,
                'Count': len(lists),
                'List': lists
            }
            #update member list and download head image
            batch_get_contact_response = self.batch_get_contact(data=params)
            for contact in batch_get_contact_response['ContactList']:
                user_name = contact['UserName']
                head_img_url = contact['HeadImgUrl']
                if not user_name or not head_img_url:
                    continue
                image = '%s/heads/contact/%s.jpg'%(self.app_home,user_name)
                if not os.path.exists(image):
                    self.wxapi.webwx_get_head_img(user_name,head_img_url)
                    
                for member in self.wxapi.friend_list:
                    exist = False
                    if contact["UserName"] == member["UserName"]:
                        exist = True
                        break
                if exist is False:
                    self.wxapi.friend_list.append(contact)
            logging.debug('statusNotifyCode:%s'%statusNotifyCode)
            if statusNotifyCode == 4:
                #update chat list
                tmp_list = self.wxapi.chat_list[:]
                for userName in statusNotifyUserNames:
                    exist = False
                    for tl in tmp_list:
                        if userName == tl["UserName"]:
                            exist = True
                            break
                    if exist:
                        continue
                    for member in self.wxapi.friend_list:
                        if userName == member["UserName"]:
                            self.wxapi.chat_list.append(member)
                            #self.append_contact_row(member,self.chatsModel)
                            break
            else:
                logging.warn('statusNotifyCode is %s not process'%statusNotifyCode)
    
    def voice_msg_handler(self,msg):
        '''
            #把語音消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name)
        '''
        #:如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        to_user_name = msg['ToUserName']
        if self.current_chat_contact and to_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(unicode("請在手機端收聽語音"))
        else:
            pass
    def video_msg_handler(self,msg):
        '''
            #把語音消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name)
        '''
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        to_user_name = msg['ToUserName']
        if self.current_chat_contact and to_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(unicode("請在手機端觀看視頻"))
        else:
            pass
        
    def text_msg_handler(self,msg):
        '''
        #:把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(msg)
        
            
        format_msg = self.msg_timestamp(from_user_display_name)
        '''
        #:如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        from_user_name = msg['FromUserName']
        user_name = None
        if from_user_name.find("@@") >= 0:
            user_name = from_user_name
        else:
            user_name = msg['ToUserName']
        if self.current_chat_contact and user_name == self.current_chat_contact['UserName']:
            msg_content = msg['Content']
            if from_user_name.find('@@') >= 0:
                index = msg_content.find(":")
                
                if msg_content.startswith("@") and index > 0:
                    msg_content = msg_content[index+1:]
                    if msg_content.startswith("<br/>"):
                        msg_content = msg_content.replace("<br/>","",1)
            msg_content = self.emotiondecode(msg_content)
            self.messages.append(format_msg)
            self.messages.append(unicode(msg_content))
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
        
    def image_msg_handler(self,msg):
        '''
        #把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        from_user_display_name = self.get_user_display_name(msg)
        to_user_name = msg['ToUserName']
        format_msg = self.msg_timestamp(from_user_display_name)
        msg_id = msg['MsgId']
        self.wxapi.webwx_get_msg_img(msg_id)
        '''
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and to_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            msg_img = ('<img src=%s/%s.jpg>'%(self.cache_image_home,msg_id))
            self.messages.append(msg_img)
        else:
            pass
    def sys_msg_handler(self,msg):
        '''
        #系統消息處理
        '''
        if not self.current_chat_contact:
            pass
        xml_content = msg['Content']
        if xml_content:
            xml_content = xml_content.replace("&gt;",">")
            xml_content = xml_content.replace("&lt;","<")
            xml_content = xml_content.replace("<br/>","")
        if msg["FromUserName"].find("@@") >=0:
            index = xml_content.find(":")
            if xml_content.startswith("@") and index > 0:
                xml_content = xml_content[index+1:len(msg)]
        doc = xml.dom.minidom.parseString(xml_content)
        replacemsg_nodes = doc.getElementsByTagName("replacemsg")
        #old_msgid
        #TODO 用old msg id 從歷史中刪去
        if replacemsg_nodes:
            replacemsg = str(replacemsg_nodes[0].firstChild.data)
            
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name)
        
        user_name = msg['ToUserName']
        msg_type = msg['MsgType']
        if msg_type == 10002:
            user_name = msg["FromUserName"]
        # 如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        if self.current_chat_contact and user_name == self.current_chat_contact['UserName']:
            self.messages.append((("%s\r\n%s")%(format_msg,unicode(replacemsg))))
        else:
            pass
        
    def app_msg_handler(self,msg):
        '''把應用消息加入到聊天記錄裏，應該指的是由其他應用分享的消息
        '''
        if not self.current_chat_contact:
            pass
        xmlContent = msg['Content']
        if xmlContent:
            xmlContent = xmlContent.replace("&gt;",">")
            xmlContent = xmlContent.replace("&lt;","<")
            xmlContent = xmlContent.replace("<br/>","")
        print("xmlContent %s"%xmlContent)
        if msg["FromUserName"].find("@@") >=0:
            index = xmlContent.find(":")
            if index > 0:
                xmlContent = xmlContent[index+1:len(msg)]
        
        #print("xml_content %s"%xmlContent)
        doc = xml.dom.minidom.parseString(xmlContent)
        title_nodes = doc.getElementsByTagName("title")
        desc_nodes = doc.getElementsByTagName("des")
        app_url_nodes = doc.getElementsByTagName("url")
        
        title = ""
        desc = ""
        app_url = ""
        if title_nodes and title_nodes[0] and title_nodes[0].firstChild:
            title = title_nodes[0].firstChild.data
        if desc_nodes and desc_nodes[0] and desc_nodes[0].firstChild:
            desc = desc_nodes[0].firstChild.data
        if app_url_nodes and app_url_nodes[0] and app_url_nodes[0].firstChild:
            app_url = app_url_nodes[0].firstChild.data
        
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name)
        
        '''
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        to_user_name = msg['ToUserName']
        if self.current_chat_contact and to_user_name == self.current_chat_contact['UserName']:
            self.messages.append(format_msg)
            self.messages.append(unicode(('%s %s %s')%(title,desc,app_url)))
        else:
            pass
        
    def put_msg_cache(self,msg):
        '''
        #用ToUserName做Key把消息存起來，同時把此人置頂
        '''   
        cache_key = None
        from_user_name = msg['FromUserName']
        msg_type = msg['MsgType']
        if from_user_name.find("@@") >= 0 or msg_type == 10002:
            cache_key = from_user_name
        else:
            cache_key = msg['ToUserName']
        row_count = self.chatsModel.rowCount()
        if row_count <= 0:
            self.new_msg_cache.append(msg)
            return False
        if self.msg_cache.has_key(cache_key):
            messages_list = self.msg_cache[cache_key]
        else:
            messages_list = []
        messages_list.append(msg)
        self.msg_cache[cache_key] = messages_list
        #TODO ADD TIPS
        '''
        #增加消息數量提示（提昇此人在會話列表中的位置）
        '''
        exist = False#此人是否在會話列表中
        for row in range(row_count):
            index = self.chatsModel.index(row,0)
            user_name_o = self.chatsModel.data(index)
            user_name = user_name_o
            #user_name = self.chatsModel.item(i,0).text()
            if user_name and user_name == cache_key:
                exist = True
                tip_index = self.chatsModel.index(row,3)
                tips_count_obj = self.chatsModel.data(tip_index)
                if tips_count_obj:
                    tips_count = tips_count_obj.toString()
                    if tips_count:
                        self.chatsModel.setData(tip_index, str(int(tips_count)+1))
                    else:
                        self.chatsModel.setData(tip_index, "1")
                else:
                    count_tips_item = QtGui.QStandardItem("1")
                    self.chatsModel.setItem(row, 3, count_tips_item)
                #提昇from_user_name在會話列表中的位置
                #move this row to the top of the sessions
                taked_row = self.chatsModel.takeRow(row)
                self.chatsModel.insertRow(0 ,taked_row)
                break;
        #have not received a message before（如果此人没有在會話列表中，則加入之）
        if not exist:
            contact = {}
            for member in self.wxapi.friend_list:
                if member['UserName'] == cache_key:
                    contact = member
                    break
            if not contact:
                logging.warn('the contact %s not found in friends'%cache_key)
                return False
            dn = contact['RemarkName'] or contact['NickName']
            #if not dn:
                #dn = contact['NickName']
            user_name = contact['UserName']
            cells = []
            # user name item
            user_name_item = QtGui.QStandardItem((user_name))
            cells.append(user_name_item)
            
            item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"),"")
            cells.append(item)
            
            # user remark or nick name
            remark_nick_name_item = QtGui.QStandardItem((dn))
            cells.append(remark_nick_name_item)
            
            count_tips_item = QtGui.QStandardItem("1")
            cells.append(count_tips_item)
            
            self.chatsModel.insertRow(0,cells)
    
    def msg_handle(self,msg):
        msg_type = msg['MsgType']
        print("msg_handle() will processing ,msgtype %s,msg body:%s"%(str(msg_type),str(msg)))
        if msg_type:
            if msg_type == 51:
                self.wxinitial_msg_handler(msg)
                return
            if msg_type == 2 or msg_type == 52:
                logging.warn('msg not process:')
                logging.warn('msg type %d'%msg_type)
                return
            user_name = msg['ToUserName']
            if user_name.startswith("@@") >= 0:
                #user_name = from_user_name
                user_name = msg['FromUserName']
            else:
                pass
            '''
            #没有選擇和誰對話或者此消息的發送人和當前的對話人不一致，則把消息存放在message_cache中;
            #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
            '''
            if (not self.current_chat_contact) or user_name != self.current_chat_contact['UserName']:
                self.put_msg_cache(msg)
            else:
                if msg_type == 1:
                    self.text_msg_handler(msg)
                elif msg_type == 3:
                    self.image_msg_handler(msg) 
                elif msg_type == 34:
                    self.voice_msg_handler(msg)
                elif msg_type == 47:
                    self.default_msg_handler(msg)
                elif msg_type == 49:
                    self.app_msg_handler(msg)
                elif msg_type == 10002:
                    self.sys_msg_handler(msg)
                else:
                    self.default_msg_handler(msg)
                    
    def webwx_sync_process(self, data):
        '''
        @param data
        MSTTYPE:
        MSGTYPE_TEXT: 1,文本消息
        MSGTYPE_IMAGE: 3,图片消息
        MSGTYPE_VOICE: 34,语音消息
        37,好友确认消息
        MSGTYPE_VIDEO: 43,
        MSGTYPE_MICROVIDEO: 62,
        MSGTYPE_EMOTICON: 47,
        MSGTYPE_APP: 49,
        MSGTYPE_VOIPMSG: 50,
        51,微信初始化消息
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
            self.msg_handle(msg)

    def select_emotion(self):
        emotionWidget = Emotion(self)
        cursor_point = QCursor.pos()
        #emotionWidget.move(cursor_point)
        emotionWidget.move(QPoint(cursor_point.x(),cursor_point.y()-Emotion.HEIGHT))
        emotionWidget.selectChanged.connect(self.get_select_emotion)
        emotionWidget.show()
        '''
        if QDialog.Accepted == emotionWidget.accept():
            selected_emotion = emotionWidget.get_selected_emotion()
            print("selected_emotion %s"%selected_emotion)
        '''
    @pyqtSlot(str)
    def get_select_emotion(self,emotion):
        cursor = self.draft.textCursor()
        imageFormat =QTextImageFormat();

        imageFormat.setName(os.path.join(Emotion.EMOTION_DIR,str(emotion)));
        cursor.insertImage(imageFormat)
        '''
        self.draft.moveCursor(QTextCursor.End)
        self.draft.append("<img src=%s>"%(os.path.join(Emotion.EMOTION_DIR,str(emotion))))
        '''
        
    def select_document(self):
        fileDialog = QFileDialog(self)
        if fileDialog.exec_():
            selectedFiles = fileDialog.selectedFiles()
            for ffile in selectedFiles:
                ffile = str(ffile)
                send_response = self.upload_send_msg_image(self.current_chat_contact,ffile)
                send_response_dict = json.loads(send_response)
                
                msg_id = send_response_dict["MsgID"]
                #send success append the image to history;failed append to draft 
                if msg_id:
                    self.stick(select=True)
                    self.wxapi.webwx_get_msg_img(msg_id)
                    #st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
                    #format_msg = ('(%s) %s:') % (st, self.wxapi.user['NickName'])
                    format_msg = self.msg_timestamp(self.wxapi.user['NickName'])
                    self.messages.append(format_msg)
                    if self.isImage(ffile):
                        msg_img = ('<img src=%s/%s.jpg>'%(self.cache_image_home,msg_id))
                    else:
                        msg_img = ffile
                    self.messages.append(msg_img)
                else:
                    #fileName=QtCore.QString.fromUtf8(fileName)
                    if self.isImage(ffile):
                        self.draft.append("<img src=%s width=80 height=80>"%(ffile))
                    else:
                        print(ffile)
                    
    def keyPressEvent(self,event):
        print("keyPressEvent")
        
    def synccheck(self,loop=True):
        while (True):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            print('push#synccheck %s' %(st))
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
            if loop is False:
                break
            sleep(3)
            
class MemberListWidget(QtGui.QDialog):
    WIDTH = 300
    membersChanged = pyqtSignal(str)
    
    def __init__(self,member_list,contacts,parent = None):
        super(MemberListWidget,self).__init__(parent)
        self.setMinimumSize(200, 600)
        self.user_home = os.path.expanduser('~')
        #self.setAcceptDrops(True)
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = './resource/images/default.png'
        self.default_member_icon = './resource/images/webwxgeticon.png'
        self.members = member_list
        self.contacts = contacts
        #self.setWindowFlags(Qt.FramelessWindowHint)#|Qt.Popup
        self.membersTable = QTableView()
        self.membersTable.verticalHeader().setDefaultSectionSize(60)
        self.membersTable.verticalHeader().setVisible(False)
        self.membersTable.horizontalHeader().setDefaultSectionSize(60)
        self.membersTable.horizontalHeader().setVisible(False)
        #More
        self.more = QPushButton(unicode('顯示更多'))
        self.verticalSpacer = QSpacerItem(20, 20, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        
        self.membersTableModel = QStandardItemModel(0,4)
        self.initinal_member_list_widget(self.members)
        mainLayout=QVBoxLayout()
        mainLayout.addWidget(self.membersTable)
        mainLayout.addWidget(self.more)
        mainLayout.addItem(self.verticalSpacer)
        self.setLayout(mainLayout)
        
    def updatemembers(self,members):
        self.members = members
        self.membersTableModel.removeRows(0, self.membersTableModel.rowCount())
        self.append_row(self.members, self.membersTableModel)
        
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
        self.memberListWindow.membersConfirmed.connect(self.route)
        self.memberListWindow.show()
    
    @pyqtSlot(str)
    def route(self,objectt):
        self.membersChanged.emit(objectt)
        
    def append_row(self,members,data_model):
        ###############
        cells = []
        item = QtGui.QStandardItem(("+"))
        cells.append(item)
        for member in members[0:3]:
            user_head_icon = self.contact_head_home + member['UserName']+".jpg"
            if not os.path.exists(user_head_icon):
                user_head_icon = self.default_member_icon
            dn = member['DisplayName'] or member['NickName']
            if not dn:
                dn = member['NickName']
            item = QtGui.QStandardItem(QIcon(user_head_icon),unicode(dn))
            cells.append(item)
        data_model.appendRow(cells)
        i = 3
        members_len = len(members)
        if members_len > 19:
            members_len = 19
        while i < members_len:
            cells = []
            for member in members[i:i+4]:
                user_head_icon = self.contact_head_home + member['UserName']+".jpg"
                if not os.path.exists(user_head_icon):
                    user_head_icon = self.default_member_icon
                dn = member['DisplayName'] or member['NickName']
                if not dn:
                    dn = member['NickName']
                item = QtGui.QStandardItem(QIcon(user_head_icon),unicode(dn))
                cells.append(item)
            i = i + 4
            data_model.appendRow(cells)
    
class ContactListWindow(QtGui.QDialog):
    WIDTH = 600
    membersConfirmed = pyqtSignal(str)
    
    def __init__(self,member_list,parent = None):
        super(ContactListWindow,self).__init__(parent)
        self.setModal(True)
        self.user_home = os.path.expanduser('~')
        self.app_home = self.user_home + '/.wechat/'
        self.head_home = ("%s/heads"%(self.app_home))
        self.cache_home = ("%s/cache/"%(self.app_home))
        self.cache_image_home = "%s/image/"%(self.cache_home)
        self.contact_head_home = ("%s/contact/"%(self.head_home))
        self.default_head_icon = './resource/images/default.png'
        self.members = member_list
        self.membersTable = QTableView()
        self.membersTable.horizontalHeader().setStretchLastSection(True)
        self.membersTable.verticalHeader().setDefaultSectionSize(60)
        #self.membersTable.horizontalHeader().setDefaultSectionSize(60)
        self.membersTable.setColumnWidth(0, 10);
        self.membersTable.setColumnWidth(1, 60);
        self.membersTable.verticalHeader().setVisible(False)
        self.membersTable.horizontalHeader().setVisible(False)
        #confirm
        self.confirm = QPushButton(unicode("確定"),self)
        self.membersTableModel = QStandardItemModel(0,2)
        self.membersTableModel.itemChanged.connect(self.itemChanged)
        self.initinal_member_list_widget()
        mainLayout=QVBoxLayout()
        mainLayout.addWidget(self.membersTable)
        mainLayout.addWidget(self.confirm)
        self.setLayout(mainLayout)
        #self.membersTable.clicked.connect(self.contact_item_clicked)
        self.confirm.clicked.connect(self.do_confirm)
        self.selectedRowCount = 0
        
    def itemChanged(self,item):
        if item.checkState() == Qt.Checked:
            self.selectedRowCount += 1
        else:
            self.selectedRowCount -= 1
            
        if self.selectedRowCount > 0:
            self.confirm.setText(unicode("確定(%d)"%(self.selectedRowCount)))
        else:
            self.confirm.setText(unicode("確定"))
            
    def initinal_member_list_widget(self):
        self.append_row(self.members, self.membersTableModel)
        self.membersTable.setModel(self.membersTableModel)
        self.membersTable.setIconSize(QSize(40,40))
        
    def append_row(self,members,data_model):
        for (i,member) in enumerate(members):
            cells = []
            user_name = member['UserName']
            user_name_cell = QtGui.QStandardItem(user_name)
            user_name_cell.setCheckable(True)
            cells.append(user_name_cell)
            
            user_avatar = self.contact_head_home + member['UserName']+".jpg"
            if not os.path.exists(user_avatar):
                user_avatar = self.default_head_icon
            dn = member['DisplayName'] or member['NickName']
            if not dn:
                dn = member['NickName']
            item = QtGui.QStandardItem(QIcon(user_avatar),unicode(dn))
            cells.append(item)
            data_model.appendRow(cells)
    
    def do_confirm(self):
        rowCount = self.membersTableModel.rowCount()        
        selected_user_names = ""
        for row in range(rowCount):
            item = self.membersTableModel.item(row,0)
            if item.checkState() == Qt.Checked:
                index = self.membersTableModel.index(row,0)
                user_name_obj = self.membersTableModel.data(index)
                if user_name_obj:
                    user_name = user_name_obj
                    user = {}
                    user['UserName']=str(user_name)
                    selected_user_names=selected_user_names+(user_name)
                    selected_user_names=selected_user_names+(";")
                
        if len(selected_user_names) > 0:
            dictt = {}
            dictt['UserNames']=selected_user_names
            self.membersConfirmed.emit(selected_user_names)
        
            self.close()