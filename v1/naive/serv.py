import sys
import socket

SERVER_SHUT_DOWN = '9/11'
MAX_NUMBER_OF_CLIENTS = 3

class Node:

    def __init__(self, port_num=5000):

        self.host = socket.gethostname()
        self.port = port_num

        self.server_socket = socket.socket()  
        self.server_socket.bind((self.host, self.port))

        print('Server started at: ' + str(self.host) + ' port: ' + str(self.port))

    def redirect(self, data, addr):

        neighbour_socket = socket.socket() 
        neighbour_socket.connect((self.host, NEIGHBOUR_NODE_PORT))
        neighbour_socket.send(str([data[::-1], addr]).encode())

    def start_listen(self):

        self.server_socket.listen(MAX_NUMBER_OF_CLIENTS)

        conn, address = self.server_socket.accept()

        print("New connection from: " + str(address))
        try:
            while True:
                data = conn.recv(1024).decode()
                if not data:
                    print('No data was sended -> interrupted')
                    break

                elif str(data).isdigit():
                    # We cant do it - ask another node
                    self.redirect(data, address)
                else:
                    # Send it back
                    conn.send(data.upper().encode())

        except KeyboardInterrupt:
            conn.send(SERVER_SHUT_DOWN.encode())
            print('\nInterrupted')

        conn.close() 

if __name__ == '__main__':

    PORT = int(sys.argv[1])

    NEIGHBOUR_NODE_PORT = int(sys.argv[2])

    node1 = Node(PORT).start_listen()
