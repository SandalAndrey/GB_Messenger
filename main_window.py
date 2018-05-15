import io
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QListWidgetItem, QDialog, QVBoxLayout, QDialogButtonBox, QTextEdit, QFileDialog, QLabel, \
    QWidget, QAction, QLayout, QFrame, QSlider, QHBoxLayout
from PyQt5.QtGui import QIcon, QFont, QTextCharFormat, QPixmap, QImage
from PIL import Image, ImageDraw  # Подключим необходимые библиотеки.
from PyQt5.QtCore import QBuffer, Qt, QByteArray, QIODevice
import urllib.parse
import jim_message
from PIL.ImageQt import ImageQt
import jim_client_db as db


class MyPopup(QWidget):
    def __init__(self):
        QWidget.__init__(self)

        self.setFixedSize(160, 320)
        self.image = None
        self.client = None
        self.win = None

        vbox = QVBoxLayout(self)

        self.lbl = QLabel(self)
        # self.lbl.setScaledContents(True)
        self.lbl.setFrameShape(QFrame.Panel)
        self.lbl.setFrameShadow(QFrame.Sunken)
        self.lbl.setLineWidth(3)
        self.lbl.setFixedSize(90, 90)

        self.scaleButton = QtWidgets.QPushButton(self)
        self.scaleButton.setObjectName("scaleButton")
        self.scaleButton.setText('Масштаб')

        self.cropButton = QtWidgets.QPushButton(self)
        self.cropButton.setObjectName("cropButton")
        self.cropButton.setText('Обрезка')

        vbox.addWidget(self.scaleButton)
        vbox.addWidget(self.cropButton)
        vbox.addWidget(self.lbl)

        self.sl = QSlider(Qt.Horizontal)
        self.sl.setValue(0)
        self.sl.setTickPosition(QSlider.TicksBelow)
        self.sl.setTickInterval(5)

        self.sl.setVisible(False)

        vbox.addWidget(self.sl)

        self.okButton = QtWidgets.QPushButton(self)
        self.okButton.setAutoDefault(False)
        self.okButton.setDefault(True)
        self.okButton.setObjectName("okButton")
        self.okButton.setText('OK')

        vbox.addWidget(self.okButton)

        self.setLayout(vbox)

        self.scaleButton.clicked.connect(self.scale)
        self.cropButton.clicked.connect(self.crop)
        self.sl.valueChanged.connect(self.valuechange)
        self.okButton.clicked.connect(self.okClicked)

    def crop(self):

        if self.image:
            width, height = self.image.size

            self.sl.setVisible(True)
            self.sl.setMinimum(0)
            if height > width:
                self.sl.setMaximum(int(height * 90 / width) - 90)
            else:
                self.sl.setMaximum(int(width * 90 / height) - 90)

    def valuechange(self):
        width, height = self.image.size

        if height > width:
            scale = 90 / width
            new_image = self.image.resize((90, int(height * scale)), Image.BICUBIC)
            new_image = new_image.crop((0, int(self.sl.value()), 90, 90 + int(self.sl.value())))
        else:
            scale = 90 / height
            new_image = self.image.resize((int(width * scale), 90), Image.BICUBIC)
            new_image = new_image.crop((int(self.sl.value()), 0, 90 + int(self.sl.value()), 90))

        img_tmp = ImageQt(new_image.convert('RGBA'))
        pixmap = QPixmap.fromImage(img_tmp)

        self.lbl.setPixmap(pixmap)

    def scale(self):
        self.sl.setVisible(False)
        if self.image:
            size = (90, 90)
            new_image = self.image.resize(size, Image.BICUBIC)
            img_tmp = ImageQt(new_image.convert('RGBA'))
            pixmap = QPixmap.fromImage(img_tmp)

            self.lbl.setPixmap(pixmap)

    # def resizeEvent(self, event):
    #     self.lbl.setGeometry(QtCore.QRect(self.width() / 2 - 30, self.height() / 2 - 45, 60, 90))
    #     return super(MyPopup, self).resizeEvent(event)

    def okClicked(self):
        if self.image:
            with db.db_session:
                byte_array = QByteArray()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.WriteOnly)
                self.lbl.pixmap().save(buffer, 'PNG')

                photo = bytes(byte_array)

                if not db.Avatar.get(user=self.client.user.login):
                    _ = db.Avatar(user=self.client.user.login, photo=photo)
                else:
                    avatar = db.Avatar.get(user=self.client.user.login)
                    avatar.set(photo=photo)

            self.win.photo = photo

        self.close()

class SearchDialog(QDialog):
    def __init__(self, parent=None):
        super(SearchDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.setWindowTitle('Введите текст для поиска')
        self.setMinimumSize(222, 111)
        self.resize(222, 111)

        self.lineEdit = QtWidgets.QLineEdit(self)
        layout.addWidget(self.lineEdit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def searchText(self):
        return self.lineEdit.text()

    @staticmethod
    def getsearchText(parent=None):
        dialog = SearchDialog(parent)
        result = dialog.exec_()
        login = dialog.searchText()
        return login, result == QDialog.Accepted

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.setWindowTitle('Введите Логин')
        self.setMinimumSize(222, 111)
        self.resize(222, 111)

        self.lineEdit = QtWidgets.QLineEdit(self)
        layout.addWidget(self.lineEdit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def login(self):
        return self.lineEdit.text()

    @staticmethod
    def getLogin(parent=None):
        dialog = LoginDialog(parent)
        result = dialog.exec_()
        login = dialog.login()
        return login, result == QDialog.Accepted


class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super(PasswordDialog, self).__init__(parent)

        layout = QVBoxLayout(self)

        self.setWindowTitle('Введите Пароль')
        self.setMinimumSize(222, 111)
        self.resize(222, 111)
        self.lineEdit = QtWidgets.QLineEdit(self)
        self.lineEdit.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addWidget(self.lineEdit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            QtCore.Qt.Horizontal, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def password(self):
        return self.lineEdit.text()

    @staticmethod
    def getPassword(parent=None):
        dialog = PasswordDialog(parent)
        result = dialog.exec_()
        password = dialog.password()
        return password, result == QDialog.Accepted


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(676, 643)

        self.photo = None
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")

        self.gridLayout_3 = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.splitter = QtWidgets.QSplitter(self.centralwidget)
        self.splitter.setOrientation(QtCore.Qt.Horizontal)
        self.splitter.setObjectName("splitter")
        self.contact_list = QtWidgets.QListWidget(self.splitter)
        self.contact_list.setObjectName("contact_list")
        self.frame = QtWidgets.QFrame(self.splitter)
        self.frame.setObjectName("frame")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.frame)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.messageList = QtWidgets.QListWidget(self.frame)
        self.messageList.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.messageList.setObjectName("messageList")

        self.messageList.setWordWrap(True)
        self.messageList.setTextElideMode(QtCore.Qt.ElideLeft)

        self.gridLayout_2.addWidget(self.messageList, 1, 0, 1, 6)

        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        # self.lineEdit = QtWidgets.QLineEdit(self.frame)
        # self.lineEdit.setMinimumSize(QtCore.QSize(0, 33))
        # self.lineEdit.setObjectName("lineEdit")

        self.textEdit = QTextEdit()
        self.textEdit.setObjectName('textEdit')

        # self.gridLayout.addWidget(self.lineEdit, 0, 0, 1, 1)
        self.gridLayout.addWidget(self.textEdit, 0, 0, 1, 1)

        self.okButton = QtWidgets.QPushButton(self.frame)
        self.okButton.setAutoDefault(False)
        self.okButton.setDefault(True)
        self.okButton.setObjectName("okButton")
        self.gridLayout.addWidget(self.okButton, 0, 1, 1, 1)

        self.strongButton = QtWidgets.QPushButton(self.frame)
        self.strongButton.setAutoDefault(False)
        self.strongButton.setDefault(True)
        self.strongButton.setObjectName("strongButton")
        self.strongButton.setIcon(QtGui.QIcon(r"ico/b.jpg"))
        self.strongButton.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.strongButton, 2, 0)

        self.italicButton = QtWidgets.QPushButton(self.frame)
        self.italicButton.setAutoDefault(False)
        self.italicButton.setDefault(True)
        self.italicButton.setObjectName("italicButton")
        self.italicButton.setIcon(QtGui.QIcon(r"ico/i.jpg"))
        self.italicButton.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.italicButton, 2, 1)

        self.underButton = QtWidgets.QPushButton(self.frame)
        self.underButton.setAutoDefault(False)
        self.underButton.setDefault(True)
        self.underButton.setObjectName("underButton")
        self.underButton.setIcon(QtGui.QIcon(r"ico/u.jpg"))
        self.underButton.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.underButton, 2, 2)

        self.smile_ab = QtWidgets.QPushButton(self.frame)
        self.smile_ab.setAutoDefault(False)
        self.smile_ab.setDefault(True)
        self.smile_ab.setObjectName("smile_ab")
        self.smile_ab.setIcon(QtGui.QIcon(r"ico/ab.gif"))
        self.smile_ab.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.smile_ab, 2, 3)

        self.smile_ac = QtWidgets.QPushButton(self.frame)
        self.smile_ac.setAutoDefault(False)
        self.smile_ac.setDefault(True)
        self.smile_ac.setObjectName("smile_ac")
        self.smile_ac.setIcon(QtGui.QIcon(r"ico/ac.gif"))
        self.smile_ac.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.smile_ac, 2, 4)

        self.smile_ai = QtWidgets.QPushButton(self.frame)
        self.smile_ai.setAutoDefault(False)
        self.smile_ai.setDefault(True)
        self.smile_ai.setObjectName("smile_ai")
        self.smile_ai.setIcon(QtGui.QIcon(r"ico/ai.gif"))
        self.smile_ai.setIconSize(QtCore.QSize(24, 24))
        self.gridLayout_2.addWidget(self.smile_ai, 2, 5)

        self.gridLayout_2.addLayout(self.gridLayout, 3, 0, 1, 6)

        self.gridLayout_3.addWidget(self.splitter, 0, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 676, 21))
        self.menubar.setObjectName("menubar")
        self.menu = QtWidgets.QMenu(self.menubar)
        self.menu.setObjectName("menu")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolBar = QtWidgets.QToolBar(MainWindow)
        self.toolBar.setObjectName("toolBar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolBar)

        self.action_image = QtWidgets.QAction(MainWindow)
        self.action_image.setObjectName("action_image")

        self.action_search = QtWidgets.QAction(MainWindow)
        self.action_search.setObjectName("action_search")

        self.action_exit = QtWidgets.QAction(MainWindow)
        icon = QtGui.QIcon()
        icon.addPixmap(
            QtGui.QPixmap(r"ico/exit.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.action_exit.setIcon(icon)
        self.action_exit.setIconText("Выход")
        font = QtGui.QFont()
        font.setFamily("Verdana")
        font.setPointSize(12)
        self.action_exit.setFont(font)
        self.action_exit.setObjectName("action_exit")

        self.menu.addAction(self.action_image)
        self.menu.addSeparator()

        self.menu.addAction(self.action_search)
        self.menu.addSeparator()

        self.menu.addAction(self.action_exit)
        self.menubar.addAction(self.menu.menuAction())
        self.toolBar.addAction(self.action_exit)

        self.retranslateUi(MainWindow)

        self.action_exit.triggered.connect(MainWindow.close)
        self.action_image.triggered.connect(self.load_photo)
        self.action_search.triggered.connect(self.actionsearch)

        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        # self.lineEdit.setToolTip(
        #     _translate("MainWindow", "<html><head/><body><p align=\"center\">Введите сообщение</p></body></html>"))
        # self.lineEdit.setStatusTip(_translate("MainWindow", "Введите сообщение"))
        self.okButton.setText(_translate("MainWindow", "OK"))
        self.okButton.setShortcut(_translate("MainWindow", "Ctrl+Return, Ctrl+Enter"))
        self.menu.setTitle(_translate("MainWindow", "Команды"))
        self.toolBar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.action_image.setText(_translate("MainWindow", "Загрузить фото"))
        self.action_search.setText(_translate("MainWindow", "Поиск сообщений"))
        self.action_exit.setText(_translate("MainWindow", "Выход"))
        self.action_exit.setToolTip(_translate("MainWindow", "Выход"))
        self.action_exit.setShortcut(_translate("MainWindow", "Ctrl+Q"))

    def show_List(self):
        pass

    def load_photo(self):
        fname = QFileDialog.getOpenFileName(self.centralwidget, 'Open file', '', 'Images (*.png *.xpm *.jpg)')[0]

        if fname:
            image = Image.open(fname)

            draw = ImageDraw.Draw(image)
            img_tmp = ImageQt(image.convert('RGBA'))

            pixmap = QPixmap.fromImage(img_tmp)
            # pixmap = QPixmap(fname)

            self.w = MyPopup()
            self.w.image = image
            self.w.client = self.graphic_ui.client
            self.w.win = self

            # self.w.setGeometry(QtCore.QRect(100, 100, 400, 300))

            self.w.show()

            self.w.lbl.setPixmap(pixmap)
            # self.w.lbl.resize(60, 90)

    def on_strongButton_clicked(self):
        cursor = self.textEdit.textCursor()
        text = cursor.selectedText()

        frmt = QTextCharFormat()
        frmt.setFontWeight(QFont.Bold)
        cursor.mergeCharFormat(frmt)
        # self.textEdit.insertHtml('<b>%s</b>' % text)

    def on_italicButton_clicked(self):
        cursor = self.textEdit.textCursor()
        frmt = QTextCharFormat()
        frmt.setFontItalic(True)
        cursor.mergeCharFormat(frmt)

    def on_underButton_clicked(self):
        cursor = self.textEdit.textCursor()
        frmt = QTextCharFormat()
        frmt.setFontUnderline(True)
        cursor.mergeCharFormat(frmt)

    def on_smileAB_clicked(self):
        self.textEdit.insertHtml('<img src="ico/ab.gif" />')

    def on_smileAC_clicked(self):
        self.textEdit.insertHtml('<img src="ico/ac.gif" />')

    def on_smileAI_clicked(self):
        self.textEdit.insertHtml('<img src="ico/ai.gif" />')

    def on_pushButtonOK_clicked(self):

        # inp = self.lineEdit.text()
        inp_txt = self.textEdit.toPlainText()
        inp_html = self.textEdit.toHtml()

        if inp_txt:
            if not self.contact_list.row(self.contact_list.currentItem()):
                to = '*'
            else:
                to = self.contact_list.currentItem().text()

            # item = QListWidgetItem(inp, self.messageList)
            # item.setTextAlignment(QtCore.Qt.AlignRight)
            # self.messageList.addItem(item)

            widgetItem = QListWidgetItem()

            widgetLayout = QHBoxLayout()

            widget = QWidget()

            html = inp_html
            # html = '<div>1111</div><div>' + inp_html + '</div>'
            widgetText = QLabel(html)
            widgetPhoto = QLabel()

            photo_width = 5

            if self.photo:
                pixmap = QPixmap()
                pixmap.loadFromData(self.photo, "PNG")

                widgetPhoto.setFixedSize(48, 48)
                widgetPhoto.setScaledContents(True)
                widgetPhoto.setPixmap(pixmap)
                widgetLayout.addWidget(widgetPhoto)

                photo_width = 48

            widgetText.width = self.messageList.frameGeometry().width() - photo_width
            widgetLayout.addWidget(widgetText)
            widgetLayout.setSizeConstraint(QLayout.SetFixedSize)
            widget.setLayout(widgetLayout)

            self.messageList.addItem(widgetItem)
            widgetItem.setSizeHint(widget.sizeHint())
            self.messageList.setItemWidget(widgetItem, widget)

            self.messageList.scrollToBottom()

            self.graphic_ui.client._send_message(inp_txt, msg_to=to)

        # self.lineEdit.clear()
        self.textEdit.clear()

    def actionsearch(self):
        text, ok = SearchDialog.getsearchText()
        if ok:
            msg = jim_message.JIMMessage('search_msg', text)
            self.graphic_ui.client.send(str(msg).encode('utf-8'))

    def login(self):
        return LoginDialog.getLogin()

    def password(self):
        return PasswordDialog.getPassword()
