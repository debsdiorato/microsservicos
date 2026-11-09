import json
import os
import uuid
from datetime import datetime, timezone

import pika
from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

EXCHANGE = "pedidos"
class PublicadorRabbit:
    def __init__(self, url: str):
        self._params = pika.URLParameters(url)

    def publicar(self, evento: dict) -> None:
        with pika.BlockingConnection(self._params) as con:
            canal = con.channel()
            canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout", durable=True)
            canal.basic_publish(
                exchange=EXCHANGE,
                routing_key="",
                body=json.dumps(evento).encode(),
                properties=pika.BasicProperties(
                    content_type="application/json",
                    delivery_mode=pika.DeliveryMode.Persistent,
                    message_id=evento["id"],
                ),
            )
def obter_publicador() -> PublicadorRabbit:
    return PublicadorRabbit(os.environ["AMQP_URL"])

app = FastAPI(title="Serviço de Pedidos", version="1.0.0")
class PedidoEntrada(BaseModel):
    cliente: str = Field(min_length=3, max_length=120)
    email: EmailStr
    valor_total: float = Field(gt=0)
class PedidoRecebido(BaseModel):
    id: str
    status: str
@app.get("/saude")
def saude():
    return {"api": "ok"}

@app.post("/pedidos", response_model=PedidoRecebido, status_code=status.HTTP_202_ACCEPTED)
def criar_pedido(entrada: PedidoEntrada, publicador: PublicadorRabbit = Depends(obter_publicador)):
    evento = {
        "id": str(uuid.uuid4()),
        "cliente": entrada.cliente,
        "email": entrada.email,
        "valor_total": entrada.valor_total,
        "criado_em": datetime.now(timezone.utc).isoformat(),
    }
    try:
        publicador.publicar(evento)
    except pika.exceptions.AMQPError:
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Broker de mensagens indisponível")
    return {"id": evento["id"], "status": "RECEBIDO"}
