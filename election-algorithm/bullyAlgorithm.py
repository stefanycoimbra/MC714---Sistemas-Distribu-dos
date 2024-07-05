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
# ZMQ é uma biblioteca para implementação de sockets e mensagens assíncronas em python
import sys
import os
import random
import threading
from multiprocessing import Process, Value, Array
import zmq
import time

# TIMEOUT setado para 10s
TIMEOUT = 10000

# Método "leaderMessage" é chamado para cada nó conectado no sistema
def leaderMessage(nodeId, isStarter, ids_alive):
    
    # PID do sistema -> para provar que cada nó começa de uma thread diferente
    pid = os.getpid()

    print("Check Node --> Pid {}, Node Id: {}, Starts an election: {}".format(pid, nodeId, isStarter))

    # Abre socket de publisher
    port = 5550 + nodeId
    
    # Criação da instância de socket
    context = zmq.Context()
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://127.0.0.1:{port}")

    # Variável compartilhada entre as 2 threads
    responder_return = {"BROADCAST_LEADER": 0, "RECEIVED_OK": 0, "BROADCAST_TERMINATE": 0}

    # Criação de thread de escuta para cada processo
    listener_thread = threading.Thread(target=responder, args=(nodeId, ids_alive, socket, responder_return,))
    listener_thread.start()

    # Começa a escutar antes de enviar mensagem de eleição
    time.sleep(1) 


    if isStarter:
        # Broadcast 'LEADER'
        responder_return["BROADCAST_LEADER"] = 1
        pass

    
    while not responder_return["BROADCAST_LEADER"]:
        # Espera até precisar do broadcast "LEADER"
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

# Método "responder" -> respostas dos nós em relação às mensagens de eleição
def responder(nodeId, ids_alive, pubsocket, responder_return):
    
    # Conecta e se inscreve nos nós conectados
    context = zmq.Context()
    socket = context.socket(zmq.SUB)

    socket.subscribe("LEADER")
    socket.subscribe("TERMINATE")
    socket.subscribe("OK")


    ports = [5550 + int(i) for i in ids_alive]

    for port in ports:
        socket.connect(f"tcp://127.0.0.1:{port}")

    # Registros como subscriber no poll
    poller = zmq.Poller()
    poller.register(socket, zmq.POLLIN)

    # Mensagens recebidas
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
                # Se outro nó tem um ID maior
                # Se torna nó passivo
                if to_id == nodeId:
                    responder_return["RECEIVED_OK"] = 1

                if to_id > nodeId:
                    # Elimina menores nós passivos
                    responder_return["RECEIVED_OK"] = 1

            if received_body == "TERMINATE":
                # Líder já foi selecionado
                # Notifica todos os nós
                return

            elif received_body == "LEADER":
                # Se sender_id <myid, então manda "OK para o sender
                if sender_id < nodeId:                                        
                    resp_message = f"OK:{5550+nodeId}:{nodeId}:{sender_id}"
                    
                    print("NODE {} RESPONDS OK TO NODE {}".format(nodeId, sender_id))
                    pubsocket.send_string(resp_message)
                    
                    # Depois disso, notifica main a mandar um broadcast "LEADER"
                    responder_return["BROADCAST_LEADER"] = 1
                    pass

        else:
            # Se nenhuma mensagem é recebida pelo TIMEOUT
            # Nó atual é o líder
            if not responder_return["RECEIVED_OK"]:
                responder_return["BROADCAST_TERMINATE"] = 1
                return

    # fim da thread de escuta
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


    # Cria os processos
    # Cada processo representa um nó
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
