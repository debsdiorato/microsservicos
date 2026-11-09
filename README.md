# microsservicos

Sistema de pedidos dividido em microsserviços, feito na aula de 26/10 de Arquitetura de Software.

O pedidos-api recebe o pedido e manda para o RabbitMQ. O notificacoes-worker e o estoque-worker recebem o pedido cada um na sua fila.

## Como rodar

Dentro da pasta aula_26-10_microsservicos/microsservicos_mq:

    copy .env.example .env
    docker compose up -d --build

A API fica em http://localhost:8000/docs e o painel do RabbitMQ em http://localhost:15672 (usuário app, senha troque-mq).

Para parar: docker compose down
