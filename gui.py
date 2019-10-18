#!/usr/bin/env python
from PyQt5 import QtCore, QtGui, QtWidgets
import qtawesome
import sys,os
import pickle


from lib import *
from pixivpy3.bapi import ByPassSniApi



class MainUi(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.is_login = False
        self.is_premium = False
        
        self.cfg = {
            'type': None,
            'key': None,
            'min_popular': 0,
            'use_ms': True,

            'sleep_download_time': 1,

            'cache_dir': './cache',
            'save_dir': './download',
            'login_cache': 'login.pickle',
        }

        self.api = ByPassSniApi()
        self.api.require_appapi_hosts()
        self.api.set_accept_language('en-us')  # zh-cn

        # 缓存登陆信息，下载进度
        if not os.path.exists(self.cfg['cache_dir']):
            os.makedirs(self.cfg['cache_dir'])

        self.init_ui()

    def closeEvent(self, event):
        sys.exit(app.exec_()) # 子线程同步退出

    def init_ui(self):
        #####################################################
        #               主界面
        #####################################################
        self.main_widget = QtWidgets.QWidget() 
        self.main_layout = QtWidgets.QHBoxLayout(spacing=0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_widget.setLayout(self.main_layout)

        self.left_widget = QtWidgets.QWidget()  
        self.left_widget.setObjectName('left_widget')
        self.left_layout = QtWidgets.QVBoxLayout()  
        self.left_layout.setContentsMargins(0, 0, 0, 0)
        self.left_widget.setLayout(self.left_layout) 

        self.right_widget = QtWidgets.QWidget() 
        self.right_widget.setObjectName('right_widget')
        self.right_layout = QtWidgets.QGridLayout()
        self.right_widget.setLayout(self.right_layout) 
        self.right_stackedWidget = QtWidgets.QStackedWidget()
        self.right_layout.addWidget(self.right_stackedWidget)

        self.main_layout.addWidget(self.left_widget)
        self.main_layout.addWidget(self.right_widget)
        self.main_layout.setSpacing(0)

        self.resize(900,640)
        self.setWindowIcon(QtGui.QIcon('./static/img/pixiv.ico'))
        self.setWindowTitle('PixivBiu～')
        self.setCentralWidget(self.main_widget)

        self.init_left_nav()
        self.init_serach_page()
        self.init_login_page()
        self.init_setting_page()
        self.init_about_page()
                

    def init_left_nav(self):
        #####################################################
        #               左侧导航栏
        #####################################################
        nav_list = ['搜索','账号','设置','关于']

        self.home_label = QtWidgets.QPushButton("PixivBiu")
        self.home_label.setObjectName('left_label')

        self.left_listWidget = QtWidgets.QListWidget()
        self.left_listWidget.setObjectName('left_listWidget')
        self.left_listWidget.setFrameShape(QtWidgets.QListWidget.NoFrame)
        self.left_listWidget.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.left_listWidget.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.left_listWidget.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框
        for i in nav_list:
            item = QtWidgets.QListWidgetItem(i, self.left_listWidget)            
            item.setSizeHint(QtCore.QSize(16777215, 60)) 
            item.setTextAlignment(QtCore.Qt.AlignCenter) 

        self.left_layout.addWidget(self.home_label)
        self.left_layout.addStretch(2)
        self.left_layout.addWidget(self.left_listWidget)
        self.left_layout.addStretch(8)

        load_qss_from_txt(self.left_widget, './static/qss/left_widget.txt')
        load_qss_from_txt(self.right_widget, './static/qss/right_widget.txt')

        self.home_label.clicked.connect(self.left_listWidget.setCurrentRow, 0)
        self.left_listWidget.currentRowChanged.connect(self.right_stackedWidget.setCurrentIndex)


    def download_thread_callback(self, msg):
        print(msg)
        if msg == 'done': 
            self.opacity.setOpacity(0)
            self.progress_bar.setGraphicsEffect(self.opacity)
            self.progress_bar.setValue(0)
            self.download_btn.setChecked(False)
            self.search_input.setEnabled(True)
            self.pixiv_icon_effect.stop()
            self.download_thread = None
        else:
            if msg.isdigit():
                self.progress_bar.setValue(int(msg))
        

    def download_btn_callback(self):
        # 判断是否满足下载条件
        if not self.page_start_el.text().isdigit():
            if len(self.page_start_el.text()) > 0:
                self.download_btn.setChecked(False)
                NotificationWindow.warning('页数必须为整数', '')    
                return False 
        else:
            self.cfg['page_start'] = int(self.page_start_el.text())
        if not self.page_num_el.text().isdigit():
            if len(self.page_num_el.text()) > 0:
                self.download_btn.setChecked(False)
                NotificationWindow.warning('页数必须为整数', '')    
                return False 
        else:
            self.cfg['page_num'] = int(self.page_num_el.text())

        # if not self.popular_lower_el.text().isdigit():
        #     if len(self.popular_lower_el.text()) > 0:
        #         self.download_btn.setChecked(False)
        #         NotificationWindow.warning('收藏量下限必须为整数', '')    
        #         return False 
        # else:
        #     self.cfg['min_popular'] = int(self.popular_lower_el.text())

        # 下载流程
        if self.download_btn.isChecked():
            self.cfg['key'] = self.search_input.text().strip()

            self.search_input.setEnabled(False)
            self.pixiv_icon_effect.start()
            self.opacity.setOpacity(1)
            self.progress_bar.setGraphicsEffect(self.opacity)

            self.download_thread = DownloadThread(self.api, self.cfg)
            self.download_thread._signal.connect(self.download_thread_callback)
            self.download_thread.start()
        else:
            self.search_input.setEnabled(True)
            if self.download_thread is not None:
                self.download_thread.callback('stop')
                self.pixiv_icon_effect.stop()
                self.opacity.setOpacity(0)
                self.progress_bar.setGraphicsEffect(self.opacity)
                self.progress_bar.setValue(0)
        return True

    def init_serach_page(self):
        #####################################################
        #               搜索页面 
        #####################################################
        self.search_widget = QtWidgets.QWidget() 
        self.search_layout = QtWidgets.QGridLayout() 
        self.search_layout.setSpacing(10)
        self.search_widget.setLayout(self.search_layout)  

        # icon显示
        # self.pixiv_icon = QtWidgets.QToolButton()
        # self.pixiv_icon.setIcon(QtGui.QIcon('./static/img/pixiv.png'))
        # self.pixiv_icon.setIconSize(QtCore.QSize(100, 100))
        # self.pixiv_icon.setStyleSheet('border:None;')
        self.pixiv_icon = QtWidgets.QLabel(self)
        self.pixiv_icon.setMinimumSize(100, 100)
        self.pixiv_icon.setMaximumSize(100, 100)
        self.pixiv_icon.setStyleSheet('border-image: url(./static/img/pixiv.png); border-radius: 50px;')
        self.pixiv_icon_effect = AnimationShadowEffect(QtGui.QColor(29, 139, 241))
        self.pixiv_icon.setGraphicsEffect(self.pixiv_icon_effect)

        # 搜索框
        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("Biu~")
        self.search_input.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        def search_change():
            self.download_thread = None
            if len(self.search_input.text().strip()) > 0:
                self.download_btn.setEnabled(True)
            else:
                self.download_btn.setEnabled(False)
        self.search_input.textChanged.connect(search_change)

        # 主题 / 作者 搜索
        self.tp_widget = QtWidgets.QWidget()
        self.tp_layout = QtWidgets.QHBoxLayout() 
        self.tp_widget.setLayout(self.tp_layout)
        self.tag_rb = QtWidgets.QRadioButton('按主题')
        self.usr_rb = QtWidgets.QRadioButton('按作者')
        self.tp_g = QtWidgets.QButtonGroup(self)
        self.tp_g.addButton(self.tag_rb, 11)
        self.tp_g.addButton(self.usr_rb, 12)        
        def tp_change():
            if self.tp_g.checkedId() == 11:
                self.cfg['type'] = 'tag'
            elif self.tp_g.checkedId() == 12:
                self.cfg['type'] = 'uid'
        self.tp_g.buttonClicked.connect(tp_change)
        self.tag_rb.toggle()
        self.cfg['type'] = 'tag'
        self.tag_rb.setEnabled(False)
        self.usr_rb.setEnabled(False)

        # 下载按钮
        self.download_btn = QtWidgets.QPushButton()
        self.download_btn.setObjectName('download_btn')
        self.download_btn.setFixedSize(30, 30)
        self.download_btn.setEnabled(False)
        # 按钮保持按下状态
        self.download_btn.setCheckable(True)
        self.download_btn.setAutoExclusive(True)
        self.download_btn.clicked.connect(self.download_btn_callback)

        # 下载进度条
        self.progress_bar = QtWidgets.QProgressBar(minimum=0, maximum=100, textVisible=False,
                                                   objectName="ProgressBar")
        self.opacity = QtWidgets.QGraphicsOpacityEffect()
        self.opacity.setOpacity(0)
        self.progress_bar.setGraphicsEffect(self.opacity)

        # 布局
        self.tp_layout.addWidget(self.tag_rb)
        self.tp_layout.addWidget(self.usr_rb)
        self.tp_layout.addStretch(0)
        self.tp_layout.addWidget(self.download_btn)

        self.search_layout.addWidget(self.pixiv_icon,0,1,1,4,QtCore.Qt.AlignCenter)
        self.search_layout.addWidget(self.search_input,1,1,1,4)
        self.search_layout.addWidget(self.tp_widget,2,1,1,4)
        self.search_layout.addWidget(self.progress_bar,4,1,1,4)

        self.search_layout.setRowStretch(0,3)
        self.search_layout.setRowStretch(1,1)
        self.search_layout.setRowStretch(2,1)
        self.search_layout.setRowStretch(3,4)
        self.search_layout.setColumnStretch(0,1)
        self.search_layout.setColumnStretch(1,10)
        self.search_layout.setColumnStretch(5,1)

        load_qss_from_txt(self.search_input, './static/qss/search_page_input.txt')
        load_qss_from_txt(self.progress_bar, './static/qss/search_page_progressbar.txt')

        self.right_stackedWidget.addWidget(self.search_widget)


    def init_login_page(self):
        #####################################################
        #               登陆页面 
        #####################################################
        self.login_widget = QtWidgets.QWidget()
        self.login_layout = QtWidgets.QGridLayout() 
        self.login_widget.setLayout(self.login_layout)

        self.login_info = {'uid': '', 'pwd': ''}

        # 用户头像
        # self.profile_icon = QtWidgets.QToolButton()
        # self.profile_icon.setIcon(QtGui.QIcon('./static/img/anonymous.png'))
        # self.profile_icon.setIconSize(QtCore.QSize(100, 100))
        # self.profile_icon.setStyleSheet('border:None;')
        self.profile_icon = CirLabel(img_path='./static/img/anonymous.png')

        # 信息输入框
        self.uid_le = QtWidgets.QLineEdit()
        self.uid_le.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.uid_le.setPlaceholderText("Pixvi ID")
        self.pwd_le = QtWidgets.QLineEdit()
        self.pwd_le.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.pwd_le.setEchoMode(QtWidgets.QLineEdit.Password)
        self.pwd_le.setPlaceholderText("Password")

        # 检查是否有历史登录信息
        if os.path.exists(os.path.join(self.cfg['cache_dir'], self.cfg['login_cache'])):
            with open(os.path.join(self.cfg['cache_dir'], self.cfg['login_cache']), 'rb') as f:
                self.login_info = pickle.load(f)
                self.uid_le.setText(self.login_info['uid'])
                self.pwd_le.setText(self.login_info['pwd'])


        # 关联登陆输入与登陆按钮
        def login_info_change():
            if len(self.uid_le.text().strip()) > 0 and len(self.pwd_le.text().strip()) > 0:
                self.login_btn.setEnabled(True)
            else:
                self.login_btn.setEnabled(False)
        self.uid_le.textChanged.connect(login_info_change)
        self.pwd_le.textChanged.connect(login_info_change)

        # 登陆、登出按钮
        login_s = 'Log in'
        logout_s = 'Log out'
        self.login_btn = QtWidgets.QPushButton(login_s)
        login_info_change()
        def login_btn_callback():
            if self.login_btn.text() == login_s:
                # 设置本地ss代理
                self.login_info['uid'] = self.uid_le.text().strip()
                self.login_info['pwd'] = self.pwd_le.text().strip()
                # 登陆时主界面冻结
                self.usr_type = QtWidgets.QLabel()
                self.usr_type.setAlignment(Qt.AlignCenter)
                self.login_metrobar = MetroCircleProgress(styleSheet='''qproperty-color: #3498DB;''')
                self.login_layout.addWidget(self.login_metrobar,5,0,1,6)
                self.uid_le.setEnabled(False)
                self.pwd_le.setEnabled(False)
                self.login_btn.setEnabled(False)
                # 登陆
                self.login_thread = LoginThread(self.login_info, self.api)
                self.login_thread._signal.connect(login_thread_callback)
                self.login_thread.start()
                
            else:
                self.profile_icon.setIcon('./static/img/anonymous.png')
                self.uid_le.show()
                self.pwd_le.show()
                self.if_rember_ck.show()
                self.login_btn.setText(login_s)

                self.login_layout.setRowStretch(0,4)
                self.login_layout.setRowStretch(5,4)
                self.login_layout.removeWidget(self.usr_type)
                self.usr_type.deleteLater()

                self.is_login = False
                self.login_info['uid'] = ''
                self.login_info['pwd'] = ''

        def login_thread_callback(msg):
            self.uid_le.setEnabled(True)
            self.pwd_le.setEnabled(True)
            self.login_btn.setEnabled(True)

            if msg != 'false':
                self.user_json = self.api.user_detail(self.api.user_id)
                # 保存登陆信息
                if self.if_rember_ck.isChecked():
                    with open(os.path.join(self.cfg['cache_dir'], self.cfg['login_cache']), 'wb') as f:
                        pickle.dump(self.login_info, f)
                else:
                    if os.path.exists(os.path.join(self.cfg['cache_dir'], self.cfg['login_cache'])):
                        os.remove(os.path.join(self.cfg['cache_dir'], self.cfg['login_cache']))
               
                # 判断是否高级用户
                if msg == "premium":
                    self.usr_type.setText("高级会员")
                    self.is_premium = True
                else:
                    self.usr_type.setText("普通会员")
                    self.is_premium = False
                self.usr_type.setFont(QtGui.QFont("Roman times",14,QtGui.QFont.Bold))
                
                # 整理主界面
                self.login_btn.setText(logout_s)
                self.uid_le.hide()
                self.pwd_le.hide()
                self.if_rember_ck.hide()
                self.login_layout.addWidget(self.usr_type,1,1,1,4)
                self.login_layout.setRowStretch(0,5)
                self.login_layout.setRowStretch(1,2)
                self.login_layout.setRowStretch(5,6)

                # 显示登录用户头像
                self.profile_path = ''
                for i in os.listdir(self.cfg['cache_dir']):
                    if i.split('.')[0] == 'profile': 
                        self.profile_path = os.path.join(self.cfg['cache_dir'], i)

                if len(self.profile_path) < 4:
                    self.profile_icon.setIcon('./static/img/pixiv.png')
                else:
                    self.profile_icon.setIcon(self.profile_path)
                    # self.profile_icon.setIcon(QtGui.QIcon(self.profile_path))
                    os.remove(self.profile_path)
                NotificationWindow.success('欢迎回来, {}'.format(self.user_json.user.name), '')

            else:
                self.is_login = False
                self.login_info['uid'] = ''
                self.login_info['pwd'] = ''
                NotificationWindow.error('登陆失败','')
            # 去掉等待动画
            self.login_layout.removeWidget(self.login_metrobar)
            self.login_metrobar.deleteLater()
        self.login_btn.clicked.connect(login_btn_callback)


        # 是否保存登陆信息
        self.if_rember_ck = QtWidgets.QCheckBox('记住我')
        # def if_rember_callback():
        #     self.cfg['rember_me'] = self.if_rember_ck.isChecked()
        # self.if_rember_ck.stateChanged.connect(if_rember_callback)
        # self.if_rember_ck.setChecked(os.path.exists(self.cfg['usr_info_path']))
        self.if_rember_ck.setChecked(True)

        # 布局
        self.login_layout.addWidget(self.profile_icon,0,1,1,4,QtCore.Qt.AlignCenter)
        self.login_layout.addWidget(self.uid_le,1,1,1,4)
        self.login_layout.addWidget(self.pwd_le,2,1,1,4)
        self.login_layout.addWidget(self.if_rember_ck,3,2,1,2,QtCore.Qt.AlignCenter)
        self.login_layout.addWidget(self.login_btn,4,2,1,2)
        self.login_layout.addWidget(QtWidgets.QWidget(),5,0,1,6)

        self.login_layout.setRowStretch(0,4)
        self.login_layout.setRowStretch(5,4)
        self.login_layout.setColumnStretch(0,7)
        self.login_layout.setColumnStretch(2,4)
        self.login_layout.setColumnStretch(5,7)

        load_qss_from_txt(self.login_widget, './static/qss/login_page.txt')

        self.right_stackedWidget.addWidget(self.login_widget)
    
    def init_setting_page(self):
        #####################################################
        #               设置页面
        #####################################################
        self.set_widget = QtWidgets.QWidget()
        self.set_layout = QtWidgets.QGridLayout() 
        self.set_widget.setLayout(self.set_layout)

        # 页数限定
        self.page_widget = QtWidgets.QWidget()
        self.page_layout = QtWidgets.QGridLayout() 
        self.page_widget.setLayout(self.page_layout)
        
        self.page_label = QtWidgets.QLabel("限定搜索页数")
        self.page_label.setObjectName("header")
        self.page_start_label = QtWidgets.QLabel("起始页")
        self.page_start_el = QtWidgets.QLineEdit("1")
        self.page_start_el.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框
        self.page_start_el.setPlaceholderText("不限")
        self.page_num_label = QtWidgets.QLabel("页数")
        self.page_num_el = QtWidgets.QLineEdit("100")
        self.page_num_el.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框
        self.page_num_el.setPlaceholderText("不限")

        row_start = 0
        self.set_layout.addWidget(self.page_label,row_start,0,1,2)
        self.set_layout.addWidget(self.page_start_label,row_start+1,0,1,1)
        self.set_layout.addWidget(self.page_start_el,row_start+1,1,1,2)
        self.set_layout.addWidget(self.page_num_label,row_start+1,4,1,1)
        self.set_layout.addWidget(self.page_num_el,row_start+1,5,1,1)


        # 收藏量限定
        # self.popular_widget = QtWidgets.QWidget()
        # self.popular_layout = QtWidgets.QGridLayout() 
        # self.popular_widget.setLayout(self.popular_layout)
        
        # self.popular_label = QtWidgets.QLabel("限定收藏量")
        # self.popular_label.setObjectName("header")
        # self.popular_lower_label = QtWidgets.QLabel("下限")
        # self.popular_lower_el = QtWidgets.QLineEdit("10")
        # self.popular_lower_el.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框
        # self.popular_lower_el.setPlaceholderText("不限")

        # row_start = 3
        # self.set_layout.addWidget(self.popular_label,row_start,0,1,2)
        # self.set_layout.addWidget(self.popular_lower_label,row_start+1,0,1,1)
        # self.set_layout.addWidget(self.popular_lower_el,row_start+1,1,1,1)


        # 本地ss代理设置
        # self.local_ss_widget = QtWidgets.QWidget()
        # self.local_ss_layout = QtWidgets.QGridLayout() 
        # self.local_ss_widget.setLayout(self.local_ss_layout)
        

        # self.local_ss_label = QtWidgets.QLabel("本地ss代理")
        # self.local_ss_label.setObjectName("header")
        # self.local_ss_ip_label = QtWidgets.QLabel("IP")
        # self.local_ss_port_label = QtWidgets.QLabel("Port")
        # self.local_ss_ip_el = QtWidgets.QLineEdit("127.0.0.1")
        # self.local_ss_ip_el.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框
        # self.local_ss_port_el = QtWidgets.QLineEdit("1086")
        # self.local_ss_port_el.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0) #获取焦点时,去掉系统的蓝色边框

        # row_start = 6
        # self.set_layout.addWidget(self.local_ss_label,row_start,0,1,2)
        # self.set_layout.addWidget(self.local_ss_ip_label,row_start+1,0,1,1)
        # self.set_layout.addWidget(self.local_ss_ip_el,row_start+1,1,1,2)
        # self.set_layout.addWidget(self.local_ss_port_label,row_start+1,4,1,1)
        # self.set_layout.addWidget(self.local_ss_port_el,row_start+1,5,1,1)

        # 下载到
        self.sdir_label = QtWidgets.QLabel("下载到")
        self.sdir_label.setObjectName("header")
        self.sdir_btn = QtWidgets.QPushButton(self.cfg['save_dir'])
        def sdir_btn_callback():
            sdir_select = QtWidgets.QFileDialog.getExistingDirectory(None, "Select a directory", self.cfg['save_dir'])
            if sdir_select != '':
                self.cfg['save_dir'] = sdir_select
            self.sdir_btn.setText(self.cfg['save_dir'])
        self.sdir_btn.clicked.connect(sdir_btn_callback)

        row_start = 3#9
        self.set_layout.addWidget(self.sdir_label,row_start,0,1,2)
        self.set_layout.addWidget(self.sdir_btn,row_start,1,1,4)


        # 是否使用多线程
        self.ms_widget = QtWidgets.QWidget()
        self.ms_layout = QtWidgets.QGridLayout() 
        self.ms_widget.setLayout(self.ms_layout)

        self.ms_label = QtWidgets.QLabel("高级设置")
        self.ms_label.setObjectName("header")
        self.ms_ck = QtWidgets.QCheckBox('多线程下载')
        self.ms_ck.setChecked(self.cfg['use_ms'])
        def if_ms_ck_callback():
            self.cfg['use_ms'] = self.ms_ck.isChecked()
        self.ms_ck.stateChanged.connect(if_ms_ck_callback)

        row_start = 6#12
        self.set_layout.addWidget(self.ms_label,row_start,0,1,2)
        self.set_layout.addWidget(self.ms_ck,row_start+1,0,1,1)


        self.set_layout.setColumnStretch(6,10)
        self.set_layout.setRowStretch(2,1)
        self.set_layout.setRowStretch(5,1)
        self.set_layout.setRowStretch(8,1)
        self.set_layout.setRowStretch(11,1)
        self.set_layout.setRowStretch(18,10)

        load_qss_from_txt(self.set_widget, './static/qss/setting_page.txt')

        self.right_stackedWidget.addWidget(self.set_widget)

    def init_about_page(self):
        #####################################################
        #               关于页面 
        #####################################################
        self.about_widget = QtWidgets.QWidget()
        self.about_layout = QtWidgets.QGridLayout() 
        self.about_widget.setLayout(self.about_layout)

        label = QtWidgets.QLabel('为热爱二次元的你')
        label.setAlignment(QtCore.Qt.AlignCenter)
        # 设置label的背景颜色(这里随机)
        # 这里加了一个margin边距(方便区分QStackedWidget和QLabel的颜色)     

        self.about_layout.addWidget(label,1,1,1,1)

        load_qss_from_txt(self.about_widget, './static/qss/about_page.txt')

        self.right_stackedWidget.addWidget(self.about_widget)

        # with open('./static/qss/right_widget.txt') as f:
        #     right_widget_qss = f.readlines()
        #     right_widget_qss =''.join(right_widget_qss).strip('\n')
        # self.right_widget.setStyleSheet(right_widget_qss)
        # load_qss_from_txt(self.right_widget, './static/qss/about_page.txt')


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    path = './static/img/pixiv_black.png'
    app.setWindowIcon(QtGui.QIcon(QtGui.QPixmap(path)))

    gui = MainUi()
    gui.show()
    sys.exit(app.exec_())















