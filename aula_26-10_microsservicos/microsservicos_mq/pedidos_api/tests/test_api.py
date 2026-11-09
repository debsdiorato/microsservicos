import pika
import pytest
from fastapi.testclient import TestClient

from app.main import app, obter_publicador

PEDIDO_VALIDO = {"cliente": "Ana Souza", "email": "ana.souza@example.com", "valor_total": 300.0}


class PublicadorFalso:
    def __init__(self):
        self.eventos = []

    def publicar(self, evento: dict) -> None:
        self.eventos.append(evento)


class PublicadorIndisponivel:
    def publicar(self, evento: dict) -> None:
        raise pika.exceptions.AMQPConnectionError("broker fora do ar")


class PublicadorSemFila:
    def publicar(self, evento: dict) -> None:
        raise pika.exceptions.UnroutableError([])


@pytest.fixture
def cliente():
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def falso():
    f = PublicadorFalso()
    app.dependency_overrides[obter_publicador] = lambda: f
    return f


def test_pedido_valido_retorna_202_e_publica_evento(cliente, falso):
    resposta = cliente.post("/pedidos", json=PEDIDO_VALIDO)
    assert resposta.status_code == 202
    assert resposta.json()["status"] == "RECEBIDO"
    assert len(falso.eventos) == 1
    assert falso.eventos[0]["id"] == resposta.json()["id"]
    assert falso.eventos[0]["cliente"] == "Ana Souza"


def test_evento_publicado_contem_email(cliente, falso):
    cliente.post("/pedidos", json=PEDIDO_VALIDO)
    assert falso.eventos[0]["email"] == "ana.souza@example.com"


@pytest.mark.parametrize("email", ["sem-arroba", "ana@", "@example.com", ""])
def test_email_invalido_retorna_422_e_nao_publica(cliente, falso, email):
    resposta = cliente.post("/pedidos", json={**PEDIDO_VALIDO, "email": email})
    assert resposta.status_code == 422
    assert "email" in str(resposta.json())
    assert falso.eventos == []


def test_email_ausente_retorna_422(cliente, falso):
    sem_email = {k: v for k, v in PEDIDO_VALIDO.items() if k != "email"}
    resposta = cliente.post("/pedidos", json=sem_email)
    assert resposta.status_code == 422
    assert falso.eventos == []


def test_valor_invalido_retorna_422_e_nao_publica(cliente, falso):
    resposta = cliente.post("/pedidos", json={**PEDIDO_VALIDO, "valor_total": 0})
    assert resposta.status_code == 422
    assert falso.eventos == []


def test_cliente_curto_retorna_422(cliente, falso):
    resposta = cliente.post("/pedidos", json={**PEDIDO_VALIDO, "cliente": "Al"})
    assert resposta.status_code == 422
    assert falso.eventos == []


def test_broker_indisponivel_retorna_503(cliente):
    app.dependency_overrides[obter_publicador] = lambda: PublicadorIndisponivel()
    resposta = cliente.post("/pedidos", json=PEDIDO_VALIDO)
    assert resposta.status_code == 503


def test_exchange_sem_fila_retorna_503(cliente):
    app.dependency_overrides[obter_publicador] = lambda: PublicadorSemFila()
    resposta = cliente.post("/pedidos", json=PEDIDO_VALIDO)
    assert resposta.status_code == 503


def test_saude(cliente):
    resposta = cliente.get("/saude")
    assert resposta.status_code == 200
    assert resposta.json() == {"api": "ok"}
