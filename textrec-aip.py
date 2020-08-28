"""
@autho: Zhou Wenqing

使用PyQt5调用百度API构建图片转文字的GUI程序
"""
import io
import sys
import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
print(os.getcwd())
import time
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from aip import AipOcr  # 导入百度API

from PIL import Image

try:
    from pynotifier import Notification
except ImportError:
    pass

class Snipper(QtWidgets.QWidget):

    sig = pyqtSignal(QPixmap) 

    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)

        self.setWindowTitle("TextRecognition")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog)

        self.setWindowState(self.windowState() | Qt.WindowFullScreen)
        self.screen = QtGui.QScreen.grabWindow(
            QtWidgets.QApplication.primaryScreen(),
            QtWidgets.QApplication.desktop().winId(),
        )
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)

        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QtWidgets.QApplication.quit()

        return super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())

        if self.start == self.end:
            return super().paintEvent(event)

        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(QtGui.QColor(255, 255, 255, 100))
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)

    def mousePressEvent(self, event):
        self.start = self.end = QtGui.QCursor.pos()
        self.update()
        
        return super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.end = QtGui.QCursor.pos()
        
        self.update()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)

        self.hide()
        QtWidgets.QApplication.processEvents()
        shot = self.screen.copy(QtCore.QRect(self.start, self.end))

        self.sig.emit(shot) # 释放信号，这是不同Qt窗口传值常用的方法
       
options = {
        'detect_direction':'true',
        'language_type':'CHN_ENG'}

# 使用QtCreator建立的ui文件路径
main_ui = "textshot.ui"
setup_ui = "idsetup.ui"
# 使用uic加载
Ui_MainWindow, QtBaseClass = uic.loadUiType(main_ui)
Ui_Setup_Dialog, QtBaseClass = uic.loadUiType(setup_ui)


class SetupWin(QDialog, Ui_Setup_Dialog):
    # 自定义信号，传输数据格式为list
    mySignal = pyqtSignal(list)

    def __init__(self):
        # SetupWin.__init__(self)
        Ui_Setup_Dialog.__init__(self)
        super().__init__()
        self.initUi()

    def initUi(self):
        self.setupUi(self)
        self.setWindowTitle("百度文字识别API设置")
        self.setWindowIcon(QIcon('./icons/setup.png'))

        self.setup_btn_ok.clicked.connect(self.update_api)
        self.setup_btn_cancel.clicked.connect(self.exitapp)
    
    def update_api(self):
 
        content = [self.setup_appid.text(),self.setup_appkey.text(),self.setup_screetkey.text()]
        self.mySignal.emit(content) # 发射信号
        self.close()

    def exitapp(self):
        self.close()

class MyApp(QMainWindow, Ui_MainWindow):
    '''
    使用PyQt5做GUI界面，调用百度文字识别API识别图片文字
    '''
    def __init__(self):
        QMainWindow.__init__(self)
        # Ui_MainWindow.__init__(self)
        # Ui_Setup_Dialog.__init__(self)
        super().__init__()

        # 手动输入百度图像处理API接口，同时取消注释
        self.APP_ID = None 
        self.API_KEY = None
        self.SECRET_KEY = None
        # self.aipOcr = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        # 初始化文字识别
        self.initUI()       # 调用自定义的UI初始化函数initUI()
        self.status = False # 状态变量，如果是打开图片来转换的，设置status为True，以区分截图时调用的图片转换函数

    def initUI(self):
        '''
        Initialize the window's UI
        '''

        self.setupUi(self)
        self.setWindowTitle("图片转文字GUI程序")
        self.setWindowIcon(QIcon("./icons/eye.png"))   # 设置图标，linux下只有任务栏会显示图标

        self.initMenuBar()      # 初始化菜单栏
        self.initToolBar()      # 初始化工具栏
        self.initButton()       # 初始化按钮
        
        self.setup_win = SetupWin()
        
        self.show()             # 显示

    def initMenuBar(self):
        '''
        初始化菜单栏
        '''
        menubar = self.menuBar()
        exitAct = QAction(QIcon('./icons/exit.png'), 'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)

        self.setupAct = QAction(QIcon('./icons/setup.png'),'设置接口参数',self)
        self.setupAct.triggered.connect(self.setup_api)

        fileMenu = menubar.addMenu('&File') # File菜单
        fileMenu.addAction(self.setupAct)
        fileMenu.addAction(exitAct)
        # 添加帮助信息
        helpAct = QAction('About',self)
        helpAct.triggered.connect(self.msg_about)

        helpMenu = menubar.addMenu('&Help')
        helpMenu.addAction(helpAct)
        

    def initToolBar(self):
        '''
        初始化工具栏
        创建一个QAction实例exitAct，然后添加到designer已经创建的默认的工具栏toolBar里面
        '''
        exitAct = QAction(QIcon('./icons/exit.png'),'Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(qApp.quit)

        self.setupAct.triggered.connect(self.setup_api)
        # self.aipOcr = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)
        self.toolBar.addAction(exitAct)
        self.toolBar.addAction(self.setupAct)

    def initButton(self):
        '''
        初始化按钮
        '''
        self.btnBrowse.clicked.connect(self.browserButton_callback) # 按下按钮调用回调函数
        self.btnBrowse.setToolTip("浏览需要转换的文件")                     # 设置提示
        #self.btnBrowse.setStyleSheet("{border-image: url(/home/kindy/Files/python/gui/pyq/play.ico);}") # 此代码没有效果
        self.btnScreen.clicked.connect(self.screenButton_callback)      # 一旦按下按钮，连接槽函数进行处理
        self.btnScreen.setToolTip("截取屏幕文字")
        self.btnConvert.clicked.connect(self.convertButton_callback)
        self.btnConvert.setToolTip("转换图片中的文字")

    def browserButton_callback(self):
        '''
        使用QFileDialog打开文件管理器
        '''
        global img_path    # 设置全局
        self.status = True
        img_path, filetype = QFileDialog.getOpenFileName(self,
                                    "选取图片文件",
                                    "/home/kindy/图片",
                                    "All Files (*);;Music Files (*.png)")   #设置文件扩展名过滤,注意用双分号间隔
        self.filePath.setText(img_path)

    def screenButton_callback(self):
        '''
        打开截图，点击对勾号会自动保存在目录"../temp/temp.png"
        '''

        self.snipper = Snipper()
        self.snipper.sig.connect(self.process_shot) # 连接信号与槽
        self.snipper.show()

    def convertButton_callback(self):
        '''
        调用百度API进行文字识别
        '''
        start = time.time()
        text = ''
        
        res = self.aipOcr.webImage(self.getImageBytes(img_path))

        if 'words_result' in res:
            txt=res['words_result']
            for i in range(len(txt)):
                text += (str(txt[i]['words'])+ '\n')
                self.ocrtext.setPlainText(text)
            # print(text)
        else:
            print("识别出错！")
            # print(res)

        end = time.time()
        self.ocrtext.setStatusTip(r"图片文字转换时间：%.2fs"%(end-start))

    def process_shot(self, shot):
        start = time.time()
        text = ''

        buffer = QtCore.QBuffer()
        buffer.open(QtCore.QBuffer.ReadWrite)
        shot.save(buffer, "PNG")
        
        img_bytes = io.BytesIO(buffer.data()).read()
        res = self.aipOcr.webImage(img_bytes)

        if 'words_result' in res:
            txt=res['words_result']
            for i in range(len(txt)):
                text += (str(txt[i]['words'])+ '\n')
                self.ocrtext.setPlainText(text)
            # print(text)
        else:
            print("识别出错！")
            # print(res)

        end = time.time()
        self.ocrtext.setStatusTip(r"图片文字转换时间：%.2fs"%(end-start))

    def getImageBytes(self, filename):
        with open(filename,'rb') as fp:
            return fp.read()

    def setup_api(self):
 
        self.setup_win.mySignal.connect(self.update_api)
        self.setup_win.show()

    def update_api(self, connect):
        # QMessageBox.about(self, "Title", connect[1])
        self.APP_ID = connect[0]
        self.API_KEY =  connect[1]
        self.SECRET_KEY = connect[2]
        self.aipOcr = AipOcr(self.APP_ID, self.API_KEY, self.SECRET_KEY)

    def msg_about(self):
        # QMessageBox.about(self, "Title", "Message")
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MyApp()
    sys.exit(app.exec_())
