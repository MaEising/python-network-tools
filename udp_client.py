import socket

target_host = "www.haveibeenpwned.com"
target_port = 80

# create a socket object
client = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)


# send some data
client.sendto(b'AAABBBCCC',(target_host,target_port))

# receive some data
data, addr = client.recvfrom(4096)

print(data.decode())
client.close()

