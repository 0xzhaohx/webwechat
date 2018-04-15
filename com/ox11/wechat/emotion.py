#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月10日

@author: zhaohongxing
'''
import os
from PyQt4 import QtGui, QtCore

from PyQt4.QtGui import QStandardItemModel, QTableView,\
    QVBoxLayout, QAbstractItemView, QCursor
from PyQt4.Qt import QIcon, QToolTip
from PyQt4.QtCore import QSize, pyqtSignal

def emotioncmp(x,y):
    xs = x.split(".")
    yx = y.split(".")
    if int(xs[0]) > int(yx[0]):
        return 1
    elif int(xs[0]) < int(yx[0]):
        return -1
    else:
        return 0
class Emotion(QtGui.QWidget):
    EMOTION_DIR = "./resource/expression"
    WIDTH = 460
    HEIGHT = 300
    selectChanged = pyqtSignal(str)
    
    def __init__(self,parent=None):#
        super(Emotion,self).__init__(parent)
        super(Emotion,self).setWindowFlags(QtCore.Qt.Popup)
        self.resize(QSize(Emotion.WIDTH,Emotion.HEIGHT))
        self.setWindowTitle("表情選擇")
        #self.setModal(True)
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.emotion_initial()
        
    def emotion_initial(self):
        self.emotion_table = QTableView()
        self.emotion_table.horizontalHeader().setVisible(False)
        self.emotion_table.verticalHeader().setVisible(False)
        self.emotion_table.setMouseTracking(True)
        self.emotion_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.emotion_table.verticalHeader().setDefaultSectionSize(30)
        self.emotion_table.horizontalHeader().setDefaultSectionSize(30)
        self.emotion_table.setIconSize(QSize(30,30))
        self.emotion_table.entered.connect(self.showEmotionTips)
        self.emotion_model = QStandardItemModel()
        
        emotions = os.listdir(Emotion.EMOTION_DIR)
        i = 0
        emotions_size = len(emotions)
        emotions = sorted(emotions,cmp=emotioncmp)
        while i < emotions_size:
            self.add_emotion(emotions[i:i+14])
            i = i + 14
        self.emotion_table.setModel(self.emotion_model)
        self.emotion_table.clicked.connect(self.emotion_click) 
        #
        mainLayout=QVBoxLayout()
        mainLayout.addWidget(self.emotion_table)
        self.setLayout(mainLayout)
        #self.
    def showEmotionTips(self,index):
        if index.isValid():
            QToolTip.showText(QCursor.pos(), "Hello", None)
    
    def add_emotion(self,emotions):
        '''
        :param emotions a list of emotion will be adding to emotion table
        '''
        cells = []
        for emotion in emotions:
            item = QtGui.QStandardItem(QIcon(os.path.join(Emotion.EMOTION_DIR,emotion)),emotion)
            cells.append(item)
        self.emotion_model.appendRow(cells)

    #def eventFilter(self, event):
        #p = QCursor.pos() - self.pos()
        #item = self.emotion_table
        
    def emotion_click(self):
        row = self.emotion_table.currentIndex().row()
        column = self.emotion_table.currentIndex().column()
        #self.accept()
        self.close()
        self.selectChanged.emit(self.get_selected_emotion(row,column))
        
    def get_selected_emotion(self,row,column):
        emotion = self.emotion_model.data(self.emotion_model.index(row, column))
        if emotion:
            return str(emotion)
        else:
            return "N/A"