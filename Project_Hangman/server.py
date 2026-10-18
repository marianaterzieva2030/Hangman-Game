import socket
from _thread import *
import pickle

server = "192.168.1.182" # IP address here
port = 9999

socket_ = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    socket_.bind((server, port))
except socket.error as e:
    print(e)


socket_.listen()
print("Waiting for a connection, Server Started...")


def threaded_client(connection):
    connection.send(pickle.dumps("Connected")) # sending to our client
    reply = ""
    while True:
        try:
            data = connection.recv(1024)
            reply = pickle.loads(data)

            if not data:
                print("Disconnected")
                break
            else:
                print("Received:", reply)
                print("Sending:", reply)
            
            connection.sendall(pickle.dumps(reply))
        except:
            break
    
    print("Lost connection")
    connection.close()


# loop that continuously listens for connections from clients
while True:
    client_socket, addr = socket_.accept() # accept() returns a tuple (socket object, address info)
    print("Connected to:", addr)

    start_new_thread(threaded_client, (client_socket,)) # calling threaded_client with param (client_socket,)