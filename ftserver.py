import socket
from random import randint
import threading
import argparse
####FUNCTIONS#############
ids =[]
details =[]
parser = argparse.ArgumentParser()
parser.add_argument('--port',type=str, nargs=1, required = True)
args = parser.parse_args()



def noarg(client, address):
    data = client.recv(4096)
    if data.decode() == 'receiver':
        print('Receiver Connected.Issuing Receiver ID')
        client.send(b'ack')
        data = client.recv(4096)
        id_ = str(address[1]) 
        detail = data.decode()
        ids.append(id_); details.append(detail);
        client.send(id_.encode())
    if data.decode() == 'sender':
        print('Sender Connected.Issuing Asked ID details')
        client.send(b'ack')
        inq_id = client.recv(4096)
        try:
            loc = ids.index(inq_id.decode())
            client.send(details[loc].encode())
        except Exception as e:
            print (e)
            #client.shutdown(socket.SHUT_RDWR)
            #client.close()

class HandlerThread(threading.Thread):    
    def __init__(self,client,address):   #__bla __ <--A constructor, self = this
        """self: current thread; client,address: Instances of client and address  """
        threading.Thread.__init__(self) #function calling itself as an instance
        self.client = client
        self.address = address
        
    def run(self):
        print('executing thread for client {}'.format(address) )
        noarg(client,address)
#################


HOST = '0.0.0.0'
PORT = 47636 # ASSIGNED PORT number
if args.port:
    PORT = int(args.port[0])

S_ADDR = (HOST, PORT)
connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
connection.bind(S_ADDR)
connection.listen(10)
 # Print's port Number
#print's command to connect to server

print("Current Server", socket.getfqdn() , 
      connection.getsockname()[1])

#while loop till server close
while True:
    client, address = connection.accept()
    th = HandlerThread(client,address) #create the thread
    th.start() #start automatically calls run(stuff)
