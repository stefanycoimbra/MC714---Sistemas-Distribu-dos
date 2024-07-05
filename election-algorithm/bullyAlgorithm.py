'''
Esse código representa eleição de um novo líder
pelo algoritmo do valentão.

O algoritmo consiste em escolher um novo líder, dado que
o atual falhou ou não está mais disponível.

Para isso:
1) Um nó dentre aqueles conectados inicia uma eleição no sistema
2) Ele envia uma mensagem de eleição de líder a todos os nós conectados a ele
3) Se um nó com um ID maior que ele recebe uma mensagem de eleição de líder, ele responde com uma mensagem de OK
4) Todos os nós com IDs maiores mandam mensagem de eleição para os conectados a eles
5) Isso é feito sucessivamente até que um nó não receba uma mensagem de OK ou não tenha para mais quem mandar mensagem de eleição
6) Se isso acontecer, este nó é o líder e envia mensagem de broadcast para todos 

Use os seguintes comandos para executar:
```sh
python bullyAlgorithm.py numProcess numConnected numStarters
```

Sobre os argumentos:
--> numProcess: quantos nós existem no coinc
--> numConnected: quantos nós estão conectados no sistema
--> numStarters: quantos nós iniciam a eleição
'''

# Election algorithm -> Bully Algorithm
# Libraries used 
import sys
import os
import random
import threading
from multiprocessing import Process, Value, Array
import zmq
import time

# Set listening timeout to be 10 sec
TIMEOUT = 10000

# "leader" method is assigned to every node alive
def leaderMessage(nodeId, isStarter, ids_alive):
    
    # Get the system Pid -> to prove each node is started from a different thread
    pid = os.getpid()

    print("Check Node --> Pid {}, Node Id: {}, Starts an election: {}".format(pid, nodeId, isStarter))

    # Open my publisher socket 
    # (also share this pub socket with listener thread)
    port = 5550 + nodeId
    
    # Creates socket instance
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{port}")

    # Shared variable among 2 threads (main & listener)
    responder_return = {"BROADCAST_LEADER": 0, "RECEIVED_OK": 0, "BROADCAST_TERMINATE": 0}

    # Creating a listener thread for each process
    listener_thread = threading.Thread(target=responder, args=(nodeId, ids_alive, socket, responder_return,))
    listener_thread.start()

    # Make sure others started listening before send LEADER message
    time.sleep(1) 


    if isStarter:
        # Broadcast 'LEADER'
        responder_return["BROADCAST_LEADER"] = 1
        pass

    
    while not responder_return["BROADCAST_LEADER"]:
        # Wait until needs to broadcast "LEADER"
        if responder_return["RECEIVED_OK"] or responder_return["BROADCAST_TERMINATE"]:
            break
        pass
    
    
    if not responder_return["RECEIVED_OK"] and responder_return["BROADCAST_LEADER"]:
        message = f"LEADER:{port}:{nodeId}:-1"

        print("NODE {} MULTICASTS LEADER MESSAGE".format(nodeId))
        time.sleep(0.1)
        socket.send_string(message)


    time.sleep(0.25)
    if not responder_return["RECEIVED_OK"]:
        while not responder_return["BROADCAST_TERMINATE"]:
            pass

        message = f"TERMINATE:{port}:{nodeId}:-1"

        print("NEW LEADER:", nodeId)
        socket.send_string(message)

    listener_thread.join()
    pass

# "responder" method makes sure that the Nodes answer the leader messages
def responder(nodeId, ids_alive, pubsocket, responder_return):
    
    # Connect and subscribe to the connected nodes
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    socket.subscribe("LEADER")
    socket.subscribe("TERMINATE")
    socket.subscribe("OK")


    ports = [5550 + int(i) for i in ids_alive]

    for port in ports:
        socket.connect(f"tcp://127.0.0.1:{port}")

    # Register subscribe socket to poller
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    # Start receiving messages
    while True:
        evts = dict(poller.poll(timeout=TIMEOUT))
        if socket in evts:
            message = socket.recv_string()

            message_parsed = message.split(":")

            received_body = message_parsed[0]
            received_port = int(message_parsed[1])
            sender_id = int(message_parsed[2])
            to_id = int(message_parsed[3])
            
            if received_body == "OK":
                # If another node has a higher ID,
                # Become passive listener
                if to_id == nodeId:
                    responder_return["RECEIVED_OK"] = 1

                if to_id > nodeId:
                    # Eliminate smaller passive nodes as well
                    responder_return["RECEIVED_OK"] = 1

            if received_body == "TERMINATE":
                # Leader is already selected
                # Notify everyone 
                return

            elif received_body == "LEADER":
                # If sender_id < myid, then send "OK" to sender
                if sender_id < nodeId:                                        
                    resp_message = f"OK:{5550+nodeId}:{nodeId}:{sender_id}"
                    
                    print("NODE {} RESPONDS OK TO NODE {}".format(nodeId, sender_id))
                    pubsocket.send_string(resp_message)
                    
                    # after that, notify main to broadcast "LEADER"
                    responder_return["BROADCAST_LEADER"] = 1
                    pass

        else:
            # If no message is received for TIMEOUT amount of time
            # Then this means actual node is the leader
            if not responder_return["RECEIVED_OK"]:
                responder_return["BROADCAST_TERMINATE"] = 1
                return

    # End of listener_thread
    pass
    
def main(args):  
    numProc = int(args[1])
    numAlive = int(args[2])
    numStarter = int(args[3])

    ids = [i for i in range(numProc)]
    ids_nodes_connected = random.sample(ids, numAlive)
    ids_election_starter = random.sample(ids_nodes_connected, numStarter)

    print("Connected nodes:", ids_nodes_connected, sep="\n")
    print("Election starters:", ids_election_starter, sep="\n")


    # Create processes
    # Each process represents a node
    processes = []
    
    for i in ids_nodes_connected:
        isStarter = (i in ids_election_starter)
        
        process = Process(target=leaderMessage, args=(i, isStarter, ids_nodes_connected,))
        processes.append(process)

    for process in processes:
        process.start()
    
    for process in processes:
        process.join()

    pass

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Invalid command line arguments!")
        print("Use: python bully.py numProcess numConnectedNodes numElectionStarters\n")
    else:
        main(args=sys.argv)
