import socket
import json
import hashlib
import math
import time
import os

mainData = {}
host = '193.164.7.25'
port = 4000
def main():
    global mainData, host, port
    print("Server Started")

    server_socket = socket.socket()
    server_socket.bind((host, port))

    server_socket.listen(5)
    #Sınırsız döngü açarak sunucuya gelecek her bir veriyi bekliyoruz
    while True:
        conn, address = server_socket.accept()
        try:
            #1024 * 1024 büyüklüğüne kadar olan bufferleri kabul ediyoruz, veri geldiğinde ise utf-8 olarak kaydediyoruz
            data = conn.recv(1024 * 1024).decode('utf-8')
            if not data:
                continue
            #Veri geldiğinde fonksiyonumuza göndererek fonksiyonun içerisinde kontrol ediyoruz
            SocketReceive(conn, data)
            conn.close()
            continue
        except:
            print("Exception")
    print("Conn close")

def SocketReceive(conn, a):
    global mainData
    a = json.loads(a)
    #Gelen veri tipi dakikalık kayıtlar mı?
    if(a["type"] == "MinuteTimer") or a["type"] == "MinutVeTimer":
        macA = getmacup(a["mac"])
        if macA not in mainData:
            mainData[macA] = {
                "MacMD5": getmacmd5(macA),
                "WinUsername": a["win_username"],
                "LastSeen": 0,
                "LastFile": 0
            }
        userPath = "logsforusers/" + getmacmd5(macA)
        try:
            if not os.path.isdir(userPath):
                os.makedirs(userPath)
            mainData[macA]["LastSeen"] = int(GetUnixMinutes())
            if len(a["data"]) > 0:
                for x in a["data"]:
                    userPathFile = userPath + "/" + x + ".txt"
                    if not os.path.isfile(userPathFile):
                        savefile(userPathFile, a["data"][x])
                        if int(x) > mainData[macA]["LastFile"]: mainData[macA]["LastFile"] = int(x)
            savemaindata(mainData)
        except:
            print("Klasör oluşturulurken sorun oluştu.")
    #Eğerki gelen istek uygulama bağlantısı ise bilgisayar listesini iletiyoruz
    elif(a["type"] == "ApplicationConnected"):
        rd = {
            "type": "ApplicationConnected",
            "data": mainData
        }
        da = json.dumps(rd)
        conn.send(da.encode())
    #Eğerki bir bilgisayarın kayıtları isteniyor ise
    elif(a["type"] == "GetMessagesFromMac"):
        SendList = {}
        #O bilgisayarın MACID'sinin md5 şifrelenmiş ismi ile klasörde tutulan dosyaları çekiyoruz
        userPath = "logsforusers/" + getmacmd5(a["data"]["MacID"])
        dir_list = os.listdir(userPath)
        dir_list.sort()
        counter = 0
        for x in dir_list:
            #1000 Karakter limiti
            if counter < 1000:
                p = userPath + "/" + x
                file = open(p, encoding="UTF-8")
                #Belirlediğimiz diziye bu yazıları yazdırıyoruz
                SendList[x] = file.read()
                counter += len(SendList)
                file.close()
        rd = {
            "type": "GetMessagesFromMac",
            "data": SendList
        }
        #Listemizi uygulamaya iletiyoruz
        da = json.dumps(rd)
        conn.send(da.encode('utf-8'))
    else:
        print("Unknown Socket Type")
        print("User: ", conn)
        print("Data: ", a)
    return
def getmacmd5(a):
    #Bir mac adresinin md5 şifrelenmiş hali. Klasörleme için kullanıyoruz
    return hashlib.md5(a.encode().upper()).hexdigest()
def getmacup(a):
    return a.upper()
def savemaindata(m):
    #Bilgisayar listesini JSON dosyasında tutuyoruz. Bu dosyayı güncellemek için gereken kayıt etme fonksiyonu.
    return savefile('data.json', json.dumps(m))
def savefile(f, m):
    file = open(f, 'w')
    file.write(m)
    file.close()
    return
def getmaindata():
    #Başlangıçta JSON dosyamızı yüklüyoruz
    try:
        file = open('data.json')
        m = json.loads(file.read())
        file.close()
    except:
        m = {}
    return m
def GetUnixMinutes():
    return str(math.floor(int(time.time()) / 60))

if __name__ == '__main__':
    mainData = getmaindata()
    main()
