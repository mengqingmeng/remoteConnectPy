import tkinter as tk
from tkinter import *
from tkinter import ttk,filedialog,messagebox
import random
import json,os,socket,threading,binascii,time,logging
import serial
import sys
import glob,datetime,base64
# 用来标记socket线程的连接状态
running = False 

exitFlag = 0

# 配置log输出
logging.basicConfig(filename='app.log',format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d-%H-%M-%S')

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

# 可用串口
coms = serial_ports()

def changeRegisterHex():
    newVal = registerHex.get()
    if(newVal == 1):
        try:
            prevRegister = int(register.get())
            register.set(hex(prevRegister)[2:])
        except:
            logging.warning("输入注册包格式不正确："+register.get())
            messagebox.showinfo(title='提示',message='请输入纯数字注册包')
    if(newVal == 0):
        prevRegister = register.get()
        register.set(eval('0x' + prevRegister))
# socket 线程
class  myThread(threading.Thread):
    def __init__(self, threadID, name):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
    def run(self):
        logging.info ("开始socket线程：" + self.name)
        try:
            connectSocket(self,self.name)
        except:
            logging.error('socket连接异常')
            status.set(-2)        
        logging.info("退出socket线程：" + self.name)

# 读数据 线程
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
            logging.info('read data spend:{} ,data:{}'.format((datetime.datetime.now() - self.beginTime).total_seconds(),result))
            self.client.sendall(result)

class sendSocketHeart(threading.Thread):
    def __init__(self,client):
        threading.Thread.__init__(self)
        global heartBeatContent
        global heartBeatTime
        self.heartBeatContent = heartBeatContent.get()
        self.heartBeatTime = heartBeatTime.get()
        self.client = client
    def run(self):
        while not exitFlag:
            logging.info('发送心跳：' + self.heartBeatContent)
            time.sleep(self.heartBeatTime)
            try:
                self.client.sendall(self.heartBeatContent.encode('utf-8'))
            except:
                logging.error("发送心跳失败")
                global status
                status.set(-2) # 异常

# 连接socket
client = socket.socket(socket.AF_INET,socket.SOCK_STREAM) 

# 端口-连接 dict
comsConnection = {}

# 连接socket
def connectSocket(self,threadName):
   
    client.setsockopt(socket.SOL_SOCKET,socket.SO_KEEPALIVE,1)
    # client.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 10000, 3000))
    try:
        client.connect((ip.get(),int(port.get())))
        client.sendall(register.get().encode()) #发送注册码
    except:
        logging.error('socket连接服务器失败')
        client.close()
    

    # 开启心跳线程
    global useHeartBeat 
    if useHeartBeat.get():
        sendSocketHeart(client).start()
    status.set(1)
    logging.info('socket连接成功')
    global running
    running = True

    for com in coms:
        comConnect = serial.Serial(com,baudrateCmb.get(),timeout=0)
        comsConnection[com] = comConnect
        logging.info(com + '打开成功')
    while True:
        if exitFlag:
            running = False
            status.set(-1)
            logging.info('退出socket线程')
            client.close()
            break
        try:
            data = client.recv(1024)
        except:     
            logging.error('获取socket数据失败')
            status.set(-2) # 异常
            exitFlag = 1   
        if data:
            # 遍历连接的串口
            endWrite = datetime.datetime.now()
            for ser in comsConnection.values():
                readDataThread(ser,endWrite,client,data).start()

root = Tk()

root.title('苏州奥丁电力-远程连接')

# 默认值
registerHexVal = 0
registerVal='0'
ipVal = '0.0.0.0'
portVal = '80'
baudrates=(50, 75, 110, 134, 150, 200, 300, 600, 1200, 1800, 2400, 4800, 9600, 19200, 38400, 57600, 115200)
heartBeatTimeVal = 60
useHeartBeatVal = True
heartBeatContentVal = '0'
statusVal = -1
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
        # registerHexVal = dictData['registerHex']
        registerVal = dictData['register']
        ipVal = dictData['ip']
        portVal = dictData['port']
        useHeartBeatVal = dictData['useHeartBeat']
        heartBeatContentVal = dictData['heartBeatContent']
        heartBeatTimeVal = dictData['heartBeatTime']
        statusVal = dictData['status']

root.resizable(width=False, height=False)
root.config(background='#EEE')
root.geometry('600x400')

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
serverProperties.grid(row=0,column=0,sticky=N,padx=10,pady=10)
ttk.Label(serverProperties,text='IP:').grid(row=0,column=0,pady=5,sticky=E)
ttk.Label(serverProperties,text='端口:').grid(row=1,column=0,pady=5,sticky=E)
ttk.Label(serverProperties,text='注册码:').grid(row=2,column=0,pady=5,sticky=E)
ttk.Label(serverProperties,text='波特率:').grid(row=3   ,column=0,pady=5,sticky=E)
ttk.Entry(serverProperties,textvariable = ip).grid(row=0,column=1,sticky=W)
ttk.Entry(serverProperties,textvariable = port).grid(row=1,column=1,sticky=W)
ttk.Entry(serverProperties,textvariable = register).grid(row=2,column=1,sticky=W)
baudrateCmb = ttk.Combobox(serverProperties,values=baudrates)
baudrateCmb.grid(row=3,column=1)
baudrateCmb.current(12) 
# 注册码 启用HEX
# ttk.Checkbutton(serverProperties,text='HEX',variable=registerHex,onvalue = 1, offvalue = 0,command=changeRegisterHex).grid(row=2,column=2)

# 心跳
heartBeatContent = tk.StringVar()
heartBeatContent.set(heartBeatContentVal)
heartBeatTime = tk.IntVar()
heartBeatTime.set(heartBeatTimeVal)
# 是否启用心跳，默认开启
useHeartBeat = tk.IntVar()
useHeartBeat.set(useHeartBeatVal)
heartBeatProperties = ttk.Labelframe(root,text='心跳',padding=10)
heartBeatProperties.grid(row=0,column=1,sticky=N,rowspan=4,padx=10,pady=10)
ttk.Checkbutton(heartBeatProperties,text='启用',variable=useHeartBeat,onvalue = 1, offvalue = 0).grid(row=0,column=0)

ttk.Label(heartBeatProperties,text='心跳内容:').grid(row=1,column=0,pady=5,sticky=E)
ttk.Label(heartBeatProperties,text='心跳时间:').grid(row=2,column=0,pady=5,sticky=E)
ttk.Entry(heartBeatProperties,textvariable = heartBeatContent).grid(row=1,column=1,sticky=W)
ttk.Entry(heartBeatProperties,textvariable = heartBeatTime).grid(row=2,column=1,sticky=W)

# 状态
global status
status = tk.IntVar()
status.set(statusVal)
statusLabelFrame = ttk.Labelframe(root,text='状态',padding=10)
statusLabelFrame.grid(row=1,column=0,sticky=W,rowspan=4,padx=10,pady=10)
ttk.Radiobutton(statusLabelFrame,text='连接',variable=status,value=1,state='disabled').grid(row=0,column=0,sticky=W)
ttk.Radiobutton(statusLabelFrame,text='未连接',variable=status,value=-1,state='disabled').grid(row=1,column=0,sticky=W)
ttk.Radiobutton(statusLabelFrame,text='异常',variable=status,value=-2,state='disabled').grid(row=2,column=0,sticky=W)

# 保存-连接
def save(): 
    global running
    if running:
        messagebox.showinfo(title='提示',message='运行中，请勿重复运行')
        return
    dict = {'register':register.get(),'ip':ip.get(),
    'port':port.get(),'useHeartBeat':useHeartBeat.get(),'heartBeatContent':heartBeatContent.get(),'heartBeatTime':heartBeatTime.get(),'status':status.get()}
    with open('config.txt','w+') as f:
        json.dump(dict,f)
    myThread(1,"socketThread").start()

ttk.Button(root,text='连接',command = save).place(relx=0.9, rely=0.9, anchor=CENTER)

# 窗口关闭监听
def on_closing():
    if messagebox.askokcancel("退出", "确定退出?"):
        exitFlag = 1
        client.close()
        root.destroy()
        logging.info('退出窗口，关闭coms')
        for ser in comsConnection.values():
            ser.close()
        sys.exit()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()

