import tkinter as tk
from tkinter import *
from tkinter import ttk,filedialog,messagebox
import random
import json,os,socket,threading,binascii,time
import serial
import sys
import glob,datetime,base64

#获取可用端口
def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

coms = serial_ports()

root = Tk()

root.title('苏州奥丁电力-远程连接')

# 默认值
registerHexVal = 0
registerVal='0'
ipVal = '0.0.0.0'
portVal = '80'

# 读取配置文件
if not os.path.exists('config.txt'):
    with open('config.txt','w+') as f:
        pass
with open('config.txt','r') as f:
    line = f.readline()
    print(line)
    if len(line)>0:
        try:
            dictData = json.loads(line)
        except:
            dictData = {}
        registerHexVal = dictData['registerHex']
        registerVal = dictData['register']
        ipVal = dictData['ip']
        portVal = dictData['port']

root.resizable(width=True, height=True)
root.config(background='#EEE')
root.geometry('800x400')

# 服务器参数
# ip地址
ip = tk.StringVar()
ip.set(ipVal)
# 端口
port = tk.StringVar()
port.set(portVal)
# 注册码内容
register = tk.StringVar()
register.set(registerVal)
# 是否启用十六进制，默认开启
registerHex = tk.IntVar()
registerHex.set(registerHexVal)

serverProperties = ttk.Labelframe(root,text='服务器参数',padding=20)
serverProperties.place(relx=0.01,rely=0.01)
ttk.Label(serverProperties,text='IP:').grid(row=0,column=0,pady=5,sticky=E)
ttk.Label(serverProperties,text='端口:').grid(row=1,column=0,pady=5,sticky=E)
ttk.Label(serverProperties,text='注册码:').grid(row=2,column=0,pady=5,sticky=E)
ttk.Entry(serverProperties,textvariable = ip).grid(row=0,column=1)
ttk.Entry(serverProperties,textvariable = port).grid(row=1,column=1)
ttk.Entry(serverProperties,textvariable = register).grid(row=2,column=1)

def changeRegisterHex():
    newVal = registerHex.get()
    if(newVal == 1):
        try:
            prevRegister = int(register.get())
            register.set(hex(prevRegister)[2:])
        except:
            messagebox.showinfo(title='提示',message='请输入纯数字注册包')
    if(newVal == 0):
        prevRegister = register.get()
        register.set(eval('0x' + prevRegister))

# 连接按钮    
ttk.Checkbutton(serverProperties,text='HEX',variable=registerHex,onvalue = 1, offvalue = 0,command=changeRegisterHex).grid(row=2,column=2)

# 连接

running = False 
def save(): 
    global running
    if running:
        messagebox.showinfo(title='提示',message='运行中，请勿重复运行')
        return
    dict = {'registerHex':registerHex.get(),'register':register.get(),'ip':ip.get(),'port':port.get()}
    with open('config.txt','w+') as f:
        json.dump(dict,f)
    myThread(1,"socketThread").start()
    


exitFlag = 0
class  myThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        print ("开始socket线程：" + self.name)
        connectSocket(self.name)
        print ("退出socket线程：" + self.name)

# 读数据线程
class readDataThread(threading.Thread):
    def __init__(self, ser,beginTime,client,data):
        threading.Thread.__init__(self)
        self.ser = ser
        self.beginTime = beginTime
        self.client = client
        self.data = data

    def run(self):
        self.ser.write(self.data)
        time.sleep(0.1)
        result = self.ser.read(100)
        print(result)
        if not result:
            for i in range(10):
                # print('读取失败，尝试第{}次'.format(i))
                time.sleep(0.2)
                result = self.ser.read(100)
                if result:
                    break
        if result:
            print('read data spend:{} ,data:{}'.format((datetime.datetime.now() - self.beginTime).total_seconds(),result))
            self.client.sendall(result)
            
# 连接socket
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 

comsConnection = {}
def connectSocket(threadName):
   
    client.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
    # client.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))

    client.connect((ip.get(),int(port.get())))
    client.sendall(str.encode(register.get())) #发送注册码
    print('socket连接成功')
    global running
    running = True

    for com in coms:
        comConnect = serial.Serial(com,9600,timeout=0)
        comsConnection[com] = comConnect
        print(com + '连接成功')

    while True:
        if exitFlag:
            threadName.exit()
        data = client.recv(1024)
        if data:
            # 遍历连接的串口
            endWrite = datetime.datetime.now()
            for ser in comsConnection.values():
                readDataThread(ser,endWrite,client,data).start()
        

ttk.Button(root,text='连接',command = save).place(relx=0.93, rely=0.95, anchor=CENTER)

# 窗口关闭监听
def on_closing():
    if messagebox.askokcancel("退出", "确定退出?"):
        global exitFlag
        exitFlag = 1
        client.close()
        root.destroy()
        for ser in comsConnection.values():
            ser.close()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

