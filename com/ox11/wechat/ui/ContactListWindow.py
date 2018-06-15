#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年6月15日

@author: zhaohongxing
'''
import os

from PyQt4.Qt import QIcon, Qt
from PyQt4 import QtGui
from PyQt4.QtGui import QStandardItemModel,QTableView, QVBoxLayout, QPushButton
from PyQt4.QtCore import QSize, pyqtSignal

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