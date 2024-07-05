# MC714: Sistemas Distribuídos

## <img src="https://img.icons8.com/color/30/000000/task--v1.png"/> Algoritmos implementados
### * Relógio de Lamport
### * Algoritmo de eleição de líder: Bully Algorithm

## <img src="https://img.icons8.com/external-kiranshastry-lineal-color-kiranshastry/30/000000/external-clipboard-advertising-kiranshastry-lineal-color-kiranshastry.png"/> Como rodar os códigos?
### Para o de Lamport:
Use os seguintes comandos para executar:
```
docker build -t lamport-lock .
docker compose up
docker-compose ps
```
Para conferir os logs rode:
```
docker logs peer1
```

### Para o Bully Algorithm:
```
python bullyAlgorithm.py numProcess numConnected numStarters
```
#### Sobre os argumentos:
* numProcess: quantos nós existem no coinc
* numConnected: quantos nós estão conectados no sistema
* numStarters: quantos nós iniciam a eleição
