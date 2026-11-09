import pika
import pytest
from fastapi.testclient import TestClient
from app.main import app, obter_publicador

class PublicadorFalso:
    def __init__(self):
        self.eventos = []
    def publicar(self, evento: dict) -> None:
        self.eventos.append(evento)
class PublicadorIndisponivel:
    def publicar(self, evento: dict) -> None:
        raise pika.exceptions.AMQPConnectionError("broker fora do ar")
@pytest.fixture
def cliente():
    yield TestClient(app)
    app.dependency_overrides.clear()
def test_pedido_valido_retorna_202_e_publica_evento(cliente):
    falso = PublicadorFalso()
    app.dependency_overrides[obter_publicador] = lambda: falso
    resposta = cliente.post("/pedidos", json={"cliente": "Ana Souza", "email": "ana@example.com", "valor_total": 300.0})
    
    assert resposta.status_code == 202
    assert resposta.json()["status"] == "RECEBIDO"
    assert len(falso.eventos) == 1
    assert falso.eventos[0]["id"] == resposta.json()["id"]
    assert falso.eventos[0]["cliente"] == "Ana Souza"
    assert falso.eventos[0]["email"] == "ana@example.com"
def test_valor_invalido_retorna_422_e_nao_publica(cliente):
    falso = PublicadorFalso()
    app.dependency_overrides[obter_publicador] = lambda: falso

    resposta = cliente.post("/pedidos", json={"cliente": "Ana Souza", "email": "ana@example.com", "valor_total": 0})

    assert resposta.status_code == 422
    assert falso.eventos == []

def test_email_invalido_retorna_422_e_nao_publica(cliente):
    falso = PublicadorFalso()
    app.dependency_overrides[obter_publicador] = lambda: falso
    resposta = cliente.post("/pedidos", json={"cliente": "Ana Souza", "email": "ana-sem-arroba", "valor_total": 300.0})
    assert resposta.status_code == 422
    assert falso.eventos == []

def test_broker_indisponivel_retorna_503(cliente):
    app.dependency_overrides[obter_publicador] = lambda: PublicadorIndisponivel()
    resposta = cliente.post("/pedidos", json={"cliente": "Ana Souza", "email": "ana@example.com", "valor_total": 300.0})
    assert resposta.status_code == 503
def test_saude(cliente):
    resposta = cliente.get("/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"api": "ok"}
