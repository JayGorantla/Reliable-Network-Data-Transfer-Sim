import sys
from socket import *
import zlib

MAX_MSG_SIZE = 2048
SERVER = None
PORT = None
inputfile = None
outputFile = None
sender = "Rec1"
receiver = "Sender1"
ack = 0

if len(sys.argv) == 5:
    SERVER = sys.argv[2]
    PORT = int(sys.argv[4])
# elif len(sys.argv) == 8:
#     SERVER = sys.argv[2]
#     PORT = int(sys.argv[4])
#     inputfile = sys.argv[6]
#     outputfile = sys.argv[7]

def make_packet(input, seq, isFile, output, isAck):
    header = "{}\n{}\n{}\n{}\n".format(str(seq), str(isFile), str(output), str(isAck))
    packet = header + input + "\n"
    packet = packet.encode()
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


def is_ack(packet, ack):
    if is_safe(packet) == False:
        return False
    else:
        msgArr = packet.split(b"\n")
        if int(msgArr[1].decode()) == ack:
            return True
        else:
            return False


sock = socket(AF_INET, SOCK_DGRAM)
sock.settimeout(1)

name = f"NAME {sender}".encode() + b"\n"

try:
    while True:
            sock.sendto(name, (SERVER, PORT))
            try:
                msg, _ = sock.recvfrom(MAX_MSG_SIZE)
                if msg.startswith(b"OK"):
                    print(msg.decode())
                    break
            except timeout:
                print(f"Timeout at initialization\n")
                continue
except KeyboardInterrupt:
    print("Error initializing names\n")


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

messages = []
outputFile = None
finished = False

while True:
    try:
        msg, _ = sock.recvfrom(MAX_MSG_SIZE)
        if is_safe(msg) == False or is_ack(msg, ack) == False:
            for i in range(ack):
                if is_ack(msg, i):
                    data = "received"
                    pkt = make_packet(data, i + 1, None, None, i + 1)
                    sock.sendto(pkt, (SERVER, PORT))
                    continue
            data = "corrupted"
            pkt = make_packet(data, -1, None, None, -1)
            sock.sendto(pkt, (SERVER, PORT))
            continue
        elif msg == b"EOF\n":
            data = "received"
            finished = True
            sock.settimeout(3)
            pkt = make_packet(data, ack, None, None, ack)
            sock.sendto(pkt, (SERVER, PORT))
            break
        ack += 1
        getmsg = msg.split(b"\n")[5:]
        getmsg = b"\n".join(getmsg)
        if msg.split(b"\n")[2] == b"False":
            outputFile = None
            print(getmsg)
        else:
            outputFile = msg.split(b"\n")[3].decode()
            messages.append(getmsg)

        if finished == True:
            break
    except timeout:
        if finished == True:
            break
        continue

if outputFile is not None:
    with open(outputFile, "bw") as f:
        for i in messages:
            f.write(i)


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
        sock.sendto("QUIT\n".encode() + b"\n", (SERVER, PORT))
        msg, _ = sock.recvfrom(MAX_MSG_SIZE)
        if msg.startswith(b"OK"):
            print(msg.decode())
            break
    except KeyboardInterrupt:
        break
    except OSError:
        continue

sock.close()