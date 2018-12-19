FileTransfer system that can send data over connections. 
	Allows Threading [CNUM] where CNUM is the number of threads
	Allows Size specification [SIZE]


Run the server using 'python3 ftserver.py [--port PORT]'
Run receive by 'python3 ftclient.py --server HOST:PORT [-s SIZE] [-p PORT] --receive'
Run send by 'python3 ftclient.py --server HOST:PORT [-c CNUM] [-s SIZE] --send ID FILE'

'Pj03_Research.pdf' contains byte/thread optimization data

