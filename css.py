CSS = """
 QWidget {
     background: QLinearGradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #eef, stop: 1 #ccf);
     }
 QPushButton {
     color: white;
     background-color: QLinearGradient( x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #88d, stop: 0.1 #99e, stop: 0.49 #77c, stop: 0.5 #66b, stop: 1 #77c);
     border-width: 1px;
     border-color: #339;
     border-style: solid;
     border-radius: 7;
     padding: 3px;
     padding-left: 5px;
     padding-right: 5px;
     min-width: 22px;
     max-width: 100px;
     }
 QLineEdit {
     padding: 1px;
     border-style: solid;
     border: 2px solid gray;
     border-radius: 8px;
     text-align: center
     }
 QTextEdit {
     padding: 1px;
     border-style: solid;
     border: 2px solid gray;
     border-radius: 8px;
     text-align: center
     }
 QListWidget {
     padding: 1px;
     border-style: solid;
     border: 2px solid gray;
     border-radius: 8px;
     text-align: center
     }
 QListWidget[objectName="messageList"]::item {
     border: 1px solid #339;
     border-radius: 6px;
     }
 QLabel {
    background: none;
    height: 13px;
    font-size: 15px;
    }
 """
