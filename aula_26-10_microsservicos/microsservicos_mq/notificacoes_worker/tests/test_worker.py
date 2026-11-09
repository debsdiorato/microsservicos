import json
import uuid

import pytest

from app import worker


class CanalFalso:
    def __init__(self):
        self.acks, self.nacks = [], []

    def basic_ack(self, tag):
        self.acks.append(tag)

    def basic_nack(self, tag, requeue=True):
        self.nacks.append((tag, requeue))


class Metodo:
    def __init__(self, tag):
        self.delivery_tag = tag


def evento(**extra):
    return {"id": str(uuid.uuid4()), "cliente": "Ana Souza", "email": "ana.souza@example.com",
            "valor_total": 300.0, **extra}


@pytest.fixture(autouse=True)
def sem_espera(monkeypatch):
    monkeypatch.setattr(worker, "TEMPO_PROCESSAMENTO", 0)
    worker._processados.clear()


def test_evento_valido_e_confirmado_com_ack():
    canal = CanalFalso()
    worker.ao_receber(canal, Metodo(1), None, json.dumps(evento()).encode())
    assert canal.acks == [1] and canal.nacks == []


def test_duplicata_nao_e_processada_duas_vezes(monkeypatch):
    chamadas = []
    monkeypatch.setattr(worker, "processar", lambda e: chamadas.append(e["id"]))
    canal, e = CanalFalso(), evento()
    worker.ao_receber(canal, Metodo(1), None, json.dumps(e).encode())
    worker.ao_receber(canal, Metodo(2), None, json.dumps(e).encode())
    assert chamadas == [e["id"]]
    assert canal.acks == [1, 2]


@pytest.mark.parametrize("corpo", [b"isto nao e json", b"\xff\xfe", b"[1, 2, 3]", b'{"id": 123}', b"{}"])
def test_mensagem_malformada_recebe_nack_sem_requeue(corpo):
    canal = CanalFalso()
    worker.ao_receber(canal, Metodo(7), None, corpo)
    assert canal.nacks == [(7, False)] and canal.acks == []


def test_log_exibe_email(capsys):
    canal = CanalFalso()
    worker.ao_receber(canal, Metodo(1), None, json.dumps(evento()).encode())
    assert "ana.souza@example.com" in capsys.readouterr().out


def test_evento_sem_email_vai_para_dlq():
    canal = CanalFalso()
    e = evento(); del e["email"]
    worker.ao_receber(canal, Metodo(1), None, json.dumps(e).encode())
    assert canal.nacks == [(1, False)]
