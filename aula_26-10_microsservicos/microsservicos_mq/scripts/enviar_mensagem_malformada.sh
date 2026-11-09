#!/usr/bin/env bash
set -euo pipefail
source .env 2>/dev/null || true
U="${RABBITMQ_USER:-app}"; P="${RABBITMQ_PASS:-troque-mq}"; H="${RABBIT_URL:-http://localhost:15672}"

curl -s -u "$U:$P" -H "content-type: application/json" -X POST \
  "$H/api/exchanges/%2F/amq.default/publish" \
  -d '{"properties":{"content_type":"application/json"},"routing_key":"pedido.criado","payload":"isto não é JSON {","payload_encoding":"string"}'
echo
sleep 2
echo "Mensagens na DLQ (pedidos.dlq):"
curl -s -u "$U:$P" -H "content-type: application/json" -X POST \
  "$H/api/queues/%2F/pedidos.dlq/get" \
  -d '{"count":10,"ackmode":"ack_requeue_true","encoding":"auto"}'
echo
