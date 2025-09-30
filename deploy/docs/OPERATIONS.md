# Day-2 Operations Runbook

This runbook covers routine operational tasks for NexusRAG in production: scaling, log collection, certificate rotation, database maintenance, and incident response.

---

## 1. Scaling

### 1.1 Horizontal Pod Autoscaler (Kubernetes)

The Gateway should be configured with an HPA based on CPU utilization:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gateway-hpa
  namespace: nexusrag
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gateway
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
```

### 1.2 Manual Scaling

```bash
# Scale Gateway
kubectl scale deployment gateway -n nexusrag --replicas=5

# Scale Data API
kubectl scale deployment data-api -n nexusrag --replicas=3

# Verify
kubectl get pods -n nexusrag -l app=nexusrag-gateway
```

### 1.3 Docker Compose Scaling

```bash
docker compose up -d --scale gateway=4 --scale data-api=2
```

### 1.4 Scaling Indicators

Scale up the Gateway when:
- Average CPU exceeds 70% across replicas
- p95 response latency exceeds 3 seconds
- Rate limit 429 responses exceed 1% of total requests
- Active WebSocket connections approach 1000 per replica

Scale down when:
- Average CPU drops below 30% for 10 minutes
- Active connections per replica drop below 100

---

## 2. Log Collection

### 2.1 Kubernetes (Fluentd + Elasticsearch)

Deploy Fluentd as a DaemonSet to collect container logs:

```bash
helm repo add fluent https://fluent.github.io/helm-charts
helm install fluentd fluent/fluentd \
  --namespace logging --create-namespace \
  --set output.host=elasticsearch.logging.svc.cluster.local
```

### 2.2 Structured Log Format

All NexusRAG services emit JSON-structured logs:

```json
{
  "timestamp": "2026-03-30T12:00:00Z",
  "level": "info",
  "service": "gateway",
  "request_id": "req_abc123",
  "message": "Query completed",
  "strategy": "combined",
  "duration_ms": 2340,
  "tokens": 1500
}
```

### 2.3 Key Log Queries

Search for slow queries:

```
service:gateway AND duration_ms:>5000
```

Search for errors:

```
service:gateway AND level:error
```

Search for rate limit events:

```
service:gateway AND message:"rate limit exceeded"
```

### 2.4 Log Retention

- Development: 7 days
- Staging: 14 days
- Production: 30 days (90 days for error-level and above)

### 2.5 Docker Compose Log Rotation

```yaml
services:
  gateway:
    logging:
      driver: json-file
      options:
        max-size: "50m"
        max-file: "10"
```

---

## 3. Certificate Rotation

### 3.1 cert-manager (Automatic)

If using cert-manager with Let's Encrypt, certificates are renewed automatically 30 days before expiration. Monitor renewal:

```bash
kubectl get certificates -n nexusrag
kubectl describe certificate nexusrag-tls -n nexusrag
```

Check for renewal failures:

```bash
kubectl get events -n nexusrag --field-selector reason=Failed
```

### 3.2 Manual Certificate Rotation

For manually managed certificates:

```bash
# Generate a new certificate (or obtain from your CA)
# Replace the TLS secret
kubectl create secret tls nexusrag-tls \
  --namespace nexusrag \
  --cert=new-tls.crt \
  --key=new-tls.key \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart the ingress controller to pick up the new certificate
kubectl rollout restart deployment ingress-nginx-controller -n ingress-nginx
```

### 3.3 Certificate Expiry Monitoring

Add a Prometheus alert for certificates expiring within 14 days:

```yaml
- alert: TLSCertificateExpiringSoon
  expr: certmanager_certificate_expiration_timestamp_seconds - time() < 1209600
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "TLS certificate for {{ $labels.name }} expires in less than 14 days"
```

---

## 4. Database Maintenance

### 4.1 MongoDB Backups

**Daily automated backup (Kubernetes CronJob):**

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: mongodb-backup
  namespace: nexusrag
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: mongo:7
            command:
            - /bin/sh
            - -c
            - |
              mongodump --uri="$MONGO_URI" --gzip --archive=/backups/nexusrag-$(date +%Y%m%d).gz
              find /backups -name "*.gz" -mtime +30 -delete
            envFrom:
            - secretRef:
                name: nexusrag-secrets
            volumeMounts:
            - name: backups
              mountPath: /backups
          volumes:
          - name: backups
            persistentVolumeClaim:
              claimName: backup-pvc
          restartPolicy: OnFailure
```

**Manual backup:**

```bash
mongodump --uri="$MONGO_URI" --gzip --archive=nexusrag-$(date +%Y%m%d).gz
```

**Restore from backup:**

```bash
mongorestore --uri="$MONGO_URI" --gzip --archive=nexusrag-20260330.gz --drop
```

### 4.2 MongoDB Index Maintenance

Verify indexes exist for query performance:

```javascript
// Connect to MongoDB
use nexusrag

// Gateway collections
db.conversations.getIndexes()
// Expected: { user_id: 1, updated_at: -1 }

db.documents.getIndexes()
// Expected: { ingested_at: -1 }

// Data API collections
use nexusrag_data

db.personnel.getIndexes()
db.portfolio.getIndexes()
// Expected: { vertical: 1 }
```

Create missing indexes:

```javascript
db.conversations.createIndex({ user_id: 1, updated_at: -1 })
db.documents.createIndex({ ingested_at: -1 })
db.portfolio.createIndex({ vertical: 1 })
```

### 4.3 MongoDB Compaction

After bulk deletions, compact collections to reclaim disk space:

```javascript
db.runCommand({ compact: "conversations" })
```

For MongoDB Atlas, compaction is handled automatically.

### 4.4 Vector Store Maintenance

**Rebuild the FAISS index** (required if chunks are deleted or the embedding model changes):

```bash
# Trigger a full re-index via the Gateway admin endpoint
curl -X POST http://localhost:5000/api/admin/reindex \
  -H "Authorization: Bearer $ADMIN_KEY"
```

**Backup the vector store:**

```bash
# Kubernetes
kubectl exec -n nexusrag deploy/gateway -- \
  tar czf /tmp/vectorstore.tar.gz /app/data/vectorstore
kubectl cp nexusrag/gateway-pod:/tmp/vectorstore.tar.gz ./backups/vectorstore-$(date +%Y%m%d).tar.gz
```

---

## 5. Health Monitoring

### 5.1 Prometheus Alerts

```yaml
groups:
- name: nexusrag
  rules:
  - alert: GatewayHighErrorRate
    expr: rate(nexusrag_request_errors_total[5m]) / rate(nexusrag_request_total[5m]) > 0.05
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "Gateway error rate exceeds 5%"

  - alert: GatewayHighLatency
    expr: histogram_quantile(0.99, rate(nexusrag_request_duration_seconds_bucket[5m])) > 10
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "Gateway p99 latency exceeds 10 seconds"

  - alert: MongoDBConnectionPoolExhausted
    expr: nexusrag_mongo_pool_available == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "MongoDB connection pool is exhausted"

  - alert: VectorStoreUnhealthy
    expr: nexusrag_vectorstore_healthy == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Vector store health check is failing"
```

### 5.2 Grafana Dashboard

Import the NexusRAG Grafana dashboard from `deploy/grafana/dashboard.json`. Key panels:

- Request rate and error rate by service
- Latency percentiles (p50, p95, p99) by strategy
- LLM token consumption over time
- Active WebSocket connections
- MongoDB operation latency
- Pod CPU and memory utilization

---

## 6. Incident Response

### 6.1 Service Degradation

If the Gateway is slow but not failing:

1. Check `kubectl top pods -n nexusrag` for resource pressure.
2. Review `nexusrag_request_duration_seconds` to identify the slow stage (retrieval, reranking, generation).
3. If reranking is the bottleneck, temporarily disable it: set `RERANKING_ENABLED=false` and restart.
4. If the LLM is slow, check the provider's status page.
5. Scale up if resource utilization is high.

### 6.2 Complete Outage

1. Check pod status: `kubectl get pods -n nexusrag`.
2. Check events: `kubectl get events -n nexusrag --sort-by=.lastTimestamp`.
3. Check MongoDB connectivity from a Gateway pod.
4. Check secrets are mounted: `kubectl exec -n nexusrag deploy/gateway -- env | grep OPENAI`.
5. Check ingress: `kubectl describe ingress -n nexusrag`.
6. Roll back if a recent deployment caused the outage: `kubectl rollout undo deployment/gateway -n nexusrag`.

### 6.3 Post-Incident

- Write a post-mortem within 48 hours.
- Update this runbook with any new procedures discovered.
- Add monitoring for the failure mode if it was not already covered.
