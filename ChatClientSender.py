import sys
from socket import *
import zlib
import time

MAX_MSG_SIZE = 2048
SERVER = None
PORT = None
inputfile = None
outputfile = None
sender = "Sender1"
receiver = "Rec1"
seqNum = 0

if len(sys.argv) == 5:
    SERVER = sys.argv[2]
    PORT = int(sys.argv[4])
elif len(sys.argv) == 8:
    SERVER = sys.argv[2]
    PORT = int(sys.argv[4])
    inputfile = sys.argv[6]
    outputfile = sys.argv[7]


def make_packet(input, seq, isFile, output, isAck):
    header = "{}\n{}\n{}\n{}\n".format(str(seq), str(isFile), str(output), str(isAck))
    packet = header.encode() + input
    checksum = zlib.crc32(packet)
    finalPacket = str(checksum).encode() + b"\n" + packet
    return finalPacket

def is_safe(packet):
    newline = packet.find(b"\n")
    if newline == -1:
        return False
    else:
        act_checksum = packet[:newline]
        new_checksum = zlib.crc32(packet[newline + 1:])
        if act_checksum == str(new_checksum).encode():
            return True
        else:
            return False


def is_ack(packet, currentSeq):
    if is_safe(packet) == False:
        return False
    else:
        msgArr = packet.split(b"\n")
        if int(msgArr[4].decode()) == currentSeq:
            return True
        else:
            return False

    
sock = socket(AF_INET, SOCK_DGRAM)
sock.settimeout(3)

name = f"NAME {sender}".encode() + b"\n"

# Initialize name
try:
    while True:
        sock.sendto(name, (SERVER, PORT))
        try:
            msg, _ = sock.recvfrom(MAX_MSG_SIZE)
            if msg.startswith(b"OK"):
                print(msg.decode())
                break
        except OSError:
            continue
except KeyboardInterrupt:
    print("Error initializing names\n")


# Connect to server
connect = f"CONN {receiver}".encode() + b"\n"

try:
    while True:
        sock.sendto(connect, (SERVER, PORT))
        try:
            msg, _ = sock.recvfrom(MAX_MSG_SIZE)
            if msg.startswith(b"OK"):
                print(msg.decode())
                break
        except OSError:
            continue
except KeyboardInterrupt:
    print("Error connecting\n")

        
if inputfile is None:
    while True:
        try:
            inp = input()
            pkt = make_packet(inp, seqNum, False, "", -1)
            while True:
                try:
                    sock.sendto(pkt, (SERVER, PORT))
                    msg, _ = sock.recvfrom(MAX_MSG_SIZE)
                    if is_ack(msg, seqNum + 1):
                        seqNum += 1
                        break
                except OSError:
                    continue
        except KeyboardInterrupt:
            continue
else:
    msgArr = []
    with open(inputfile, "rb") as file:
        while True:
            chunk = file.read(1024)
            if not chunk:
                break
            msgArr.append(chunk)
        file.close()

    for ch in msgArr:
        try:
            input = make_packet(ch, seqNum, True, outputfile, -1)
            while True:
                try:
                    sock.sendto(input, (SERVER, PORT))
                    msg, _ = sock.recvfrom(MAX_MSG_SIZE)
                    if (is_ack(msg, seqNum + 1) == True) and (is_safe(msg) == True):
                        seqNum += 1
                        break       
                except timeout:
                    continue
                except KeyboardInterrupt:
                    break
        except KeyboardInterrupt:
            break

    end = "EOF\n"

    try:
        input = end.encode()    
        sock.sendto(input, (SERVER, PORT))
    except KeyboardInterrupt:
        print("Can't initialize")


while True:
    try:
        sock.sendto(".\n".encode(), (SERVER, PORT))
        msg, _ = sock.recvfrom(MAX_MSG_SIZE)
        if msg.startswith(b"OK"):
            break
    except KeyboardInterrupt:
        break
    except OSError:
        continue

while True:
    try:
        sock.sendto("QUIT\n\n".encode(), (SERVER, PORT))
        msg, _ = sock.recvfrom(MAX_MSG_SIZE)
        if msg.startswith(b"OK"):
            print(msg.decode())
            break
    except KeyboardInterrupt:
        break
    except OSError:
        continue


sock.close()