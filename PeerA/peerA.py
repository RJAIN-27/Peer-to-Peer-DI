import socket
import threading
import platform
import os, fnmatch
import pickle
import time

RFCIndex = []
PeerIndex = []
need_RFC_list = [768]
cookie = None
RS_SERVER = ''
RS_SERVER_PORT = 65423
HOST = socket.gethostname()
OS = platform.system()
SEP = '&*'
version = 'P2P-DI/1.0'
LISTENING_PORT = 65454
FilePath = ''


def read_files_in_local():
    global FilePath
    list_of_files = os.listdir(FilePath)
    dict_list = []
    for file in list_of_files:
        list_tmp = []
        if fnmatch.fnmatch(file, "rfc*.txt"):
            number = file[3:file.index('-')]
            title = file[file.index('-') + 1:file.index('.')]
            dict_list.append([number, title])
    return dict_list


def set_rfc_index_local():
    global HOST
    global RFCIndex
    dict_list = read_files_in_local()
    for rfc in dict_list:
        rfc_dict = {
            'number': int(rfc[0]),
            'title': rfc[1],
            'hostname': HOST,
            'TTL': 7200
        }
        RFCIndex.append(rfc_dict)
    print ("---Local RFC Updated---")
    print(RFCIndex)


def is_duplicate(rfc_dict):
    global RFCIndex
    for rfc_there in RFCIndex:
        if rfc_dict['number'] == rfc_there['number'] and rfc_dict['hostname'] == rfc_there['hostname']:
            return True
        else:
            continue
    return False


def merge_rfc_index(new_rfc_index):
    global RFCIndex

    for rfc in new_rfc_index:
        if is_duplicate(rfc):
            continue
        else:
            RFCIndex.append(rfc)
#    print("New RFC Required after merging", RFCIndex)

def search_after_updating_rfc_index(RFCNo):
    global RFCIndex
    global PeerIndex

    for rfc in RFCIndex:
        if rfc['hostname'] == HOST:  # !!!!!!!! CORRECT == TO NOT= for host issue!!!!!!!!
            if rfc['number'] == RFCNo:
                for peer in PeerIndex:
                    if rfc['hostname'] == peer['host']:
                        return [rfc['hostname'], peer['port']]
    return None


def request_rfc_from_peer(RFCNo, host_port_list, s):
    global RFCIndex
    req = (str('GET' + SEP + 'RFC' + SEP + str(RFCNo) + SEP + version + SEP + HOST + SEP + OS)).encode()
    print("---Message sent from Client--- ", req)
    s.send(req)
    msg = (s.recv(8192)).decode()
    message = msg.split(SEP)
    print("---File Recieved 200 OK---")
    filename = message[5]
    title = filename[filename.index('-') + 1:filename.index('.')]
    f = open(filename, "w+")  # save it in local
    f.write(message[6])
    f.close()
    rfc_dict = {'number': RFCNo, 'Title': title, 'hostname': HOST, 'TTL': 7200}
    RFCIndex.append(rfc_dict)


def response_rfc_send_to_peer(RFCNo, conn):
    print("Sending RFC file ", RFCNo, " to peer")
    response = version + SEP + '200' + SEP + 'OK' + SEP + HOST + SEP + OS
    print("---Response sent from server--- ", response)
    title = ''
    for rfc in RFCIndex:
        if rfc['number'] == RFCNo and rfc['hostname'] == HOST:
            title = rfc['title']
    filename = 'rfc' + str(RFCNo) + '-' + title + '.txt'
    with open(filename, "r") as f:
        filedata = f.read()
        response = response + SEP + filename + SEP + filedata
    conn.send(str(response).encode())


def send_your_rfc_index(conn):
    global RFCIndex
    conn.send(pickle.dumps(RFCIndex))


def request_rfc_index_from_peer(s):
    req = (str('GET' + SEP + 'RFC-Index' + SEP + version + SEP + HOST + SEP + OS)).encode()
    print("---Requesting RFC Index to merge---")
    s.send(req)
    print("---Message sent from Client--- ", req)
    rfc_dict = pickle.loads(s.recv(1024))
    print("---New rfc loaded from peer--- ", rfc_dict)
    merge_rfc_index(rfc_dict)  # sending it to the merge function to check for duplicates and do


def server_action(conn, addr):
    global HOST
    global OS
    msg = (conn.recv(1024)).decode()
    message = str.split(msg, SEP)
    if message[0] == 'GET':
        if message[1] == 'RFC-Index':
            print("Sending RFC Index to ", str(addr))
            send_your_rfc_index(conn)
            print("Finished sending RFC Index to ", str(addr))
        elif message[1] == 'RFC':
            print("sending the RFC ", message[2])
            rfc_no = int(message[2])
            response_rfc_send_to_peer(rfc_no, conn)
            print("Finished sending RFC")
    conn.close()


def peer_server_start():
    global HOST
    global LISTENING_PORT
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('', LISTENING_PORT))
    s.listen(5)
    while True:  # server will continuously listen for new peer-clients
        conn, addr = s.accept()
        t = threading.Thread(target=server_action,
                             args=(conn, addr))  # new thread for each client --> go to function connect
        t.start()
    s.close()


def keepalive():  # we can use fun to keep-alive instead
    global RS_SERVER
    global RS_SERVER_PORT
    global HOST
    global OS
    global cookie
    global version
    s1 = socket.socket()
    s1.connect((RS_SERVER, RS_SERVER_PORT))
    while True:
        time.sleep(5)
        message = "KEEPALIVE" + SEP + version + SEP + str(cookie) + SEP + HOST + SEP + OS
        s1.send(str(message).encode())
    s1.close()  # Check while running if its causing issue


def leave_network(s1):
    global RS_SERVER
    global RS_SERVER_PORT
    global HOST
    global OS
    global cookie
    global SEP
    global version
    message = "LEAVE" + SEP + version + SEP + str(cookie) + SEP + HOST + SEP + OS
    print ("---Message sent while leaving--- ",message)
    s1.send(str(message).encode())
    print("Leaving the peer network")


def register(s1):
    global RS_SERVER
    global RS_SERVER_PORT
    global HOST
    global OS
    global SEP
    global version
    global cookie

    if cookie == None:
        message = "REGISTER" + SEP + version + SEP + HOST + SEP + OS + SEP + str(LISTENING_PORT)
        s1.send(str(message).encode())
        print("---Message sent from client--- ", message)
        msg = (s1.recv(1024)).decode()
        message = msg.split(SEP)
        print("---Message recieved from server--- ", msg)
        if len(message) == 6:
            cookie = message[5]
    else:
        message = "REGISTER" + SEP + version + SEP + HOST + SEP + OS + SEP + str(LISTENING_PORT) + SEP + str(cookie)
        s1.send(str(message).encode())
        print("---Message sent from client--- ", message)
        msg = (s1.recv(1024)).decode()
        message = str.split(msg, SEP)
        print("---Message recieved from server--- ", msg)
        if message[1] == '200':
            print("Registered again with the network")

def pquery(s):
    message = (str("PQUERY" + SEP + version + SEP + str(cookie) + SEP + HOST + SEP + OS)).encode()
    print("---Quering for Active Peers from RS---")
    s.send(message)
    print("---Message from Client Sent--- ", message)
    PeerIndex = pickle.loads(s.recv(4096))
    print("---The following Peer Index was recieved---\n", PeerIndex)
    if len(PeerIndex) == 0:
        print("---No active peers---")
    return PeerIndex


def main():
    global RS_SERVER
    global RS_SERVER_PORT
    global HOST
    global LISTENING_PORT
    global OS
    global need_RFC_list
    global FilePath
    global Cookieval
    global RFCIndex
    global PeerIndex

    wd = os.getcwd()
    FilePath = wd

    s = socket.socket()
    s.connect((RS_SERVER, RS_SERVER_PORT))

    register(s)  # Registration verified
    print("---Register done---")
    s.close()

    #keep_alive_thread = threading.Thread(target=keepalive)
    #keep_alive_thread.daemon = True
    #keep_alive_thread.start()  # Keep Alive registered
    set_rfc_index_local()  # Local list updated verified
    print("---Local RFCS---")

    server_thread = threading.Thread(target=peer_server_start)
    server_thread.start()  # server boot up and handling the server requests verified

    for rfc_no in need_RFC_list:
        s2 = socket.socket()
        s2.connect((RS_SERVER, RS_SERVER_PORT))
        message = (str("PQUERY" + SEP + version + SEP + str(cookie) + SEP + HOST + SEP + OS)).encode()
        print("---Quering for Active Peers from RS---")
        s2.send(message)
        print ("---Message from Client Sent--- ",message)
        PeerIndex = pickle.loads(s2.recv(4096))
        print("---The following Peer Index was recieved---\n", PeerIndex)
        if len(PeerIndex) == 0:
            print("---No active peers---")
        s2.close()

        # searching in each active Peer list if the requested RFC is present
        found = False
        for peer in PeerIndex:
            if peer['host'] != HOST or (peer['port'] != str(LISTENING_PORT)):
                s = socket.socket()
                s.connect((peer['host'], int(peer['port'])))
                print("---Requesting RFC index from peer--- ", peer['host'], peer['port'])
                request_rfc_index_from_peer(s)  # request and merge verified
                s.close()

                ret_value = search_after_updating_rfc_index(rfc_no)  # returns hostname if found, else None
                if ret_value != None:
                    found = True
                    s = socket.socket()
                    s.connect((ret_value[0], int(ret_value[1])))
                    request_rfc_from_peer(rfc_no, ret_value, s)  # downloads, saves and appends to the rfc list
                    s.close()

        if found == False:
            print("---No peer has the rfc number requested---")

    while True:
        userinput = input("leave or pquery??\n")

        if userinput == "leave":
            s1 = socket.socket()
            s1.connect((RS_SERVER, RS_SERVER_PORT))
            LeaveSock = leave_network(s1)
            #keep_alive_thread.join()
            s1.close()
            break
        # elif userinput == "stay":
        #     print ("Waiting before closing server....\n")
        #     time.sleep(60)
        elif userinput == "pquery":
            s1 = socket.socket()
            s1.connect((RS_SERVER, RS_SERVER_PORT))
            pquery(s1)
            s1.close()

if __name__ == '__main__':
    main()
