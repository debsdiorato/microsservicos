# Microsserviços de Pedidos com RabbitMQ

Sistema distribuído de pedidos baseado em microsserviços e mensageria assíncrona utilizando RabbitMQ.

## Arquitetura da Solução

O projeto é composto por quatro serviços orquestrados via Docker Compose:

- **rabbitmq**: Broker de mensagens (RabbitMQ 4) com plugin de gerenciamento (Management UI na porta 15672).
- **pedidos-api**: API REST desenvolvida em FastAPI (porta 8000) responsável por receber os pedidos via HTTP e publicá-los na exchange de mensagens.
- **notificacoes-worker**: Serviço de processamento em segundo plano que consome da fila `pedido.criado` e simula o disparo de notificações por e-mail.
- **estoque-worker**: Serviço de processamento em segundo plano que consome da fila `estoque.pedido.criado` e simula a reserva de estoque.
- **DLQ (Dead Letter Queue)**: Fila `pedidos.dlq` associada à exchange `pedidos.dlx` para mensagens malformadas ou com erro de processamento.

## Pré-requisitos

- Docker Desktop instalado e em execução (com suporte ao Docker Compose v2).
- PowerShell (Windows) ou terminal Bash (Linux/macOS).
- Postman (opcional, para execução da suíte de testes).

## Configuração do Ambiente

O arquivo `compose.yaml` utiliza variáveis de ambiente para autenticação no RabbitMQ (`RABBITMQ_USER` e `RABBITMQ_PASS`).

Crie ou edite o arquivo `.env` dentro da pasta `aula_26-10_microsservicos/microsservicos_mq` (ou configure as variáveis em seu terminal/sistema):

```env
RABBITMQ_USER=app
RABBITMQ_PASS=troque-mq
```

Nota: Esses valores são os mesmos configurados nos testes do Postman e nos scripts utilitários do projeto.

## Como Executar o Projeto

1. Abra o terminal (PowerShell no Windows) e navegue até a pasta do Docker Compose:

   ```powershell
   cd "aula_26-10_microsservicos\microsservicos_mq"
   ```

2. Se preferir definir as variáveis de ambiente diretamente na sessão do terminal antes de iniciar:

   No PowerShell (Windows):
   ```powershell
   $env:RABBITMQ_USER="app"
   $env:RABBITMQ_PASS="troque-mq"
   ```

   No Bash (Linux/macOS):
   ```bash
   export RABBITMQ_USER="app"
   export RABBITMQ_PASS="troque-mq"
   ```

3. Construa as imagens e inicie os contêineres:

   ```powershell
   docker compose up --build
   ```

   Para executar em segundo plano (modo detached), utilize a opção `-d`:

   ```powershell
   docker compose up -d --build
   ```

4. Para acompanhar os logs dos serviços quando estiver em modo detached:

   ```powershell
   docker compose logs -f
   ```

   Para acompanhar o log de um serviço específico:

   ```powershell
   docker compose logs -f pedidos-api
   docker compose logs -f notificacoes-worker
   docker compose logs -f estoque-worker
   ```

## Acessando os Serviços e Testando

### 1. Verificação de Saúde da API
- URL: http://localhost:8000/saude
- Resposta esperada: `{"api": "ok"}`
- Documentação interativa (Swagger UI): http://localhost:8000/docs

### 2. Painel de Gerenciamento do RabbitMQ
- URL: http://localhost:15672
- Usuário: `app`
- Senha: `troque-mq`
- Permite visualizar exchanges, filas ativas, conexões e taxas de mensagens trafegadas.

### 3. Envio de um Pedido de Teste
Via PowerShell:
```powershell
Invoke-RestMethod -Method Post -Uri "http://localhost:8000/pedidos" -ContentType "application/json" -Body '{"cliente": "Ana Souza", "email": "ana.souza@example.com", "valor_total": 300}'
```

Via cURL:
```bash
curl -X POST http://localhost:8000/pedidos \
  -H "Content-Type: application/json" \
  -d '{"cliente": "Ana Souza", "email": "ana.souza@example.com", "valor_total": 300}'
```

Resposta esperada (HTTP 202 Accepted):
```json
{
  "id": "uuid-gerado",
  "status": "RECEBIDO"
}
```

Ao enviar a requisição, é possível acompanhar nos logs do terminal que tanto o worker de estoque quanto o worker de notificações processam a mensagem simultaneamente.

### 4. Teste de Dead Letter Queue (Mensagem Inválida)
Para verificar o descarte e envio para a DLQ (`pedidos.dlq`):
```powershell
.\scripts\enviar_mensagem_malformada.ps1
```
Ou no Linux/macOS:
```bash
bash ./scripts/enviar_mensagem_malformada.sh
```

### 5. Testes Automatizados com Postman
Os arquivos de teste encontram-se na pasta `aula_26-10_microsservicos/postman`:
1. Abra o Postman.
2. Importe a coleção `AS_aula-26-10_pedidos.postman_collection.json`.
3. Importe o ambiente `AS_aula-26-10_local.postman_environment.json` e selecione-o como ambiente ativo.
4. Execute as requisições manualmente ou utilize o Runner da coleção.

## Como Parar o Projeto

Para encerrar os contêineres:
```powershell
docker compose down
```

Para encerrar removendo volumes e redes criadas:
```powershell
docker compose down -v
```

## Solução de Problemas (Troubleshooting)

Caso ocorra algum erro durante o início ou execução do Docker, siga as instruções abaixo conforme o cenário:

### 1. Erro de Conflito de Porta (port is already allocated / address already in use)
- **Sintoma**: Mensagem como `Bind for 0.0.0.0:8000 failed: port is already allocated` ou na porta `15672`.
- **Causa**: Outro contêiner Docker ou serviço local no sistema operacional já está usando essa porta.
- **O que fazer**:
  1. Liste os contêineres em execução:
     ```powershell
     docker ps
     ```
  2. Localize qual contêiner está mapeando a porta conflitante (por exemplo `8000` ou `15672`) e pare o contêiner:
     ```powershell
     docker stop <nome_ou_id_do_container>
     ```
  3. Caso o conflito seja com um processo nativo do Windows (fora do Docker), identifique e encerre o processo:
     ```powershell
     Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess
     ```

### 2. Erro de Conexão com o Docker Daemon (Cannot connect to the Docker daemon)
- **Sintoma**: `error during connect: ... The system cannot find the file specified` ou `docker daemon is not running`.
- **Causa**: O Docker Desktop está fechado, ainda inicializando ou travado.
- **O que fazer**:
  1. Abra o Docker Desktop no menu Iniciar do Windows.
  2. Aguarde o ícone do Docker na bandeja do sistema indicar status verde ("Engine running").
  3. No terminal, teste executando:
     ```powershell
     docker info
     ```
  4. Se o Docker Desktop travar, reinicie o aplicativo ou o serviço do Windows:
     ```powershell
     Restart-Service docker
     ```

### 3. Erro de Autenticação no RabbitMQ (ProbableAuthenticationError / Access Refused)
- **Sintoma**: A API ou os workers exibem erro de conexão com RabbitMQ repetidamente e não inicializam.
- **Causa**: As variáveis de ambiente `RABBITMQ_USER` e `RABBITMQ_PASS` não foram declaradas ou diferem entre o serviço do RabbitMQ e os clientes.
- **O que fazer**:
  1. Certifique-se de que o arquivo `.env` existe e contém:
     ```env
     RABBITMQ_USER=app
     RABBITMQ_PASS=troque-mq
     ```
  2. Se as variáveis foram alteradas após a criação do contêiner do RabbitMQ, o volume antigo pode ter retido a senha anterior. Para resetar completamente os dados do RabbitMQ:
     ```powershell
     docker compose down -v
     docker compose up --build
     ```

### 4. Falha de Dependência ou Contêiner Marcado como Unhealthy
- **Sintoma**: `dependency failed to start: container microsservicos_mq-rabbitmq-1 is unhealthy`.
- **Causa**: O RabbitMQ demorou mais tempo para inicializar do que o tempo limite do healthcheck, ou há falta de recursos de memória/CPU alocados para a máquina virtual do Docker (WSL2).
- **O que fazer**:
  1. Verifique os logs específicos do RabbitMQ para descobrir o motivo da falha:
     ```powershell
     docker compose logs rabbitmq
     ```
  2. Verifique o consumo de memória da máquina. Em computadores com pouca memória livre, o RabbitMQ pode ativar alarmes de bloqueio de recursos.
  3. Tente reiniciar os serviços após garantir recursos livres:
     ```powershell
     docker compose restart rabbitmq
     ```

### 5. Erro na Construção das Imagens (Build Failure / Falha no pip)
- **Sintoma**: Erro durante `docker compose build` ao baixar pacotes Python via `pip install`.
- **Causa**: Falha de conexão de rede, bloqueio por proxy ou cache desatualizado.
- **O que fazer**:
  1. Force a reconstrução das imagens descartando o cache local:
     ```powershell
     docker compose build --no-cache
     ```
  2. Verifique sua conexão com a internet e se o Docker possui acesso aos servidores do PyPI.

### 6. Contêineres Órfãos ou Estado Corrompido
- **Sintoma**: Comportamento inconsistente, contêineres antigos com nomes divergentes permanecendo ativos.
- **O que fazer**:
  1. Execute uma limpeza completa dos recursos do compose:
     ```powershell
     docker compose down --remove-orphans -v
     ```
  2. Suba o ambiente novamente:
     ```powershell
     docker compose up --build
     ```
