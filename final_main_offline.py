from PyQt5 import QtCore, QtWidgets, QtGui
from final_plotter_offline import CustomWidget
from final_plotter_offline import processing
import threading
import time
import sys
from pathlib import Path


class Ui_MainWindow(QtWidgets.QWidget):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 800)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = CustomWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(200, 60, 770, 521))
        self.widget.setObjectName("widget")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 800, 21))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setGeometry(QtCore.QRect(25, 510, 150, 50))
        self.pushButtonA = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonA.setGeometry(QtCore.QRect(25, 230, 150, 50))
        self.pushButtonPeriod = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonPeriod.setGeometry(25, 700, 150, 50)
        self.pushButtonFile = QtWidgets.QPushButton(self.centralwidget)
        self.pushButtonFile.setGeometry(QtCore.QRect(25, 50, 150, 50))
        self.pushButtonPeriod.setGeometry(25, 700, 150, 50)
        self.start = QtWidgets.QPushButton(self.centralwidget)
        self.start.setGeometry(QtCore.QRect(300, 600, 200, 50))
        self.stop = QtWidgets.QPushButton(self.centralwidget)
        self.stop.setGeometry(QtCore.QRect(700, 600, 200, 50))
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(400, 700, 400, 50))
        self.label.setFont(QtGui.QFont("Arial", 14, QtGui.QFont.Black))
        self.N = 5
        self.a = 0.88
        self.period = 0
        self.filepath = "60_bpm_no_noise.txt"
        self.heart_rate = "Not measured"
        self.start_program_flag = False
        self.stop_program_flag = False

        self.retranslateUi(MainWindow)

    def set_text_label(self):
        self.label.setText(f"Heart rate: {self.heart_rate}")

    def input_dialog(self):
        parameter, done = QtWidgets.QInputDialog.getInt(
            self, 'Input Dialog', 'Enter N parameter:')
        if done:
            if parameter > 0 and parameter < 11:
                self.N = parameter
            else:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText('Value must be positive and no more than 10')
                msg.setWindowTitle("Error")
                msg.exec_()

    def input_dialog_a(self):
        parameter, done = QtWidgets.QInputDialog.getDouble(
            self, 'Input Dialog', 'Enter a parameter:')
        if done:
            if parameter > 0 and parameter < 1:
                self.a = parameter
            else:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText('Value must be between 0 and 1')
                msg.setWindowTitle("Error")
                msg.exec_()

    def input_dialog_period(self):
        parameter, done = QtWidgets.QInputDialog.getInt(
            self, 'Input Dialog', 'Enter averaging periods:')
        if done:
            if parameter >= 0:
                self.period = parameter
            else:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText('Number of periods must be positive')
                msg.setWindowTitle("Error")
                msg.exec_()

    def input_dialog_file(self):
        parameter, done = QtWidgets.QInputDialog.getText(
            self, 'Input Dialog', 'Enter file directory:')
        if done:
            path = Path(parameter)
            if path.is_file():
                self.filepath = parameter
            else:
                msg = QtWidgets.QMessageBox()
                msg.setIcon(QtWidgets.QMessageBox.Critical)
                msg.setText("Error")
                msg.setInformativeText('Invalid file path')
                msg.setWindowTitle("Error")
                msg.exec_()

    def start_program(self):
        self.start_program_flag = True
        time.sleep(1)
        self.widget.start_plotting()

    def stop_program(self):
        self.stop_program_flag = True
        self.widget.stop_plotting()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Heart rate from ECG"))
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        MainWindow.setStyleSheet("background-color: white")
        self.pushButton.setText(_translate("MainWindow", "Enter N parameter"))
        self.pushButton.clicked.connect(self.input_dialog)
        self.pushButtonA.setText(_translate("MainWindow", "Enter a parameter"))
        self.pushButtonA.clicked.connect(self.input_dialog_a)
        self.pushButtonPeriod.setText(_translate("MainWindow", "Averaging periods"))
        self.pushButtonPeriod.clicked.connect(self.input_dialog_period)
        self.pushButtonFile.clicked.connect(self.input_dialog_file)
        self.pushButtonFile.setText(_translate("MainWindow", "Enter filename"))
        self.start.setText(_translate("MainWindow", "Start"))
        self.start.clicked.connect(self.start_program)
        self.stop.setText(_translate("MainWindow", "Stop"))
        self.stop.clicked.connect(self.stop_program)


class GUIForm(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.t = threading.currentThread()
        self.stop_data = False

    def closeEvent(self, event):
        self.stop_data = True
        self.t.do_run = False
        try:
            self.t.join()
        except RuntimeError:
            pass
        event.accept()


def thread_data(ui: Ui_MainWindow, gui: GUIForm, processing):
    while getattr(gui.t, "do_run", True):
        ui.set_text_label()
        if ui.start_program_flag:
            processing(ui.widget, ui, gui)
            ui.start_program_flag = False
        if ui.stop_program_flag:
            ui.heart_rate = "Not measured"
            ui.stop_program_flag = False


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = GUIForm()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    this_thread = threading.Thread(target=thread_data,
                                   args=(ui, MainWindow, processing))
    this_thread.start()
    MainWindow.show()
    sys.exit(app.exec_())