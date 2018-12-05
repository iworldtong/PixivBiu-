#!/usr/bin/env python

from PyQt5 import QtCore, QtGui, QtWidgets

class CirLabel(QtWidgets.QLabel):
    def __init__(self, *args, img_path, antialiasing=True, **kwargs):
        super(CirLabel, self).__init__(*args, **kwargs)
        self.Antialiasing = antialiasing
        self.setIcon(img_path)

    def setIcon(self, img_path):
        self.length = 100
        self.setMaximumSize(self.length, self.length)
        self.setMinimumSize(self.length, self.length)
        self.radius = self.length // 2

        self.target = QtGui.QPixmap(self.size())  # 大小和控件一样
        self.target.fill(QtCore.Qt.transparent)  # 填充背景为透明

        p = QtGui.QPixmap(img_path).scaled(  # 加载图片并缩放和控件一样大
            self.length, self.length, QtCore.Qt.KeepAspectRatioByExpanding, QtCore.Qt.SmoothTransformation)

        painter = QtGui.QPainter(self.target)
        if self.Antialiasing:
            # 抗锯齿
            painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
            painter.setRenderHint(QtGui.QPainter.HighQualityAntialiasing, True)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform, True)

#         painter.setPen(# 测试圆圈
#             QPen(Qt.red, 5, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        path = QtGui.QPainterPath()
        path.addRoundedRect(
            0, 0, self.width(), self.height(), self.radius, self.radius)
        #**** 切割为圆形 ****#
        painter.setClipPath(path)
#         painter.drawPath(path)  # 测试圆圈

        painter.drawPixmap(0, 0, p)
        self.setPixmap(self.target)