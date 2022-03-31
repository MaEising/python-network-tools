import socket
import threading

ip = '0.0.0.0'
port = 9998

def handle_client(client_socket):
    with client_socket as sock:
        request = sock.recv(1024)
        print('Received: {}'.format(request.decode('UTF-8')))
        sock.send(b'ACK')


def main():
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.bind((ip,port))
    server.listen(5)
    print('Listening on {}:{}'.format(ip,port))

    while True:
        client, address = server.accept()
        print('Accepted Connection from {}:{}'.format(address[0],address[1]))
        client_handler = threading.Thread(target=handle_client, args=(client,))
        client_handler.start()


if __name__ == '__main__':
    main()