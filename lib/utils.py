#!/usr/bin/env python
import os
from PyQt5 import QtWidgets

def load_qss_from_txt(widget, txt):
    with open(txt) as f:
        qss = f.readlines()
        qss =''.join(qss).strip('\n')
    widget.setStyleSheet(qss)
