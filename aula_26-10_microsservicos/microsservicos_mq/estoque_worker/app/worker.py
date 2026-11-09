import json
import os
import signal
import sys
import time
import pika

EXCHANGE = "pedidos"
FILA = "estoque.pedido.criado"
DLX = "pedidos.dlx"
DLQ = "pedidos.dlq"
TEMPO_PROCESSAMENTO = float(os.environ.get("TEMPO_PROCESSAMENTO", "1"))
_processados: set[str] = set()

def conectar(tentativas: int = 30, intervalo: float = 2.0) -> pika.BlockingConnection:
    params = pika.URLParameters(os.environ["AMQP_URL"])
    for n in range(1, tentativas + 1):
        try:
            return pika.BlockingConnection(params)
        except pika.exceptions.AMQPConnectionError:
            print(f"[estoque] RabbitMQ indisponível (tentativa {n}/{tentativas})", flush=True)
            time.sleep(intervalo)
    raise RuntimeError("RabbitMQ não respondeu a tempo")
def processar(evento: dict) -> None:
    time.sleep(TEMPO_PROCESSAMENTO)
    print(f"[estoque] Estoque reservado para o pedido {evento['id'][:8]} "
          f"(R$ {evento['valor_total']:.2f})", flush=True)


def ao_receber(canal, metodo, propriedades, corpo: bytes) -> None:
    try:
        evento = json.loads(corpo)
    except json.JSONDecodeError:
        print("[estoque] Mensagem inválida enviada para a DLQ", flush=True)
        canal.basic_nack(metodo.delivery_tag, requeue=False)
        return
    if evento["id"] in _processados:
        print(f"[estoque] Pedido {evento['id'][:8]} já reservado; ignorado", flush=True)
    else:
        processar(evento)
        _processados.add(evento["id"])
    canal.basic_ack(metodo.delivery_tag)
def main() -> None:
    signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
    con = conectar()
    canal = con.channel()
    canal.exchange_declare(exchange=EXCHANGE, exchange_type="fanout", durable=True)
    canal.exchange_declare(exchange=DLX, exchange_type="fanout", durable=True)
    canal.queue_declare(queue=DLQ, durable=True)
    canal.queue_bind(queue=DLQ, exchange=DLX)
    canal.queue_declare(queue=FILA, durable=True, arguments={"x-dead-letter-exchange": DLX})
    canal.queue_bind(queue=FILA, exchange=EXCHANGE)
    canal.basic_qos(prefetch_count=1)
    canal.basic_consume(queue=FILA, on_message_callback=ao_receber)
    print("[estoque] Aguardando mensagens...", flush=True)
    try:
        canal.start_consuming()
    finally:
        con.close()
if __name__ == "__main__":
    main()
