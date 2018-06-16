#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年3月25日

@author: zhaohongxing
'''
from config import WechatConfig

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
from com.ox11.wechat.ui.emotion import Emotion
from com.ox11.wechat.ui.about import About
from com.ox11.wechat import property
from com.ox11.wechat.ui.MemberListWidget import MemberListWidget
from com.ox11.wechat.ui.delegate.labeldelegate import LabelDelegate
from msg import Msg

import xml.dom.minidom
import json
import logging

from PyQt4.Qt import QIcon, QCursor, QTextImageFormat
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QStandardItemModel, QFileDialog, QMenu, QAction,\
    QVBoxLayout, QDialog, QLabel
from PyQt4.QtCore import QSize, pyqtSlot, pyqtSignal, QPoint, QUrl

'''
1.ContactFlag:
    1是好友，值为3是公众号
2."UserName" 用户名称:
    一个"@"为好友，两个"@"为群组
3."Sex": 
    性别，0-未设置（公众号、保密），1-男，2-女
4."StarFriend": 是否为星标朋友  0-否  1-是
'''

def _decode_data(data):
    """
    @brief      decode array or dict to utf-8
    @param      data   array or dict
    @return     utf-8
    """
    if isinstance(data, dict):
        rv = {}
        for key, value in data.iteritems():
            if isinstance(key, unicode):
                key = key.encode('utf-8')
            rv[key] = _decode_data(value)
        return rv
    elif isinstance(data, list):
        rv = []
        for item in data:
            item = _decode_data(item)
            rv.append(item)
        return rv
    elif isinstance(data, unicode):
        return data.encode('utf-8')
    else:
        return data
reload(sys)

sys.setdefaultencoding('utf-8')

qtCreatorFile = "resource/ui/wechat-0.5.ui"


WeChatWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChat(QtGui.QMainWindow, WeChatWindow):

    I18N = "resource/i18n/resource.properties"
    
    EMOTION_DIR = "./resource/expression"
    
    MESSAGE_TEMPLATE = "./resource/messages.html"
    
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
    messageReceived = pyqtSignal(str)
    
    def __init__(self,wechatweb):
        QtGui.QMainWindow.__init__(self)
        WeChatWindow.__init__(self)
        self.config = WechatConfig()
        logging.basicConfig(filename='./wechat.log',level=logging.DEBUG,format=WeChat.LOG_FORMAT)
        self.setAcceptDrops(True)
        self.user_home = os.path.expanduser('~')
        self.current_chat_contact = None
        self.messages_pool = {}
        #没有來得及處理的新消息,主要用於存放UI未初始化完時收到消息，然後等初始結束處理
        self.blocked_messages_pool = []
        self.prepare4Environment()
        self.wechatweb = wechatweb
        self.setupUi(self)
        self.setWindowIcon(QIcon("resource/icons/hicolor/32x32/apps/wechat.png"))
        self.chatsModel = QStandardItemModel(0,4)
        self.friendsModel = QStandardItemModel(0,3)
        self.publicModel = QStandardItemModel()
        #connect the slot before #wxinitial()
        self.messageReceived.connect(self.webwx_sync_process)
        #initial messages
        #should initial before chat item click
        ap = os.path.abspath(WeChat.MESSAGE_TEMPLATE)
        self.messages.load(QUrl.fromLocalFile(ap))
        self.messages.loadFinished.connect(self.loadFinished)
        #after initial model,do login
        self.wechatweb.login()
        
        self.wxinitial()
        #self.synct = WeChatSync(self.wechatweb)
        #self.synct.start()
        timer = threading.Timer(5, self.synccheck)
        timer.setDaemon(True)
        timer.start()
        
        self.memberListWidget = None
        self.showImageDialog = None
        self.friendsWidget.setVisible(False)
        self.publicWidget.setVisible(False)
        self.profileWidget.setVisible(False)
        self.init_chat_contacts()
        self.init_friends()
        self.init_public()
        self.emotionscodeinitial()
        self.initialed.connect(self.process_blocked_messages)
        
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
        #
        self.initialed.emit()
    
    @pyqtSlot()
    def loadFinished(self):
        print('loadFinished')
        self.messages.page().mainFrame().addToJavaScriptWindowObject("Wechat", self)
        
    @pyqtSlot(str)
    def showImage(self,image):
        if self.showImageDialog:
            print(image)
            self.showImageDialog.show()
        else:
            self.showImageDialog = QDialog(self)
            #self.showImageDialog.setModal(True)
            mainLayout = QVBoxLayout()
            image_label = QLabel()
            s_image = QtGui.QImage()
            user_icon = self.config.getContactHeadHome() + self.wechatweb.getUser()['UserName'] + ".jpg"
            if s_image.load(user_icon):
                image_label.setPixmap(QtGui.QPixmap.fromImage(s_image))
            mainLayout.addWidget(image_label)
            self.showImageDialog.setLayout(mainLayout)
            self.showImageDialog.show()
        
    def process_blocked_messages(self):
        logging.debug('start process blocked_messages_pool')
        for message in self.blocked_messages_pool:
            self.msg_handle(message)
    
    def wxinitial(self):
        wx_init_response = self.wechatweb.webwx_init()
        #self.wechatweb.webwxstatusnotify()
        self.setupwxuser()
        
        #do downlaod icon
        self.wechatweb.webwx_get_contact()
        self.synccheck(loop=False)
        #TODO download the head image or icon of contact
        #fetch the icon or head image that init api response
        groups = []
        for contact in wx_init_response['ContactList']:
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            if self.isChatRoom(user_name):
                #prepare arguments for batch_get_contact
                group = {}
                group['UserName'] = contact['UserName']
                group['ChatRoomId'] = ''
                groups.append(group)
                #doanload head image
                self.wechatweb.webwx_get_head_img(user_name,head_img_url)
            elif user_name.startswith('@'):
                self.wechatweb.webwx_get_icon(user_name,head_img_url)
            else:
                pass
        params = {
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
        params = data
        response = self.wechatweb.webwx_batch_get_contact(params)
        '''
        session_response中的contact里面有群成员，所以更新chat_contact
        if response['Count'] and response['Count'] > 0:
            session_list = response['ContactList']
            for x in session_list:
                for i,ss in enumerate(self.wechatweb.getChatContacts()):
                    if ss["UserName"] == x["UserName"]:
                        self.wechatweb.update_chat_contact(i,x)
                        break
        '''
        for contact in response['ContactList']:
            user_name = contact['UserName']
            head_img_url = contact['HeadImgUrl']
            if not user_name or not head_img_url:
                continue
            image = '%s\heads\contact\%s.jpg'%(self.config.getAppHome(),user_name)
            #下載聯天室圖像
            if not os.path.exists(image):
                self.wechatweb.webwx_get_head_img(user_name,head_img_url)
            else:
                logging.warn("%s is already exist"%image)
            
            #如果群没有名字，则取前2个成员名字的组合作为群名称
            if not contact["NickName"] and not contact["DisplayName"]:
                t_names = []
                for _member in contact["MemberList"][:2]:
                    t_names.append(_member['DisplayName'] or _member['NickName'])
                        
                contact["DisplayName"] = "、".join(t_names)
            #把聯天室加入聯系人列表對象
            for member in self.wechatweb.getFriends():
                exist = False
                if contact["UserName"] == member["UserName"]:
                    exist = True
                    break
            if exist is False:
                self.wechatweb.appendFriend(contact)
            #更新chat_contact,以使其群成员有数据
            for i,chat_contact in enumerate(self.wechatweb.getChatContacts()):
                if contact["UserName"] == chat_contact["UserName"]:
                    self.wechatweb.update_chat_contact(i,contact)
                    break
        return response
    
    def prepare4Environment(self):
        if os.path.exists(self.config.getAppHome()):
            self.__remove()
        else:
            os.makedirs(self.config.getAppHome())
            
        if os.path.exists(self.config.getContactHeadHome()):
            self.__remove()
        else:
            os.makedirs(self.config.getContactHeadHome())
            
        if os.path.exists(self.config.getCacheHome()):
            pass
        else:
            os.makedirs(self.config.getCacheHome())
        
        if os.path.exists(self.config.getHeadHome()):
            pass
        else:
            os.makedirs(self.config.getHeadHome())
            
        if os.path.exists(self.config.getCacheImageHome()):
            pass
        else:
            os.makedirs(self.config.getCacheImageHome())
            
    def __remove(self):
        '''
        #删除下载的头像文件
        '''
        for i in os.listdir(self.config.getContactHeadHome()):
            head_icon = os.path.join(self.config.getContactHeadHome(),i)
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
                image.load(self.config.getAppHome())

    def setupwxuser(self):
        user = self.wechatweb.getUser()
        nickName = user['NickName']
        self.userNameLabel.setText(unicode(nickName))
        user_icon = self.config.getContactHeadHome() + user['UserName'] + ".jpg"
        user_head_image = QtGui.QImage()
        if user_head_image.load(user_icon):
            self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))
        else:
            if user_head_image.load(self.config.getDefaultIcon()):
                self.headImageLabel.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(40, 40))

    def code_emotion(self,msg):
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
                        #print('[%s]'%((code_emotion)))
                        pcode = p.replace(imagemark,'[%s]'%(unicode(emotioncode)))
                        #print("p coded:%s"%pcode)
                        pimage["p"]=pcode
                        break
            pimage["images"]=images
            pimages.append(pimage)
        return pimages
    
    def decode_emotion(self,msg):
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
        
    def append_chat_contact(self,chat_contact,action="APPEND",row=None):
        '''
        :param action APPEND OR INSERT,APPEND value is default
        '''
        ###############
        cells = []
        # user name item
        user_name = chat_contact['UserName']
        user_name_item = QtGui.QStandardItem(unicode(user_name))
        cells.append(user_name_item)
        
        user_head_icon = self.config.getContactHeadHome() + user_name+".jpg"
        item = QtGui.QStandardItem(QIcon(user_head_icon),"")
        cells.append(item)
        
        dn = chat_contact['DisplayName'] or chat_contact['RemarkName'] or chat_contact['NickName']
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
        
        user_head_icon = "%s/%s.jpg"%(self.config.getContactHeadHome(), user_name)
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
        
    def messages_clear(self):
        #ap = os.path.abspath(WeChat.MESSAGE_TEMPLATE)
        #self.messages.load(QUrl.fromLocalFile(ap))
        self.messages.page().mainFrame().evaluateJavaScript("clearr();")
        
    def init_chat_contacts(self):
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
        for chat_contact in self.wechatweb.getChatContacts():
            self.append_chat_contact(chat_contact)
            
        '''
        for session in sorted([x for x in self.wechatweb.friend_list if x["AttrStatus"] and x["AttrStatus"] > 0],key=lambda ct: ct["AttrStatus"],reverse=True):
            exist = False
            for contact in self.wechatweb.chat_list:
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
        for member in self.wechatweb.getFriends():
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
        for member in self.wechatweb.getChatContacts():
            if user_name == member['UserName']:
                return member
            
        for member in self.wechatweb.getFriends():
            if user_name == member['UserName']:
                return member
            
    def chat_item_clicked(self):
        if self.chatAreaWidget.isHidden():
            self.chatAreaWidget.setVisible(True)
            self.label.setVisible(False)
            
        if self.current_chat_contact:
            self.messages_clear()
        current_row = self.chatsWidget.currentIndex().row()
        user_name_cell_index = self.chatsModel.index(current_row,0)
        user_name_cell = self.chatsModel.data(user_name_cell_index)

        tip_index = self.chatsModel.index(current_row,3)
        tips_item = self.chatsModel.data(tip_index)
        if tips_item:
            self.chatsModel.setData(tip_index, "")
        head_tips_index = self.chatsModel.index(current_row,0)
        tips_item = self.chatsModel.data(head_tips_index)
        #if message_count:
        #    count = int(message_count)
        user_name = str(user_name_cell.toString())
        print("current click user is %s"%user_name)
        if self.isChatRoom(user_name):
            contact = self.get_member(user_name)
        else:
            contact = self.get_contact(user_name)
        self.current_chat_contact = contact
        dn = contact['DisplayName'] or contact['RemarkName'] or contact['NickName']
        #if not dn:
        #    dn = contact['NickName']
        if self.isChatRoom(user_name):
            self.currentChatUser.setText(("%s (%d)")%(unicode(dn),contact["MemberCount"]))
        else:
            self.currentChatUser.setText(unicode(dn))
        #self.messages_clear()
        #self.messages.setText('')
        self.draft.setText('')
        cached_messages = self.messages_pool.get(user_name) or []
        #for (key,messages_list) in self.msg_cache.items():
        #for (key,messages_list) in msgss:
            #if user_name == key:
        for message in cached_messages:
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
                elif msg_type == 10000:
                    self.default_msg_handler(message)
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
            
            self.memberListWidget = MemberListWidget(memebers,self.wechatweb.getFriends(),self)
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
        
        response_data = self.wechatweb.webwx_create_chatroom(member_list)
        print("webwx_create_chatroom response:%s"%response_data)
        data_dict = json.loads(response_data)
        if data_dict["BaseResponse"]["Ret"] == 0:
            chat_room_name = data_dict["ChatRoomName"]
            data = {
                'Count': 1,
                'List': [{"UserName":chat_room_name,"ChatRoomId":""}]
            }
            batch_response = self.wechatweb.webwx_batch_get_contact(data)
            if batch_response['Count'] and batch_response['Count'] > 0:
                new_contact = batch_response['ContactList'][0]
                remark_name = ("%s,%s,%s")%(self.wechatweb.getUser()["NickName"],self.current_chat_contact["NickName"],"")
                new_contact["RemarkName"]=remark_name
                self.wechatweb.appendFriend(new_contact)
                self.wechatweb.webwx_get_head_img(new_contact["UserName"], new_contact["HeadImgUrl"])
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
            user_icon = self.config.getContactHeadHome() + contact['UserName'] + ".jpg"
            user_head_image = QtGui.QImage()
            if user_head_image.load(user_icon):
                self.avater_label.setPixmap(QtGui.QPixmap.fromImage(user_head_image).scaled(132, 132))
            else:
                if user_head_image.load(self.config.getDefaultIcon()):
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
    def make_message(self,user_name,msg_body):
        '''MSG TEMPLATE
        {
            id:'',
            user:{
                head_class='',
                head_img = '<img src=xx.jpg/>'
            },
            body:{
                content_class:'',
                content:''
            }
        }
        '''
        """
        _msg = 
           {
            id:'%s',
            user:{
               head_class='%s',
               head_img = '%s'
            },
            body:{
               content_class:'%s',
               content:'%s'
            }
        } %(
            '1',
            ("divMyHead" if self.wechatweb.user["UserName"] == user_name else "divotherhead"),
            "<img src=%s.jpg/>"%(self.config.getContactHeadHome() + user_name),
            ("triangle-right right" if self.wechatweb.user["UserName"] == user_name else "triangle-left left"),
            unicode(msg_body)
        )
        """
        user = self.wechatweb.getUser()
        _msg = {}
        _msg['id'] = ""
        _user = {}
        _user['head_class']=("divMyHead" if user["UserName"] == user_name else "divotherhead")
        _user['head_img']="%s.jpg"%(self.config.getContactHeadHome() + user_name)
        _msg['user']=_user
        _body = {}
        _body['content_class']= ("triangle-right right" if user["UserName"] == user_name else "triangle-left left")
        _body['content'] = unicode(msg_body)
        _msg['body']=_body

        return _msg

    def send_msg(self):
        '''
        #把消息發送出去
        '''
        msg_html = self.draft.toHtml()
        rr = re.search(r'<img src="([.*\S]*\.gif)"',msg_html,re.I)
        msg_body = ""
        if rr:
            pimages = self.code_emotion(msg_html)
            for pimage in pimages:
                p = pimage["p"]
                msg_body+=p
        else:
            msg_body = self.draft.toPlainText()
        #print("xxxx %s"%msgBody)
        #msg_text = str(self.draft.toPlainText())
        if not msg_body or len(msg_body) <= 0:
            return 
        msg_body = unicode(msg_body)
        msg = Msg(1, msg_body, self.current_chat_contact['UserName'])
        response = self.wechatweb.webwx_send_msg(msg)
        if not response or response is False:
            return False
        #if send success
        self.stick(select=True)
        #self.chatsWidget.selectRow(0)
        #format_msg = self.msg_timestamp(self.wechatweb.user['NickName'])
        #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%msgBody)
        #TODO append msg
        #self.messages.append(format_msg)
        msg_body = msg_body.replace("'", "\'")
        msg_body = msg_body.replace('"', '\"')
        msg_decode_body = self.decode_emotion(msg_body) if rr else msg_body
        #msg_text = self.decode_emotion(msgBody)
        #self.messages.append(unicode(msg_text))
        _msg = self.make_message(self.current_chat_contact['UserName'],msg_decode_body)
        script = "nappend('%s','%s','%s','%s','%s');"%(_msg['id'],_msg['user']['head_class'],_msg['user']['head_img'],_msg['body']['content_class'],_msg['body']['content'])
        print(script)
        self.messages.page().mainFrame().evaluateJavaScript(script)
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
        upload_response = self.wechatweb.webwx_upload_media(contact,ffile)
        json_upload_response = json.loads(upload_response)
        media_id = json_upload_response['MediaId']
        if self.isImage(ffile):
            msg = Msg(3, str(media_id), self.current_chat_contact['UserName'])
            send_response = self.wechatweb.webwx_send_msg_img(msg)
        else:
            #parameter: appid,title,type=6,totallen,attachid(mediaid),fileext
            fileext = os.path.splitext(ffile)[1]
            if fileext and len(fileext) > 1 and fileext.startswith("."):
                fileext = fileext[1:(len(fileext))]
            content = "<appmsg appid='wxeb7ec651dd0aefa9' sdkver=''><title>%s</title><des></des><action></action><type>6</type><content></content><url></url><lowurl></lowurl><appattach><totallen>%d</totallen><attachid>%s</attachid><fileext>%s</fileext></appattach><extinfo></extinfo></appmsg>"%(os.path.basename(ffile),os.path.getsize(ffile),media_id,fileext)
            msg = Msg(6, content, self.current_chat_contact['UserName'])
            send_response = self.wechatweb.webwx_send_app_msg(msg)
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
    
    def isChatRoom(self,user):
        '''
        :parameter user.the id of user
        '''
        if user:
            return user.startswith('@@')
        else:
            return False
        
    def get_user_display_name(self,message):
        
        from_user_name = message['FromUserName']
        user = self.wechatweb.getUser()
        #如果和當前登陸人是同一個人
        if from_user_name == user["UserName"]:
            from_user = user
        else:
            from_user = self.get_contact(from_user_name)
        #如果為群，則消息來源顯示from_member_name
        #如果是群消息
        from_user_display_name = from_member_name= None
        content = message['Content']
        if self.isChatRoom(from_user_name):
            contents = content.split(":<br/>")
            from_user_display_name = from_member_name = contents[0]
                
            members = from_user["MemberList"]
            for member in members:
                if from_member_name == member['UserName']:
                    from_user_display_name = member['NickName'] or member['DisplayName'] or from_member_name
                    break
        else:
            from_user_display_name = from_user['RemarkName'] or from_user['NickName']
                
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
        
    def wxinitial_msg_handler(self,message):
        '''
        #msg_type =51
        #微信初化消息處理handler，
        #我認為主要是初始化會話列表
        #用返回的數据更新會話列表
        '''
        statusNotifyUserName = message["StatusNotifyUserName"]
        #
        #StatusNotifyCode = 2,4,5
        #4:初始化時所有的會話列表人員信息
        #2應該是新增會話，就是要把此人加入會話列表
        #5還不清楚
        #
        statusNotifyCode = message["StatusNotifyCode"]
        if statusNotifyUserName:
            statusNotifyUserNames = statusNotifyUserName.split(",")
            lists = []
            for userName in statusNotifyUserNames:
                exist = False
                for tl in self.wechatweb.getChatContacts():
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
                'Count': len(lists),
                'List': lists
            }
            #update member list and download head image
            #拉取聯天室成員列表
            self.batch_get_contact(data=params)
            
            logging.debug('statusNotifyCode:%s'%statusNotifyCode)
            if statusNotifyCode == 4:
                #update chat list
                tmp_list = self.wechatweb.getChatContacts()[:]
                for userName in statusNotifyUserNames:
                    exist = False
                    for tl in tmp_list:
                        if userName == tl["UserName"]:
                            exist = True
                            break
                    if exist:
                        continue
                    for member in self.wechatweb.getFriends():
                        if userName == member["UserName"]:
                            self.wechatweb.appendChatContact(member)
                            #self.append_contact_row(member,self.chatsModel)
                            break
            else:
                logging.warn('statusNotifyCode is %s not process'%statusNotifyCode)
                logging.warn('message body is %s '%message)
    
    def voice_msg_handler(self,msg):
        '''
            #把語音消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(msg)
        #format_msg = self.msg_timestamp(from_user_display_name)
        '''
        #:如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        from_user_name = msg['FromUserName']
        if from_user_name == self.wechatweb.getUser()['UserName']:
            from_user_name = msg['ToUserName']
        
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            #self.messages.append(format_msg)
            #self.messages.append(unicode("請在手機端收聽語音"))
            
            _msg = self.make_message(from_user_name,unicode("請在手機端收聽語音"))
            script = "nappend('%s','%s','%s','%s','%s');"%(_msg['id'],_msg['user']['head_class'],_msg['user']['head_img'],_msg['body']['content_class'],_msg['body']['content'])
            self.messages.page().mainFrame().evaluateJavaScript(script)
            #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode("請在手機端收聽語音"))
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
        from_user_name = msg['FromUserName']
        if from_user_name == self.wechatweb.getUser()['UserName']:
            from_user_name = msg['ToUserName']
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            #self.messages.append(format_msg)
            #self.messages.append(unicode("請在手機端觀看視頻"))
            _msg = self.make_message(msg["UserName"],unicode("請在手機端觀看視頻"))
            script = "nappend('%s','%s','%s','%s','%s');"%(_msg['id'],_msg['user']['head_class'],_msg['user']['head_img'],_msg['body']['content_class'],_msg['body']['content'])
            self.messages.page().mainFrame().evaluateJavaScript(script)
            #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode())
        else:
            pass
        
    def text_msg_handler(self,message):
        '''
        #:把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        
        from_user_display_name = self.get_user_display_name(message)
        
        format_msg = self.msg_timestamp(from_user_display_name)
        '''
        #:如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        from_user_name = message['FromUserName']
        if from_user_name == self.wechatweb.getUser()['UserName']:
            from_user_name = message['ToUserName']
            
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            content = message['Content']
            if self.isChatRoom(from_user_name):
                if content.startswith("@"):
                    contents = content.split(":<br/>")
                    content = contents[1]
            content = self.decode_emotion(content)
            #self.messages.append(format_msg)
            #self.messages.append(unicode(msg_content))
        
            _msg = self.make_message(from_user_name,unicode(content))
            script = "nappend('%s','%s','%s','%s','%s');"%(_msg['id'],_msg['user']['head_class'],_msg['user']['head_img'],_msg['body']['content_class'],_msg['body']['content'])
            self.messages.page().mainFrame().evaluateJavaScript(script)
            #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode(msg_content))
        else:
            pass
        
    def download_msg_img(self,msg_id):
        data = self.wechatweb.webwx_get_msg_img(msg_id)
        if not data:
            return False
        img_cache_folder = ('%s/cache/img/'%(self.config.getAppHome()))
        msg_img = img_cache_folder+msg_id+'.jpg'
        with open(msg_img, 'wb') as image:
            image.write(data)
        return True
        
    def image_msg_handler(self,message):
        '''
        #把文本消息加入到聊天記錄裏
        '''
        if not self.current_chat_contact:
            pass
        from_user_display_name = self.get_user_display_name(message)
        from_user_name = message['FromUserName']
        if from_user_name == self.wechatweb.getUser()['UserName']:
            from_user_name = message['ToUserName']
        format_msg = self.msg_timestamp(from_user_display_name)
        msg_id = message['MsgId']
        self.wechatweb.webwx_get_msg_img(msg_id)
        '''
        #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        '''
        if self.current_chat_contact and from_user_name == self.current_chat_contact['UserName']:
            #self.messages.append(format_msg)
            msg_img = ('%s/%s.jpg'%(self.config.getCacheImageHome(),msg_id))
            #self.messages.append(msg_img)
            self.messages.page().mainFrame().evaluateJavaScript("appendImage('%s');"%unicode(msg_img))
        else:
            pass
    def sys_msg_handler(self,msg):
        '''
        #系統消息處理
        '''
        if not self.current_chat_contact:
            pass
            
        from_user_display_name = self.get_user_display_name(msg)
        format_msg = self.msg_timestamp(from_user_display_name)
        
        user_name = msg['FromUserName']
        if user_name == self.wechatweb.getUser()['UserName']:
            user_name = msg['ToUserName']
        msg_type = msg['MsgType']
        if msg_type == 10002:
            user_name = msg["FromUserName"]
            
        xml_content = msg['Content']
        if xml_content:
            xml_content = xml_content.replace("&gt;",">")
            xml_content = xml_content.replace("&lt;","<")
            xml_content = xml_content.replace("<br/>","")
        if self.isChatRoom(user_name):
            xml_contents = xml_content.split(":<br/>")
            xml_content = xml_contents[1]
        print('xml_content %s'%xml_content)
        doc = xml.dom.minidom.parseString(xml_content)
        replacemsg_nodes = doc.getElementsByTagName("replacemsg")
        #old_msgid
        #TODO 用old msg id 從歷史中刪去
        if replacemsg_nodes:
            replacemsg = str(replacemsg_nodes[0].firstChild.data)
        # 如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
        if self.current_chat_contact and user_name == self.current_chat_contact['UserName']:
            new_msg = "%s\r\n%s"%(format_msg,unicode(replacemsg))
            #self.messages.append(new_msg)
            _msg = self.make_message(msg["UserName"],unicode(new_msg))
            self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%(json.dumps(_msg)))
            #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode(new_msg))
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
        
        print("xmlContent %s"%xmlContent)
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
            #self.messages.append(format_msg)
            #self.messages.append(unicode(('%s %s %s')%(title,desc,app_url)))
            _msg = self.make_message(msg["UserName"],unicode(('%s %s %s')%(title,desc,app_url)))
            self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%(json.dumps(_msg)))
            #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode(('%s %s %s')%(title,desc,app_url)))
        else:
            pass
        
    def put_message_cache(self,cache_key,message):
        '''
        #用FromUserName做Key把消息存起來，同時把此人置頂
        '''   
        msg_type = message['MsgType']
        '''
        if msg_type == 10002 or self.isChatRoom(cache_key):
            cache_key = cache_key
        else:
            cache_key = message['FromUserName']
        '''
        row_count = self.chatsModel.rowCount()
        if row_count <= 0:
            self.blocked_messages_pool.append(message)
            return False
        if self.messages_pool.has_key(cache_key):
            messages = self.messages_pool[cache_key]
        else:
            messages = []
        messages.append(message)
        self.messages_pool[cache_key] = messages
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
            for member in self.wechatweb.getFriends():
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
    
    def msg_handle(self,message):
        msg_type = message['MsgType']
        #print("msg_handle() will processing ,msgtype %s,msg body:%s"%(str(msg_type),str(message)))
        if msg_type:
            if msg_type == 51:
                self.wxinitial_msg_handler(message)
                return
            if msg_type == 2 or msg_type == 52:
                logging.warn('msg not process:')
                logging.warn('msg type %d'%msg_type)
                logging.warn('msg body %s'%message)
                return
            
            print(self.wechatweb.getUser()["UserName"])
            print(message)
            #
            #
            #
            from_user_name = message['FromUserName']
            if self.isChatRoom(from_user_name):
                #user_name = from_user_name
                from_user_name = message['FromUserName']
            else:
                #如果消息的發送者和登陸人一致，那麼上比消息有可能是通過其他設备發送，那麼有取ToUserName,才能顯示正确
                if from_user_name == self.wechatweb.getUser()['UserName']:
                    from_user_name = message['ToUserName']
            '''
            #没有選擇和誰對話或者此消息的發送人和當前的對話人不一致，則把消息存放在message_cache中;
            #如果此消息的發件人和當前聊天的是同一個人，則把消息顯示在窗口中
            '''
            if (not self.current_chat_contact) or from_user_name != self.current_chat_contact['UserName']:
                self.put_message_cache(from_user_name,message)
            else:
                if msg_type == 1:
                    self.text_msg_handler(message)
                elif msg_type == 3:
                    self.image_msg_handler(message) 
                elif msg_type == 34:
                    self.voice_msg_handler(message)
                elif msg_type == 47:
                    self.default_msg_handler(message)
                elif msg_type == 49:
                    self.app_msg_handler(message)
                elif msg_type == 10002:
                    self.sys_msg_handler(message)
                else:
                    self.default_msg_handler(message)

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
                    self.wechatweb.webwx_get_msg_img(msg_id)
                    #st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
                    #format_msg = ('(%s) %s:') % (st, self.wechatweb.user['NickName'])
                    format_msg = self.msg_timestamp(self.wechatweb.getUser()['NickName'])
                    #self.messages.append(format_msg)
                    if self.isImage(ffile):
                        msg_img = ('<img src=%s/%s.jpg>'%(self.config.getCacheImageHome(),msg_id))
                    else:
                        msg_img = ffile
                    #self.messages.append(msg_img)
                    _msg = self.make_message(self.wechatweb.getUser()['UserName'],unicode(msg_img))
                    self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%(json.dumps(_msg)))
                    #self.messages.page().mainFrame().evaluateJavaScript("append('%s');"%unicode(msg_img))
                else:
                    #fileName=QtCore.QString.fromUtf8(fileName)
                    if self.isImage(ffile):
                        self.draft.append("<img src=%s width=80 height=80>"%(ffile))
                    else:
                        print(ffile)
                    
    def keyPressEvent(self,event):
        print("keyPressEvent")
    
    @pyqtSlot(str)
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
        data = json.loads(str(data), object_hook=_decode_data)
        ret_code = data['BaseResponse']['Ret']

        if ret_code == 0:
            pass
        else:
            return False

        add_msg_count = data['AddMsgCount']
        if add_msg_count == 0:
            return True

        messages = data['AddMsgList']

        for message in messages:
            self.msg_handle(message)
            
    def synccheck(self,loop=True):
        while (True):
            st = time.strftime("%Y-%m-%d %H:%M:%S ", time.localtime())
            print('push#synccheck %s' %(st))
            (code, selector) = self.wechatweb.sync_check()
            if code == -1 and selector == -1:
                print("self.wechatweb.sync_check() error")
            else:
                if code != '0':
                    if code == '1101' and selector == '0':
                        print("session timeout")
                        self.do_logout()
                        break
                else:
                    if selector != '0':
                        sync_response = self.wechatweb.webwx_sync()
                        #print("WeChatSync.run#webwx_sync:")
                        
                        self.messageReceived.emit(sync_response)
                        #self.webwx_sync_process(sync_response)
            if loop is False:
                break
            sleep(15)
