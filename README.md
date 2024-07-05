# MC714: Sistemas Distribuídos

## <img src="https://img.icons8.com/color/30/000000/task--v1.png"/> Algoritmos implementados
### * Relógio de Lamport com exclusão mútua (lamport-lock)
### * Algoritmo de eleição de líder: Bully Algorithm (election-algorithm)

## <img src="https://img.icons8.com/external-kiranshastry-lineal-color-kiranshastry/30/000000/external-clipboard-advertising-kiranshastry-lineal-color-kiranshastry.png"/> Como rodar os códigos?
### Para o de Lamport-lock:
Use os seguintes comandos para executar:
```
docker build -t lamport-lock .
docker compose up
```
Para conferir os logs rode:
```
docker logs peer1
```
#### Fontes Lamport-Lock:

- Parte do algoritmo foi modificado de [Lamport Clocks by Connor Stein](https://connorwstein.github.io/Lamport-Clocks/).
- Também foi utilizado o ChatGPT para gerar os Dockerfiles e um esqueleto para a comunicação usando sockets.
- Para o relógio de Lamport, ele segue implementações padrões. Foi utilizada uma lock para tornar os acessos atômicos.

#### Fontes Election-Algorithm:

- Algoritmo foi retirado e modificado de [Bully Algorithm by Alperari]([https://github.com/alaattinyilmaz/bully](https://github.com/alperari/bully/tree/main)).

### Para o Bully Algorithm:
```
python bullyAlgorithm.py numProcess numConnected numStarters
```
#### Sobre os argumentos:
* numProcess: quantos nós existem no coinc
* numConnected: quantos nós estão conectados no sistema
* numStarters: quantos nós iniciam a eleição
