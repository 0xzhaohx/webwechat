#!/usr/bin/python
# -*- coding:UTF-8 -*-

from PyQt4 import QtCore, QtGui


class BubbleList(QtGui.QWidget):
    pass


class BubbleListPrivate(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)

        self.m_item_vector = None
        self.m_current_index = 0
        self.m_selected_index = 0
        self.m_visible_item_cnt = 0
        self.m_item_counter = 0

        self.m_b_all_job_done = False
        self.m_hover_rect = None
        self.m_str_hover_text = None
        self.m_rotate_timer = None
        self.m_item_count_timer = None

    def addItem(self, str, orientation):
        pass

    def clear(self):
        pass

    def render(self):
        pass

    def setCurrentIndex(self, currentIndex):
        pass

    def paintEvent(self, event):
        pass

    def mouseMoveEvent(self, event):
        pass

    def mouseReleaseEvent(self, event):
        pass

    def resizeEvent(self, event):
        pass

    def leaveEvent(self, event):
        pass

    def showEvent(self, event):
        pass

    def wheelEvent(self, event):
        pass

    #private
    def drawBg(self, painter):
        pass

    def drawItems(self, painter):
        pass

    def drwaHoverRect(self, painter):
        pass

    def doRatation(self):
        pass

    def updateItemCount(self):
        pass

    def addItem(self, str, orientation):
        pass

    def clear(self):
        pass

    def render(self):
        self.update()

    def setCurrentIndex(self,currentIndex):
        pass

    #private utility functoins
    def initVars(self):
        pass

    def initSettings(self):
        pass

    def calcGeo(self):
        pass

    def makeupJobs(self):
        pass

    def wheelUp(self):
        pass

    def wheelDown(self):
        pass

    def itemCount(self):

        self.scrollbar = QtGui.QScrollBar(self)
        return 0


class ItemInfo(object):
    ITEM_START_ANGLE=270
    ITEM_D_ANGLE = 2
    ITEM_D_ZOOMING_FACTOR = 0.05

    def __init__(self,str,orientation=1,angle=270,zooming_factor=0):
        self.m_str_data = str
        self.m_orientation = orientation
        self.m_angle = angle
        self.m_zooming_factor =zooming_factor

    def setText(self,str):
        self.m_str_data = str

    def getText(self):
        return self.m_str_data

    def updateAngle(self):
        self.m_angle += ItemInfo.ITEM_D_ANGLE
        if self.m_angle > 360:
            self.m_angle = 0

    def updateZoomingFactor(self):
        self.m_zooming_factor += ItemInfo.ITEM_D_ZOOMING_FACTOR

        if self.m_zooming_factor > 1.0:
            self.m_zooming_factor = 1.0

    def jobDone(self):
        return self.m_angle == 360 or self.m_zooming_factor == 1.0

    def resetAngle(self):
        self.m_angle = ItemInfo.ITEM_D_ANGLE

    def resetZoomingFactor(self):
        self.m_zooming_factor = ItemInfo.ITEM_D_ZOOMING_FACTOR

    def getAngle(self):
        return self.m_angle

    def getZoomingFactor(self):
        return self.m_zooming_factor

    def inWrongPosition(self):
        return self.m_angle > ItemInfo.ITEM_START_ANGLE and self.m_angle < 360

    def inWrongZoomingPosition(self):
        return self.m_zooming_factor < 1.0

    def getOrientation(self):
        return self.m_orientation

    def setOrientation(self,orientation):
        self.m_orientation = orientation

class ChatBubble(QtGui.QWidget):

    def __init__(self):
        self.initVars()
        self.initWgts()
        self.initStgs()
        self.initConns()

    def initVars(self):
        pass

    def initWgts(self):
        main_layout = QtGui.QHBoxLayout(self)
        scrollbar = QtGui.QScrollBar(self)

        self.setMinimumWidth(300)
        self.setLayout(main_layout)
        pass

    def initStgs(self):

        pass

    def initConns(self):
        pass

