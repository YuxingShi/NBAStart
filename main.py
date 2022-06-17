import sys

from PyQt5.QtWidgets import QApplication

from App.MainWindow import MainWindow

GLOBAL_STRUT_WIDTH = 35

if __name__ == "__main__":
    app = QApplication(sys.argv)
    size = app.globalStrut()
    size.setWidth(GLOBAL_STRUT_WIDTH)
    app.setGlobalStrut(size)

    mw = MainWindow()
    mw.setWindowTitle('NAB中文')
    mw.showNormal()
    sys.exit(app.exec_())
