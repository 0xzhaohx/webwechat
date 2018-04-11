import sys

from PyQt4.QtGui import QPainter, QWidget, QPixmap, QColor, QLabel
from PyQt4 import QtGui
from PyQt4.QtCore import QSize

class HeadWidget(QWidget):
    
    HEAD_IMG_WIDTH = HEAD_IMG_HEIGHT = 45
    MINI_MUM_SIZE = 70
    
    def __init__(self,img,msg_numbers = 0,parent=None):
        super(HeadWidget,self).__init__(parent)
        self.setMinimumSize(HeadWidget.MINI_MUM_SIZE, HeadWidget.MINI_MUM_SIZE)
        #self.resize(QSize(60,60))
        self.img = img
        self.msg_numbers = msg_numbers
        
    def paintEvent(self, event):
        #QLabel.paintEvent(event)
        painter = QPainter(self)
        painter.save()
        painter.drawPixmap(20,20,HeadWidget.HEAD_IMG_WIDTH,HeadWidget.HEAD_IMG_HEIGHT, QPixmap(self.img))
        if self.msg_numbers and self.msg_numbers > 0:
            white = QColor(255, 0, 0)
            painter.setPen(white)
            painter.setBrush(white)
            painter.drawEllipse(52.5,10,20,20)
            red = QColor(255, 255, 255)
            painter.setPen(red)
            painter.setBrush(red)
            x = 60
            
            if self.msg_numbers >= 10 and self.msg_numbers < 100:
                x = 57.5
            elif self.msg_numbers >= 100 and self.msg_numbers < 1000:
                x = 55
            elif self.msg_numbers >= 1000 and self.msg_numbers < 10000:
                x = 52.5
            painter.drawText(x,25, str(self.msg_numbers))
        painter.restore()
        
    def setNumber(self,number=0):
        if number > 0:
            self.msg_numbers = self.msg_numbers + number
        else:
            self.msg_numbers = 0
        
        self.update()
        
    def increase (self):
        self.msg_numbers = self.msg_numbers + 1
        self.update()
        
    def clean (self):
        self.msg_numbers = 0
        self.update()
    
if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)
    img = "C:/Users/zhaohongxing/Pictures/aaaa.jpg"
    launcher = HeadWidget(img = img,msg_numbers=10)
    launcher.show()
    sys.exit(app.exec_())
