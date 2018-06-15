#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-

'''
Created on 2018年6月15日

@author: zhaohongxing
'''
import os

from PyQt4.Qt import QIcon
from PyQt4 import QtGui
from PyQt4.QtGui import QStandardItemModel,\
    QTableView, QVBoxLayout, QPushButton, QSpacerItem
from PyQt4.QtCore import QSize, pyqtSlot, pyqtSignal
from com.ox11.wechat.ui.ContactListWindow import ContactListWindow


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