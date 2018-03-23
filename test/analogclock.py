#!usr/bin/python2.7
# -*- coding: UTF-8-*-

import sys
from PyQt4 import QtGui, uic


class AnalogClock(QtGui.QWidget):

    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.setWindowTitle('Analog Clock')
        self.resize(200,200)

    def paintEvent(self, QPaintEvent):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.translate(self.width() / 2,self.height() / 2)
        #
        #painter.scale(self.size() / 200.0,self.size()/ 200.0)




if __name__ =="__main__":

    app = QtGui.QApplication(sys.argv)
    clock = AnalogClock()
    clock.show()
    sys.exit(app.exec_())