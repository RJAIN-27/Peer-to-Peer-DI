import socket
from threading import *
import datetime
import pickle
import time
import platform

SEP='&*'
peer_dictionary_list = []
cookie_count=0
conn = 0
os=platform.system()
host = socket.gethostname()
version='P2P-DI/1.0'

def send_list_to_client(): #not used need to check before deleting
   print(PQuery())
   List = pickle.dumps(PQuery())
   send_list(List)

def get_it(): #recieving normal data
        data = ((conn.recv(1024))).decode()
        return (data)

def send_it(data): #sending normal data
   data1=(str(data)).encode()
   conn.send(data1)

def send_list(list): #not used need to check before deleting
   print (list)
   conn.send(list)


def getcookie(): #increaments the global cookie variable
    global cookie_count
    cookie_count+=1
    return (cookie_count)

def add_data_to_final_list(flag,ttl,host,listening_port,cookie,date_time,number_of_times):
   global peer_dictionary_list
   thisdict = dict(host=host, cookie=cookie, flag=flag, port=listening_port, num_of_times=number_of_times, date_time=date_time, ttl=ttl)
   peer_dictionary_list.append(thisdict)


def PQuery(command): #checks the active peers in the flag using the flag and makes a new list that is returned to the client
    new_list=[]
    for host in peer_dictionary_list:
        if (host["flag"] == 1 and (host["cookie"]!=int(command))):
            print ("flag was set to 1")
            new_list.append(host)
    return (new_list)

def already_registered(conn, command): #when ever the client is already registered and comes with a cookie for some other work this "num_of_times" variable is increased
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(command)):
            client["num_of_times"] = client["num_of_times"] + 1
            return "YES"

def register(conn,addr, HOST, lp): #the new clients come and get registered
    host = HOST
    cookie = getcookie()  #for every new client the global cookie variable is increased and given
   # data1 = (str(cookie)).encode()
   # conn.send(data1)
   # print (cookie)
    flag = 1 #flag is set to one showing that client is active
    ttl = 7200
    date_time = datetime.datetime.now()
    number_of_times = 1 #this variable counts the number of times a client comes for some work
    listening_port = lp #this fetches the port on which the peer is having its server
    add_data_to_final_list(flag, ttl, host, listening_port, cookie, date_time, number_of_times)  #adding the client to the list on RS
    print (PQuery(cookie))
    t = Thread(target=reduce_ttl, args=(conn, cookie))
    t.start()
    print("We started KeepAlive for")
    return cookie

def edit_flag_in_peer_list(conn, command): #This function is also not being used, I made it earlier for some purpose, need to check before deleting
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(command)):
            client["flag"] = 0

def keep_alive(command): #The client when chooses the keepalive, he is searched on the basis of the coomkie and the KEEPALIVE is updates
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(command)):
            client["ttl"] = 7200
            client["flag"] = 1

def reduce_ttl(conn, command): #as soon as the client registers in the RS, a thread runs to reduce the TTL
        global peer_dictionary_list
        for client in peer_dictionary_list:
            if client["cookie"] == (int(command)):
                for i in range(client["ttl"]):
                    time.sleep(1)
                    if (client["ttl"] == 0):
                        client["flag"] = 0 #once the TTL becomes 0 the flag is set to 0 and the client becomes inactive
                        break
                    client["ttl"]=client["ttl"]-1

def make_ttl_zero(command): #this function is not currently being used anywhere, I used it earlier, needs to check before deleting
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(command)):
           client["ttl"] = 0

def remove_client_from_list(conn, command): #if the client wats to leave then we remove him from the list on the RS
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(command)):
           # peer_dictionary_list.remove(client)
            client["ttl"] = 0
            client["flag"] = 0
            print ("print", client["flag"])
    print("Made inactive")

# def work(conn, command): #this function gives the main functionalities that the client can perform
#     while True:
#         ch=((conn.recv(1024))).decode()
#         if ch == "PQUERY":
#             conn.send(pickle.dumps(PQuery())) #send the list of clients active to the client
#         elif ch == "LEAVE":
#             remove_client_from_list(conn, command)
#             print ("Bye Again")
#         elif ch == "KEEPALIVE":
#             keep_alive(command)

def  set_flag_to_one(cookie):
    global peer_dictionary_list
    for client in peer_dictionary_list:
        if client["cookie"] == (int(cookie)):
            client["ttl"] = 7200
            client["flag"] = 1

def connect(conn, addr):#this function checks if the client who comes is already registered and has a cookie or it needs to be registered and put in the list on registration server
    global version
    global host
    while True:
        command=((conn.recv(1024))).decode() #this fetches the REGISTER command or the Cookie if already registered
        message=str.split(command, SEP)
        length=len(message)
        if message[0] == "REGISTER":
            if(length != 6):
              cookie=register(conn, addr, message[2], message[4])
              response=version+SEP+"200"+SEP+"OK"+SEP+host+SEP+os+SEP+str(cookie)
              data1 = (str(response)).encode()
              conn.send(data1)
            else:
              set_flag_to_one(message[2])
              response =version+SEP+"200"+SEP+"OK"+SEP+host+SEP+os
              data1 = (str(response)).encode()
              conn.send(data1)
        elif message[0] == "LEAVE":
            var=already_registered(conn,message[2])
            if (var == "YES"):
                remove_client_from_list(conn, message[2])
                print("Bye Again")
        elif message [0] == "KEEPALIVE":
            var = already_registered(conn,(message[2]))
            if (var == "YES"):
                keep_alive(message[2])
        elif message[0] == "PQUERY":
            var = already_registered(conn, (message[2]))
            if (var == "YES"):
                print("Client already registered")
                print ("sends the following list", PQuery(message[2]))
                conn.send(pickle.dumps(PQuery(message[2])))
    # if command == "REGISTER":
    #     register(conn,addr)
    # else:
    #     var=already_registered(conn,command)
    #     if (var == "YES"):
    #         data1 = (str(var)).encode()
    #         conn.send(data1)
    #         work(conn, command)

if __name__ == "__main__":
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    port = 65423
    s.bind(('', port))
    s.listen(5)
    print ("server listening")
    while True:   #server will continuously listen for new clients
        conn, addr = s.accept()
        t = Thread(target=connect, args=(conn, addr))  #new thread for each client --> go to function connect
        t.start()
    s.close()


