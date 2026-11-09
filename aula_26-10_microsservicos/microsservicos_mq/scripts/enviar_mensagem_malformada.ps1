$u = "app"; $p = "troque-mq"; $h = "http://localhost:15672"
$cred = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("${u}:${p}"))
$hdr = @{ Authorization = "Basic $cred" }
$corpo = '{"properties":{"content_type":"application/json"},"routing_key":"pedido.criado","payload":"isto nao e JSON {","payload_encoding":"string"}'
Invoke-RestMethod -Method Post -Uri "$h/api/exchanges/%2F/amq.default/publish" -Headers $hdr -ContentType "application/json" -Body $corpo
Start-Sleep -Seconds 2
Invoke-RestMethod -Method Post -Uri "$h/api/queues/%2F/pedidos.dlq/get" -Headers $hdr -ContentType "application/json" -Body '{"count":10,"ackmode":"ack_requeue_true","encoding":"auto"}' | ConvertTo-Json -Depth 6
