# Form implementation generated from reading ui file 'day_schedule.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_DaySchedule(object):
    def setupUi(self, DaySchedule):
        DaySchedule.setObjectName("DaySchedule")
        DaySchedule.resize(333, 726)
        self.verticalLayout = QtWidgets.QVBoxLayout(DaySchedule)
        self.verticalLayout.setObjectName("verticalLayout")
        self.gb_d_sched = QtWidgets.QGroupBox(parent=DaySchedule)
        self.gb_d_sched.setObjectName("gb_d_sched")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.gb_d_sched)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableView = QtWidgets.QTableView(parent=self.gb_d_sched)
        self.tableView.setObjectName("tableView")
        self.verticalLayout_2.addWidget(self.tableView)
        self.verticalLayout.addWidget(self.gb_d_sched)
        self.gb_d_freq = QtWidgets.QGroupBox(parent=DaySchedule)
        self.gb_d_freq.setObjectName("gb_d_freq")
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.gb_d_freq)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label = QtWidgets.QLabel(parent=self.gb_d_freq)
        self.label.setObjectName("label")
        self.horizontalLayout.addWidget(self.label)
        self.horizontalSlider = QtWidgets.QSlider(parent=self.gb_d_freq)
        self.horizontalSlider.setMinimum(0)
        self.horizontalSlider.setMaximum(28)
        self.horizontalSlider.setProperty("value", 7)
        self.horizontalSlider.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalSlider.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.horizontalSlider.setTickInterval(1)
        self.horizontalSlider.setObjectName("horizontalSlider")
        self.horizontalLayout.addWidget(self.horizontalSlider)
        self.label_2 = QtWidgets.QLabel(parent=self.gb_d_freq)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout.addWidget(self.gb_d_freq)
        self.gb_d_dur = QtWidgets.QGroupBox(parent=DaySchedule)
        self.gb_d_dur.setObjectName("gb_d_dur")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(self.gb_d_dur)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_3 = QtWidgets.QLabel(parent=self.gb_d_dur)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_2.addWidget(self.label_3)
        self.horizontalSlider_2 = QtWidgets.QSlider(parent=self.gb_d_dur)
        self.horizontalSlider_2.setMinimum(1)
        self.horizontalSlider_2.setMaximum(60)
        self.horizontalSlider_2.setProperty("value", 10)
        self.horizontalSlider_2.setOrientation(QtCore.Qt.Orientation.Horizontal)
        self.horizontalSlider_2.setTickPosition(QtWidgets.QSlider.TickPosition.TicksAbove)
        self.horizontalSlider_2.setTickInterval(1)
        self.horizontalSlider_2.setObjectName("horizontalSlider_2")
        self.horizontalLayout_2.addWidget(self.horizontalSlider_2)
        self.label_4 = QtWidgets.QLabel(parent=self.gb_d_dur)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout_2.addWidget(self.label_4)
        self.verticalLayout.addWidget(self.gb_d_dur)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.label_7 = QtWidgets.QLabel(parent=DaySchedule)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_3.addWidget(self.label_7)
        self.timeEdit = QtWidgets.QTimeEdit(parent=DaySchedule)
        self.timeEdit.setObjectName("timeEdit")
        self.horizontalLayout_3.addWidget(self.timeEdit)
        self.line_2 = QtWidgets.QFrame(parent=DaySchedule)
        self.line_2.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout_3.addWidget(self.line_2)
        self.label_8 = QtWidgets.QLabel(parent=DaySchedule)
        self.label_8.setObjectName("label_8")
        self.horizontalLayout_3.addWidget(self.label_8)
        self.label_9 = QtWidgets.QLabel(parent=DaySchedule)
        self.label_9.setObjectName("label_9")
        self.horizontalLayout_3.addWidget(self.label_9)
        self.line_3 = QtWidgets.QFrame(parent=DaySchedule)
        self.line_3.setFrameShape(QtWidgets.QFrame.Shape.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_3.setObjectName("line_3")
        self.horizontalLayout_3.addWidget(self.line_3)
        self.label_10 = QtWidgets.QLabel(parent=DaySchedule)
        self.label_10.setObjectName("label_10")
        self.horizontalLayout_3.addWidget(self.label_10)
        self.label_11 = QtWidgets.QLabel(parent=DaySchedule)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_3.addWidget(self.label_11)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        self.line = QtWidgets.QFrame(parent=DaySchedule)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.verticalLayout.addWidget(self.line)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.pushButton = QtWidgets.QPushButton(parent=DaySchedule)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout_4.addWidget(self.pushButton)
        self.pushButton_2 = QtWidgets.QPushButton(parent=DaySchedule)
        self.pushButton_2.setObjectName("pushButton_2")
        self.horizontalLayout_4.addWidget(self.pushButton_2)
        self.verticalLayout.addLayout(self.horizontalLayout_4)

        self.retranslateUi(DaySchedule)
        QtCore.QMetaObject.connectSlotsByName(DaySchedule)

    def retranslateUi(self, DaySchedule):
        _translate = QtCore.QCoreApplication.translate
        DaySchedule.setWindowTitle(_translate("DaySchedule", "Day Schedule"))
        self.gb_d_sched.setTitle(_translate("DaySchedule", "Schedule"))
        self.gb_d_freq.setTitle(_translate("DaySchedule", "Period"))
        self.label.setText(_translate("DaySchedule", "0"))
        self.label_2.setText(_translate("DaySchedule", "28 days"))
        self.gb_d_dur.setTitle(_translate("DaySchedule", "Duration"))
        self.label_3.setText(_translate("DaySchedule", "1"))
        self.label_4.setText(_translate("DaySchedule", "60 mins"))
        self.label_7.setText(_translate("DaySchedule", "Time:"))
        self.label_8.setText(_translate("DaySchedule", "Period:"))
        self.label_9.setText(_translate("DaySchedule", "28 days"))
        self.label_10.setText(_translate("DaySchedule", "Duration:"))
        self.label_11.setText(_translate("DaySchedule", "60 mins"))
        self.pushButton.setText(_translate("DaySchedule", "Schedule"))
        self.pushButton_2.setText(_translate("DaySchedule", "Unschedule"))
