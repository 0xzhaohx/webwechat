#!/usr/bin/python2.7
# -*- coding: UTF-8 -*-
'''
Created on 2018年4月10號

@author: zhaohongxing
'''
import os

from PyQt4.Qt import QStyledItemDelegate, QColor, QPixmap
from PyQt4.QtGui import QStyle

class LabelDelegate(QStyledItemDelegate):
    
    HEAD_IMG_WIDTH = HEAD_IMG_HEIGHT = 45
    
    Editable, ReadOnly = range(2)
    
    USER_NAME_COLUMN = 0
    
    MSG_COUNT_COLUMN = 3
    
    DEFAULT_IMAGE = "./resource/images/default.png"
    
    USER_HOME = os.path.expanduser('~')
    
    CONTACT_HEAD_HOME = ("/heads/contact/")
    
    def paint(self, painter, option,index):
        if index.column() ==1:
            model = index.model()
            userNameIndex = model.index(index.row(),LabelDelegate.USER_NAME_COLUMN)
            msgCountIndex = model.index(index.row(),LabelDelegate.MSG_COUNT_COLUMN)
            
            userName = model.data(userNameIndex)
            msgCount = model.data(msgCountIndex)
            
            if option.state & QStyle.State_Selected:
                painter.fillRect(option.rect, option.palette.highlight())
            rect_x = option.rect.x()
            rect_y = option.rect.y()
            head_image_x_offset = 5
            head_image_y_offset = 10
            head_image_x = rect_x + head_image_x_offset
            head_image_y = rect_y + head_image_y_offset
            image = ("%s/.wechat/%s/%s.jpg")%(LabelDelegate.USER_HOME,LabelDelegate.CONTACT_HEAD_HOME,userName)
            if not os.path.exists(image):
                image = LabelDelegate.DEFAULT_IMAGE
            painter.drawPixmap(head_image_x,head_image_y,LabelDelegate.HEAD_IMG_WIDTH,LabelDelegate.HEAD_IMG_HEIGHT, QPixmap(image))
            msg_numbers = msgCount
            if msg_numbers and msg_numbers > 0:
                white = QColor(255, 0, 0)
                painter.setPen(white)
                painter.setBrush(white)
                ellipse_r = 20
                ellipse_x = rect_x+LabelDelegate.HEAD_IMG_WIDTH-5
                ellipse_y = rect_y+head_image_y_offset-7.5
                
                painter.drawEllipse(ellipse_x,ellipse_y,ellipse_r,ellipse_r)
                red = QColor(255, 255, 255)
                painter.setPen(red)
                painter.setBrush(red)
                
                msg_count_x = rect_x+LabelDelegate.HEAD_IMG_WIDTH+0.5
                
                if msg_numbers >= 10 and msg_numbers < 100:
                    msg_count_x = msg_count_x-0.5
                elif msg_numbers >= 100 and msg_numbers < 1000:
                    msg_count_x = msg_count_x - 3.5
                elif msg_numbers >= 1000 and msg_numbers < 10000:
                    msg_count_x = msg_count_x - 5
                msg_count_y = rect_y+head_image_y_offset+5
                painter.drawText(msg_count_x,msg_count_y, str(msg_numbers))
        else:
            super(LabelDelegate, self).paint(painter, option, index)