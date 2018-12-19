import socket
import argparse
import threading
import os
import sys
import math
HOST = '0.0.0.0'
PORT = 47636 # ASSIGNED PORT number
receive = False
parser = argparse.ArgumentParser()
parser.add_argument('--server',type=str, nargs=1)
parser.add_argument('--receive',action ='store_true')
parser.add_argument('--send',type=str, nargs=2)
args = parser.parse_args()
id_ = 0
file_name =''
threads = 2
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
S_ADDR = (HOST, PORT)

######################
#                    #
###Receiving SECTION##
#                    #
######################
parts = []
def receiver(connection):
    rechost = str(socket.getfqdn())
    recport = 47637
    connection.send(b'receiver')
    connection.recv(1024)
    connection.send( (rechost+':'+str(recport)).encode() )
    data = connection.recv(4096)
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
    client.shutdown(socket.SHUT_RDWR)
    client.close() ##end file check
    recv_data =b''
    running_threads = 1
    while (running_threads <threads):
        try:
            client, address = con.accept()
            th = HandlerThread(client,address)
            th.start()
            print('Out if Thread loops', running_threads)
            running_threads+=1
        except Exception as e:
            print('No more connections')
            break;
    print('Finally Out of while')
    con.shutdown(socket.SHUT_RDWR)
    compileReceived(parts, files) #parts = list files = filename
    con.close()
    return 

def concurrentReceive(client,address):
    sender_data =b''
    fname = ''
    fname =client.recv(4096).decode()
    client.send(b'ack')
    length = int(client.recv(1024).decode())
    client.send(b'confirm') #send length confirmation
    order = client.recv(1024)
    client.send(b'confirm') #send order confirmation 
    recvSize = 4096
    looptime = length/recvSize
    if looptime <1:
        looptime = 1
    counter =0
    order = int( order.decode())
    while (counter < looptime):
        b = client.recv(recvSize)
        sender_data+=b
        counter+=1
        if not b:
            break;
    ##Start Writing files here
    print('Order', order ,' End', order+length)
    parts_name = fname+':'+ str(order)
    parts.append(parts_name)
    f= open(parts_name,'w')
    f.write(sender_data.decode())
    f.close()
    parts.append(parts_name)
    print('THREAD : PART NAMES',parts,'\n\n')
    client.close();
    #client.shutdown(socket.SHUT_RDWR) 


def compileReceived(filename_array,main_file_name): ##parts: global variable that hold peer file breakdown
    print('INSIDE COMPILE RECEIVED')
    print ('FileName Array:', filename_array)
    print(main_file_name)
    with open(main_file_name, 'w') as outfile:
        for file_parts in filename_array:
            with open(file_parts) as infile:
                for line in infile:
                    outfile.write(line)
    #clean up the files
    for file_parts in filename_array:
        os.remove(file_parts)


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
        return True ##run


def sender(connection):
    connection.send(b'sender')
    connection.recv(1024)
    connection.send(id_.encode())
    data = connection.recv(4096)
    data = data.decode().split(':')
    adr = (data[0],int(data[1]))
    print("Issued ID: ", adr)
    connection.shutdown(socket.SHUT_RDWR)
    connection.close()
    try:
        f = open(file_name,'rb')
        f.close()
    except Exception as e:
        print('Read Fail in line 121', e)
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
    print('Inside read:', beginning,rd_length)
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
            breaker(prep[0],prep[1],prep[2]) #Prep here
        else:
            print('Error:FILE EXISTS')
                
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

class HandlerThread(threading.Thread):
    def __init__(self,client,address):   #__bla __ <--A constructor, self = this
        """self: current thread; client,address: Instances of client and address  """
        threading.Thread.__init__(self) #function calling itself as an instance
        self.client = client
        self.address = address
        self.is_running = True

    def stop(self):
        self.is_running = False

    def run(self):
        while(self.is_running):
            print('executing thread for client {}'.format(self.address))
            concurrentReceive(self.client,self.address)
            self.stop()


connection.connect(S_ADDR)
selector(receive,connection)
