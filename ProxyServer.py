 #Application HttpProxyServer
import socket ,threading
import sys
#define
PORT_PROXY=8888
PORT_HTTP=80
BUFF_SIZE = 8192# 10 KB
LOCALHOST="127.0.0.1"
BLACKLIST_FILE = "blacklist.conf"

#tao mot socket server
def CreateServer(host:str, port:int): 
    try:
        Server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        Server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        Server.bind((host,port))
        Server.listen(5)
    except socket.msg as error:
        print("Recieved error #%d: %s\n" % (error[0], error[1]))
        exit(0)
    return Server

#tao mot socket client
def CreateClient(host:str,post:int):
    try:
        client=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect((host,post))
    except:
        print("Dia chi khong hop le!")
        exit(0)
    return client    

#phan tich request nhan duoc tu browser roi tra ve dictonary
def parseRequest(ReqMsg:str):
    #tach dong dau
    firstline=ReqMsg.split("\r\n")[0]
    method=firstline.split(" ")[0]
    url=firstline.split(" ")[1]
    version=firstline.split(" ")[2]
    #phan tich url
    if url[0]=='/':
        protocol="http"
        path=url[1:]
    elif "http" in url:
        protocol="http"
        pos=url.find("/",7)
        path=url[pos+1:]
    else: 
        protocol="https"
        path=""
    #tach  host
    pos1=ReqMsg.find("Host: ")
    pos2=ReqMsg.find('\r',pos1)
    host=ReqMsg[pos1+6:pos2]
    #tra ve mot dictionary
    return {"method":method , 
            "protocol":  protocol,
            "host":host ,
            "path":path,
            "version":version  }

#in thong tin yeu cau tu browser
def printReqInfo(inf:dict):
    print(" Request:")
    print("   Method  :",inf["method"])
    print("   Protocol:",inf["protocol"])
    print("   Host    :",inf["host"])
    print("   Path    :",inf["path"])
    print("   Version :%s\n"%(inf["version"]))

#gui file code 403 forbidden
def Send403Code(sockfd:socket):
    data=b''
    try:
        f=open("403.html","rb")
        data=f.read()
    except: data=b'403 forbidden'
    header=b"HTTP/1.1 403 Forbidden\r\n\r\n"
    res=header+data
    sockfd.send(res)

#kiem tra xem host cua request co nam trong danh sach den hay khong
def checkBlacklist(host:str,filename:str):
    data=b''
    try:
        f = open (filename,"rb")
        data=f.read()
    except:
        print("Can't find file ",filename)
        #pass
    blacklist=data.decode("utf-8")
    if host in blacklist or LOCALHOST in host :
        return True
    return False

#doc yeu cau tu mot socket 
def readRequest(sock:socket):
    request_msg=b''
    sock.settimeout(0.5)
    try:
        request_msg=sock.recv(BUFF_SIZE)
    except socket.timeout:
        print(" Error: [Time out]!")
        return b''
    return request_msg

#doc phan hoi tu mot socket 
def readResponse(sock:socket, conn:socket):
    data = b''
    sock.settimeout(0.3)
    try:
        while 1:
            part = sock.recv(BUFF_SIZE)
            if len(part) >0:
                data += part
            else:
                break
           
            
    except socket.timeout:
        pass
        #print(" Error: [Time out]!")
    return data

 #ham xu ly chinh
def ProcessProxy(proxySocket:socket):
    #Nhan request tu phia client (browser)
    request_msg=readRequest(proxySocket)
    if request_msg==b'': 
        proxySocket.close()
        return 0

    #nhan dirtory sau khi da phan tich request
    httpReq=parseRequest(request_msg.decode())

    #kiem tra phuong thuc
    if httpReq["method"]!="GET" and   httpReq["method"]!="POST" :
        proxySocket.close()
        return 0;

    #in thong thong tin da phan tich tu thong diep len console
    printReqInfo(httpReq)

    #get host
    host=httpReq["host"]
    #lay cac host bi cam trong file blacklist.conf va kiem tra xem host bi cam hay khong
    if (checkBlacklist(host,BLACKLIST_FILE)):
        Send403Code(proxySocket)
        proxySocket.close()
        return 1

    #tao mot client ket noi den webserver
    proxyclient=CreateClient(host,PORT_HTTP)

    #gui request den Webserver
    proxyclient.send(request_msg)

    #Nhan phan hoi tu webserver sau khi gui request
    response_msg=readResponse(proxyclient,proxySocket)

    #Gui phan hoi tu webserver ve cho browser
    #print(response_msg)
    proxySocket.send(response_msg)
    #dong ket noi socket.
    proxySocket.close()
    proxyclient.close()
    return 1

#main function
#-----------------------------------main---------------------------------#
if __name__== "__main__":
    #creat socket server
    ProxyServer=CreateServer(LOCALHOST,PORT_PROXY)
    print(":------------------------------------------------------:" )
    print(":             HTTP PROXY SERVER APPLICATION            :" )
    print(":------------------------------------------------------:" )
    print( "\nHTTP Proxy listening on port: %d"%(PORT_PROXY))

    #threads.append(thread)
    while True:
        try:
            newsock,newadd = ProxyServer.accept()
            print ("Received connection from IP: %s - Port: %d:"%(newadd[0],newadd[1]))
            #xu ly da luong
            
            threadsocket=threading.Thread(target=ProcessProxy, args=(newsock,))
            threadsocket.start()
            threadsocket.join()

        except KeyboardInterrupt:
            ProxyServer.close()
            
            break
#-----------------------------------main---------------------------------#