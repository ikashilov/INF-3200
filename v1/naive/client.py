import sys
import socket

SERVER_SHUT_DOWN = '9/11'

class Client:

    def __init__(self, port_num=5000):

        self.host = socket.gethostname()
        self.port = port_num

        self.client_socket = socket.socket()

    def run(self):

        try:
            self.client_socket.connect((self.host, self.port))
        except:
            print('Cannot connect to a server. Check the port number or either it has been runned')
            exit()

        try:
            while True:
                message = raw_input(" -> ") 

                self.client_socket.send(message.encode()) 
                data = self.client_socket.recv(1024).decode() 

                if data == SERVER_SHUT_DOWN:
                    print('Server shuted down. Quiting')
                    break
                else:
                    print('Received from server: ' + data)

        except KeyboardInterrupt:
            print('\nInterrupted')

        self.client_socket.close() 



if __name__ == '__main__':

    PORT = int(sys.argv[1])
    client1 = Client(PORT).run()
