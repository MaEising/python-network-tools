# /usr/bin/env python3
import argparse
import socket
import shlex
import subprocess
import sys
import textwrap
import threading


#netcat object
class NetCat:
    def __init__(self,args,buffer=None):
        self.args = args
        self.buffer = buffer
        self.socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        #at which level to specify socket options and to allow reuse of local addresses
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)


    # entry point for managing NetCat object, call listen if setting up listener otherwise call send.
    def run(self):
        if self.args.listen:
            self.listen()
        else:
            self.send()


    def send(self):
        self.socket.connect((self.args.target,self.args.port))
        # if we have buffer send that to target first
        if self.buffer:
            self.socket.send(self.buffer)

        # try except to manually close connection if needed
        try:
            # while data is received
            while True:
                recv_len = 1
                response = ''
                while recv_len:
                    data = self.socket.recv(4096)
                    recv_len = len(data)
                    response += data.decode()
                    if recv_len < 4096:
                        break
                    if response:
                        print(response)
                        buffer = input('> ')
                        buffer += '\n'
                        self.socket.send(buffer.encode())
        except KeyboardInterrupt:
            print('User terminated')
            self.socket.close()
            sys.exit()


    def listen(self):
        self.socket.bind((self.args.target, self.args.port))
        self.socket.listen(5)
        while True:
            client_socket, _ = self.socket.accept()
            client_thread = threading.Thread(target=self.handle, args=(client_socket,))
            client_thread.start()


    def handle(self, client_socket):
        if self.args.execute:
            output = execute(self.args.execute)
            client_socket.send(output.encode())

        # if file upload: set up a loop, listen for content on listening socket and receive data until no more coming in.
        # Then write content to specified file.
        elif self.args.upload:
            file_buffer = b''
            while True:
                data = client_socket.recv(4096)
                if data:
                    file_buffer += data
                else: break

            with open(self.args.upload,'wb') as f:
                f.write(file_buffer)
            message = 'Saved file {}'.format(self.args.upload)
            client_socket.send(message.encode())

        # If shell to be created, send a prompt to sender and wait for cmd string then call execute()
        # scans for newline character to execute
        elif self.args.command:
            cmd_buffer = b''
            while True:
                try:
                    client_socket.send(b'Selfbuilt-NC: #> ')
                    while '\n' not in cmd_buffer.decode():
                        cmd_buffer += client_socket.recv(64)
                    response = execute(cmd_buffer.decode())
                    if response:
                        client_socket.send(response.encode())
                    cmd_buffer = b''
                except Exception as e:
                    print('server killed, error: {}'.format(e))
                    self.socket.close()
                    sys.exit()




# write a commandline helping function
def execute(cmd):
    cmd = cmd.strip()
    if not cmd:
        return
    output = subprocess.check_output(shlex.split(cmd),stderr=subprocess.STDOUT)
    return output.decode




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='selfbuilt netcat',
    formatter_class = argparse.RawDescriptionHelpFormatter,
    epilog = textwrap.dedent(''' Example:
        netcat.py -t 192.168.1.109 -p 4444 -l -c # command shell
        netcat.py -t 192.168.1.109 -p 4444 -l -u=mytest.txt # upload a file
        netcat.py -t 192.168.1.109 -p 4444 -l -e=\"cat /etc/passwd\ # execute command
        echo 'ABC' | ./netcat.py -t 192.168.1.109 -p 4444 -p 135 # echo text to server port 135
        netcat.py -t 192.168.1.109 -p 4444 # connect to server
    '''))
    parser.add_argument('-c', '--command', action='store_true', help='command shell')
    parser.add_argument('-e','--execute', help='execute specified command')
    parser.add_argument('-l', '--listen', action='store_true', help='listen')
    parser.add_argument('-p', '--port', type=int, default=4444, help='specified port')
    parser.add_argument('-t','--target', default='127.0.0.1', help='specified IP')
    parser.add_argument('-u','--upload',help='upload file')
    args = parser.parse_args()
    if args.listen:
        buffer = ''
    else:
        buffer = sys.stdin.read()

    nc = NetCat(args,buffer.encode())
    nc.run()