import time
import socket
import argparse
import threading
import os
import sys
import math
HOST = '0.0.0.0'
PORT = 47636 # ASSIGNED PORT number
receive = False
getTime = lambda: (time.time())
parser = argparse.ArgumentParser()
parser.add_argument('--server',type=str, nargs=1, required = True)
parser.add_argument('--receive',action ='store_true')
parser.add_argument('--send',type=str, nargs=2)
parser.add_argument('-s',type=int,nargs = 1) #recv SIZE
parser.add_argument('-p',type=int,nargs = 1) # PORT#
parser.add_argument('-c',type=int,nargs = 1) # no. of Threads
args = parser.parse_args()
id_ = 0
file_name =''
threads = 2 ##default Threads
parts = []
SIZE = 4096 # default size for send/recv
Receiver_Port = 47637
if args.server:
    argument =args.server[0].split(':')
    HOST = argument[0]; PORT = int(argument[1])
if args.receive:
    print('Client Set to Receive Mode')
    receive = True
if args.send:
    print('Client Set to Send Mode')
    receive = False
    id_ = args.send[0]
    file_name = args.send[1]

if args.s: #set recv/send size
    SIZE = args.s[0]
if args.p:
    Receiver_Port = args.p[0]
if args.c:
    threads = args.c[0]
    
S_ADDR = (HOST, PORT)

######################
#                    #
###Receiving SECTION##
#                    #
######################


def concurrentReceive(client,address):
    sender_data =b''
    fname = ''
    fname =client.recv(4096).decode()
    client.send(b'ack')
    length = int(client.recv(1024).decode())
    client.send(b'confirm') #send length confirmation
    order = client.recv(1024).decode()
    client.send(b'confirm') #send order confirmation
    recvSize = SIZE
    looptime = math.ceil(length/recvSize)
    if looptime <1:
        looptime = 1
    counter =0
    #order = int(order.decode())
    while (counter < looptime):
        b = client.recv(recvSize)
        sender_data+=b
        counter+=1
        if not b:
            break;
    ##Start Writing files here
    parts_name = fname+':'+ order
    f= open(parts_name,'w')
    f.write(sender_data.decode())
    f.close()
    parts.append(parts_name)
    client.close()
    #client.shutdown(socket.SHUT_RDWR)


def receiver(connection):
    thread_count = 1
    rechost = str(socket.getfqdn())
    recport = Receiver_Port
    connection.send(b'receiver')
    connection.recv(1024)
    connection.send( (rechost+':'+str(recport)).encode() )
    data = connection.recv(SIZE)
    print("Issued 'ID': ",data.decode()) 
    con =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    adr = (rechost,recport)
    con.bind(adr)
    con.listen(10)
    #file check
    client, address = con.accept()
    files = client.recv(1024).decode()
    if (os.path.isfile(files)): 
        client.send(b'exists')
    else:
        client.send(b'no')
        thread_count = int( client.recv(1024).decode() )
        client.send(b'ack')
        print ('Threads=', thread_count )
    client.shutdown(socket.SHUT_RDWR)
    client.close() ##end file check
    recv_data =b''
    st = getTime()
    print('Receive Started over',thread_count,'connections at time', st)
    for i in range(thread_count):    
        try:
            client, address = con.accept()
            th = HandlerThread(client,address)
            th.start()
            th.join()
        except Exception as e:
            print('Thread Error', e)
    et = getTime()
    print('Transfer ended at ', et)
    print('Total Time:', et-st)
    print('Time Including Compile: ', et-st+ compileReceived(parts, files))
    

def compileReceived(filename_array,main_file_name): ##parts: global variable that hold peer file breakdown
    cst= getTime()
    print('Compiling Files to main file named:',main_file_name,'...........')
    with open(main_file_name, 'w') as outfile:
        for file_parts in filename_array:
            with open(file_parts) as infile:
                for line in infile:
                    outfile.write(line)
    print('Files Compiled.......\nPerforming cleanUp........')
    #clean up the files
    for file_parts in filename_array:
        os.remove(file_parts)
    print('Cleanup Completed...........')
    print('Compile Time',getTime()-cst)
    return getTime()-cst

def file_check(adr,fname):
    con =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    con.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    con.connect(adr)
    print('adr:', adr)
    con.send(fname.encode())
    rec =con.recv(1024).decode()
    if rec == 'exists': ## don't run
        return False
    else:
        con.send( str(threads).encode() )
        con.recv(1024) #ack recv
        return True ##run


def sender(connection):
    connection.send(b'sender')
    connection.recv(1024)
    connection.send(id_.encode())
    data = connection.recv(SIZE)
    data = data.decode().split(':')
    adr = (data[0],int(data[1]))
    print("Issued ID: ", adr)
    connection.shutdown(socket.SHUT_RDWR)
    connection.close()
    try:
        f = open(file_name,'rb')
        f.close()
    except Exception as e:
        print('Read Fail in line 152', e)
    tup = os.stat(file_name).st_size
    return adr,file_name,tup


def pre_processing(adr,tup): #tup = fileSIze
    connections = []
    breaklist =[]
    for i in range (threads):
        con =socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        con.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        connections.append(con)
        breakpoint = math.ceil(tup/threads) ## no of threads to send
        
        breaklist.append(0)  ##breaklist = start of read/write
        for i in range(threads): ##keep adding breakpoints till eof
            breaklist.append(breakpoint)
            breakpoint += breakpoint
    return connections,breaklist,adr
    
def breaker(connections, breaklist,adr):
    for i in range (len(connections)):
        try:
            connections[i].connect(adr) ##connect to adr
            connections[i].send(file_name.encode()) #send filename
            connections[i].recv(1024)  #filename Confirmation
            connections[i].send(str(breaklist[i+1]-breaklist[i]).encode() ) #send data length  
            connections[i].recv(1024) ##recv confirmation of lenData acceptance
            connections[i].send(str(breaklist[i]).encode())#send the order[0,100...] of the file
            connections[i].recv(1024) ## recv breakpoint ack
            data = read(file_name,breaklist[i], breaklist[i+1]-breaklist[i])
            connections[i].send(data)
        except Exception as e:
            print('Read Fail in line 155', e)
        #connections[i].shutdown(socket.SHUT_RDWR)
        connections[i].close()
####
def read(filename,beginning,rd_length):
    f = open(filename,'rb')
    f.seek(beginning,0)  # beginning = breaklist[i]
    info = f.read(rd_length)
    f.close()
    return info

def write(filename,info):
    f = open(filename, 'xb')
    f.write(info)
    f.close()

def selector(boolean,connection):
    if (boolean):
        receiver(connection)
    else:
        details =sender(connection)   #details = {address, filename, filesize }
        if file_check(details[0],details[1]):
            prep = pre_processing(details[0],details[2]) #pre_pro = connecitons, breaklist, adr
            sh = SenderThread(prep[0],prep[1],prep[2])
            #breaker(prep[0],prep[1],prep[2]) #Prep And send Here
            sh.start()
            sh.join()
        else:
            print('Error:FILE EXISTS')
            

class HandlerThread(threading.Thread):
    def __init__(self,client,address):   #__bla __ <--A constructor, self = this
        """self: current thread; client,address: Instances of client and address  """
        threading.Thread.__init__(self) #function calling itself as an instance
        self.client = client
        self.address = address
    def run(self):
        #print('executing thread for client {}'.format(self.address))
        concurrentReceive(self.client,self.address)

class SenderThread(threading.Thread):
    def __init__(self,connections,chunks,address):   #__bla __ <--A constructor, self = this
        """self: current thread; client,address: Instances of client and address  """
        threading.Thread.__init__(self) #function calling itself as an instance
        self.connections = connections
        self.chunks = chunks
        self.address = address
    def run(self):
        #print('executing thread for client {}'.format(self.address))
        sh = ()
        breaker(self.connections,self.chunks,self.address)


connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.connect(S_ADDR)
selector(receive,connection)
