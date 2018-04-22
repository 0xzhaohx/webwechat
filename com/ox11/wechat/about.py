#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月13日

@author: zhaohongxing
'''
from PyQt4 import QtGui

from PyQt4.QtGui import QVBoxLayout
from PyQt4.QtCore import QSize, Qt

class About(QtGui.QDialog):
    WIDTH = 460
    HEIGHT = 300
    
    def __init__(self,parent=None):
        super(About,self).__init__(parent)
        #super(About,self).setWindowFlags(QtCore.Qt.Popup)
        self.setModal(True)
        self.resize(QSize(About.WIDTH,About.HEIGHT))
        self.setWindowTitle(unicode("關於"))
        self.about_initial()
        
    def about_initial(self):
        #
        mainLayout=QVBoxLayout()
        label = QtGui.QLabel("v0.5")
        label.setAlignment(Qt.AlignHCenter)
        mainLayout.addWidget(label)
        #mainLayout.addWidget(self.emotion_table)
        self.setLayout(mainLayout)