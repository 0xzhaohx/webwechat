#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-


import os
import sys
import threading
from time import sleep

from PyQt4 import QtCore,QtGui, uic

from PyQt4.QtGui import QStandardItemModel, QStandardItem
from PyQt4.Qt import Qt, QVariant, QIcon
from PyQt4.QtCore import QSize

qtCreatorFile = "resource/ui/table-view.ui"

TableViewWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class WeChatLauncher(QtGui.QDialog, TableViewWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        TableViewWindow.__init__(self)
        self.setupUi(self)
        self.model = QStandardItemModel();
        self.doTableInitial()
        self.addButton.clicked.connect(self.do_append_item)
        self.insertButton.clicked.connect(self.do_insert_item)
        self.removeButton.clicked.connect(self.do_remove_item)
        self.upButton.clicked.connect(self.up_item)
        self.downButton.clicked.connect(self.down_item)
        self.dataTableView.clicked.connect(self.item_click)
        
        
    def item_click(self):
        current_row = self.dataTableView.currentIndex().row()
        print("click row %d"%(current_row))
        
    def doTableInitial(self):
        self.dataTableView.setIconSize(QSize(160*2,160*2))
        self.model.setColumnCount(4);
        self.model.setHeaderData(0,Qt.Horizontal,QVariant(QtCore.QString.fromUtf8("ID")));
        self.model.setHeaderData(1,Qt.Horizontal,QVariant(QtCore.QString.fromUtf8("頭像")));
        self.model.setHeaderData(2,Qt.Horizontal,QVariant(QtCore.QString.fromUtf8("姓名")));
        self.model.setHeaderData(3,Qt.Horizontal,QVariant("xuhao"));
        self.dataTableView.setModel(self.model)
        self.dataTableView.setColumnHidden(0,True)
        #self.dataTableView.setColumnWidth(0,0)
    
    def do_append_item(self):
        item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/electronic-wechat.png"),"")
        rowCount = self.model.rowCount()
        self.model.setItem(rowCount,1,item)
        item = QtGui.QStandardItem()
        item.setText("%d-sssddddddddddddttt"%(rowCount))
        self.model.setItem(rowCount,2,item)
        
    def do_insert_item(self):
        current_row = self.dataTableView.currentIndex().row()
        print(current_row)
        row = []
        if current_row > 0:
            self.model.insertRow(-1)
            print("after insert:%d"%(current_row))
            index = self.model.index(0,2)
            
            cell_index =self.model.index(current_row, 2)
            cell_o = self.model.data(cell_index)
            self.model.setData(index, cell_o.toString())
            #cell_item = QStandardItem(cell_o);
            self.model.removeRow(current_row)
            return True
        item = QtGui.QStandardItem(QIcon("resource/icons/hicolor/32x32/apps/electronic-wechat.png"),"")
        #self.model.setItem(-1,0,item)
        row.append(item)
        item = QtGui.QStandardItem("ddd")
        row.append(item)
        self.model.insertRow(0, row)
    
    def do_remove_item(self):
        current_row = self.dataTableView.currentIndex().row()
        print("remove row %d"%(current_row))
        self.model.removeRow(current_row)
    
    def down_item(self):
        print("down")
    
    def up_item(self):
        print("up")

if __name__ =="__main__":

    #QtGui.QTextCodec.setCodecForTr(QtGui.QTextCodec.codecForName("utf8"))
    #QtGui.QTextCodec.setCodecForCStrings(QtGui.QTextCodec.codecForLocale())
    app = QtGui.QApplication(sys.argv)
    launcher = WeChatLauncher()
    launcher.show()
    if QtGui.QDialog.Accepted == launcher.exec_():
        sys.exit(app.exec_())
    else:
        sys.exit(0)
