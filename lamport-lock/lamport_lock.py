'''
Esse algoritmo resolve o problema da exclusao mutua para diversos
processos (docker containers no nosso caso), que se comunicam
atraves de mensagens AF_INET sockets.

O algoritmo consiste em manter um relogio logico de Lamport e
conceder o acesso a zona critica se:

1) Todos os outros eventos responderam a sua requisicao (i.e. estao cientes)
2) Todos os outros eventos tem alguma requisicao para entrar na zona critica
3) O evento desse processo eh o com maior prioridade: menor valor da tupla: (timestampt, pid).

Use os seguintes comandos para executar:
```sh
docker build -t lamport-lock .
docker compose up
```
Para conferir os logs rode:
```sh
docker logs peer1
```

As vezes os logs podem demorar de aparecer ou virem em blocos grandes.

Exemplo de output:
```
...
peer2  | Processo 2 retorna evento de 1
peer2  | Mensagem de 1 recebida por 2. Tipo da msg=reply
peer2  | Mensagem de 3 recebida por 2. Tipo da msg=request
peer1  | Mensagem de 3 recebida por 1. Tipo da msg=reply
peer3  | Mensagem de 2 recebida por 3. Tipo da msg=reply
peer2  | Processo 2 retorna evento de 3
peer2  | Mensagem de 3 recebida por 2. Tipo da msg=reply
peer2  | Mensagem de 1 recebida por 2. Tipo da msg=release
peer1  | Acesso a zona critica por 1 no tempo 09:18:22, pela 1-esima vez
peer1  | Lista de processos:  [(1, 1), (1, 2), (1, 3)]
peer2  | Mensagem de 1 recebida por 2. Tipo da msg=request
peer1  | Liberando zona critica. Lista:  [(1, 1), (1, 2), (1, 3)]
...
```

Fontes: 
    Parte do algoritmo foi modificado de https://connorwstein.github.io/Lamport-Clocks/

    Tambem foi utilizado o ChatGPT para gerar os dockerfiles e um esqueleto
    para a comunicacao usando sockets.

    Para o relogio de Lamport, ele segue implementacoes padroes. Foi utilizada uma
    lock para tornar os acessos atomicos.
'''

import threading
import time
import socket
import json
import os
from datetime import datetime


class LamportClock:
    def __init__(self) -> None:
        self.clock = 0
        self.lock = threading.Lock()
    
    def increment(self):
        # usar lock para manter incremento atomico
        with self.lock:
            self.clock += 1
    
    def update(self, event_timestamp):
        with self.lock:
            self.clock = max(self.clock, event_timestamp)
            self.clock += 1
    
    def time(self):
        with self.lock:
            return self.clock

class Process:
    def __init__(self, pid, peers):
        self.pid = pid
        self.peers = peers # lista com outros servidores
        self.request_list = [] # lista de eventos ainda nao respondidos 
        self.replies_received = 0 # 
        self.clock = LamportClock()
        self.lock = threading.Lock()
        print(f'Initialized pid={pid}')

    def request_critical_section(self):
        with self.lock: # pego a lock para adicionar na lista
            self.clock.increment() # evento interno
            timestamp = self.clock.time() 
            self.request_list.append((timestamp, self.pid))
            self.request_list.sort()
            assert(self.replies_received == 0) # teste de sanidade: nao pedir duas vezes
        self.replies_received = 0
        message = json.dumps({'type': 'request', 'timestamp': timestamp, 'pid': self.pid})
        for peer in self.peers.values():
            self.send_message(peer, message)

    def release_critical_section(self):
        with self.lock:
            # Pegar lock para alterar a lista de requests e o clock
            self.clock.increment()
            timestamp = self.clock.time()
            print('Liberando zona critica. Lista: ', self.request_list)
            self.request_list.sort()
            # teste de sanidade: o evento retirado deve ser o de menor
            # prioridade
            assert(self.request_list[0][1] == self.pid)
            self.request_list.pop(0)
            self.replies_received = 0
        message = json.dumps({'type': 'release', 'timestamp': timestamp, 'pid': self.pid})
        for peer in self.peers.values():
            self.send_message(peer, message)

    def handle_message(self, message):
        with self.lock:
            message = json.loads(message)
            msg_type = message['type']
            msg_pid = message['pid']
            msg_ts = message['timestamp']
            print(f'Mensagem de {msg_pid} recebida por {self.pid}. Tipo da msg={msg_type}')
            if msg_type == 'request':
                # alguem quer acessar a critical session
                # devemos atualizar nosso clock, e retornar uma resposta
                # de que recebemos essa mensagem
                self.clock.update(msg_ts)
                self.request_list.append((msg_ts, msg_pid))
                self.request_list.sort()
                reply = json.dumps({
                    'type': 'reply',
                    'timestamp': self.clock.time(),
                    'pid' : self.pid
                })
                print(f'Processo {self.pid} retorna evento de {msg_pid}')
                self.send_message(self.peers[msg_pid], reply)
                return
            elif msg_type == 'release':
                # Marca que msg_pid liberou a zona critica
                self.clock.update(msg_ts)
                #Retira da lista
                self.request_list = [req for req in self.request_list if req[1] != message['pid']]
            elif msg_type == 'reply':
                # Responderam nossa requisicao
                self.clock.update(msg_ts)
                self.replies_received += 1           
    
    def send_message(self, peer, message):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.sendto(message.encode(), peer)

    def listen_for_messages(self, port): 
        '''
        Escuta a requisição dos outros processos participantes 
        através da porta do socket, a mensagem é passada por meio
        de um json e seu tipo é verificada, e a mensagem
        é lidada pelo handle_message. 
        '''
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', port))
        while True:
            data, _ = sock.recvfrom(1024)
            self.handle_message(data.decode())
            time.sleep(0.05)

    def critical_section(self, i):
        while True:
            if self.check_available():
                # Accessando zona critica!
                now = datetime.now()
                cur_time = now.strftime("%H:%M:%S")
                print(f'Acesso a zona critica por {self.pid} no tempo {cur_time}, pela {i}-esima vez')
                print('Lista de processos: ', self.request_list)
                time.sleep(1) # simular acesso
                self.release_critical_section()
                break
            else:
                time.sleep(0.05)
                continue
    
    def check_available(self):
        # Devemos checar se todos os outros servidores ja responderam,
        # se meu evento eh o mais novo E se tambem todos os outros eventos
        # tem algum requisicao depois da minha
        all_answered = self.replies_received == len(self.peers)
        if not all_answered:
            return False
        older_request = {k: False for k in self.peers.keys()}
        my_req = None            
        for req in self.request_list:
            if req[1] == self.pid:
                my_req = req
        if my_req == None:
            return False
        for req in self.request_list:
            if req[1] != self.pid and my_req < req:
                # sou mais recente
                older_request[req[1]]=True
        if all(older_request.values()):
            # posso accessar
            return True
        return False
    
def main():
    peers = {
        1: ('peer1', 5001),
        2: ('peer2', 5002),
        3: ('peer3', 5003),
    }
    #peers é um dict que associa o pid (chave) com seu nome e porta do socket (valor)
    pid = int(os.environ['PEER_ID'])
    peers_without_me = peers.copy()
    del peers_without_me[pid]
    lamport_lock = Process(pid, peers_without_me)
    
    listener_thread = threading.Thread(target=lamport_lock.listen_for_messages, args=(peers[pid][1],))
    listener_thread.start()
    
    time.sleep(1)  
    for i in range(1,20):
        lamport_lock.request_critical_section()
        lamport_lock.critical_section(i)

if __name__ == "__main__":
    main()
