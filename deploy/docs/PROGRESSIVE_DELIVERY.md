# Progressive Delivery

This document describes canary and blue-green deployment procedures for NexusRAG using Argo Rollouts.

---

## Prerequisites

- Kubernetes 1.28+ cluster with NexusRAG deployed
- Argo Rollouts controller installed
- NGINX Ingress Controller or Istio for traffic splitting
- Prometheus and Grafana for metrics-based analysis

### Install Argo Rollouts

```bash
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install the kubectl plugin
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-linux-amd64
chmod +x kubectl-argo-rollouts-linux-amd64
sudo mv kubectl-argo-rollouts-linux-amd64 /usr/local/bin/kubectl-argo-rollouts
```

---

## Canary Deployment

Canary deployment gradually shifts traffic from the stable version to the new version while monitoring for errors.

### Step 1: Replace Deployment with Rollout

Convert the Gateway `Deployment` to an Argo `Rollout`:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: gateway
  namespace: nexusrag
spec:
  replicas: 4
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: nexusrag-gateway
  template:
    metadata:
      labels:
        app: nexusrag-gateway
    spec:
      containers:
      - name: gateway
        image: ghcr.io/nexusrag/gateway:1.2.3
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: nexusrag-config
        - secretRef:
            name: nexusrag-secrets
        livenessProbe:
          httpGet:
            path: /alive
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 15
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 15
          periodSeconds: 10
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
  strategy:
    canary:
      canaryService: gateway-canary
      stableService: gateway-stable
      trafficRouting:
        nginx:
          stableIngress: nexusrag-ingress
          additionalIngressAnnotations:
            canary-by-header: X-Canary
      steps:
      - setWeight: 10
      - pause: { duration: 5m }
      - analysis:
          templates:
          - templateName: gateway-success-rate
          args:
          - name: service-name
            value: gateway-canary
      - setWeight: 30
      - pause: { duration: 5m }
      - analysis:
          templates:
          - templateName: gateway-success-rate
          args:
          - name: service-name
            value: gateway-canary
      - setWeight: 60
      - pause: { duration: 5m }
      - setWeight: 100
```

### Step 2: Create Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-stable
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-gateway
  ports:
  - port: 5000
    targetPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: gateway-canary
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-gateway
  ports:
  - port: 5000
    targetPort: 5000
```

### Step 3: Define Analysis Template

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: gateway-success-rate
  namespace: nexusrag
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 60s
    count: 5
    successCondition: result[0] >= 0.99
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
        query: |
          sum(rate(nexusrag_request_total{service="{{args.service-name}}",status!~"5.."}[2m]))
          /
          sum(rate(nexusrag_request_total{service="{{args.service-name}}"}[2m]))
  - name: latency-p99
    interval: 60s
    count: 5
    successCondition: result[0] <= 5.0
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring.svc.cluster.local:9090
        query: |
          histogram_quantile(0.99,
            sum(rate(nexusrag_request_duration_seconds_bucket{service="{{args.service-name}}"}[2m]))
            by (le)
          )
```

### Step 4: Trigger a Canary Release

Update the image tag:

```bash
kubectl argo rollouts set image gateway gateway=ghcr.io/nexusrag/gateway:1.3.0 -n nexusrag
```

Monitor the rollout:

```bash
kubectl argo rollouts get rollout gateway -n nexusrag --watch
```

### Step 5: Manual Promotion or Abort

If the canary is paused waiting for manual approval:

```bash
# Promote to next step
kubectl argo rollouts promote gateway -n nexusrag

# Abort and roll back
kubectl argo rollouts abort gateway -n nexusrag
```

### Automatic Rollback

If any analysis step fails (error rate exceeds 1% or p99 latency exceeds 5 seconds), Argo Rollouts automatically aborts the canary and routes all traffic back to the stable version. No manual intervention is required.

---

## Blue-Green Deployment

Blue-green deployment maintains two full environments and switches traffic atomically.

### Rollout Manifest

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: gateway-bluegreen
  namespace: nexusrag
spec:
  replicas: 4
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: nexusrag-gateway
  template:
    metadata:
      labels:
        app: nexusrag-gateway
    spec:
      containers:
      - name: gateway
        image: ghcr.io/nexusrag/gateway:1.2.3
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: nexusrag-config
        - secretRef:
            name: nexusrag-secrets
        readinessProbe:
          httpGet:
            path: /ready
            port: 5000
          initialDelaySeconds: 15
          periodSeconds: 10
        resources:
          requests:
            cpu: "500m"
            memory: "1Gi"
          limits:
            cpu: "2"
            memory: "4Gi"
  strategy:
    blueGreen:
      activeService: gateway-active
      previewService: gateway-preview
      autoPromotionEnabled: false
      prePromotionAnalysis:
        templates:
        - templateName: gateway-success-rate
        args:
        - name: service-name
          value: gateway-preview
      scaleDownDelaySeconds: 300
```

### Services

```yaml
apiVersion: v1
kind: Service
metadata:
  name: gateway-active
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-gateway
  ports:
  - port: 5000
    targetPort: 5000
---
apiVersion: v1
kind: Service
metadata:
  name: gateway-preview
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-gateway
  ports:
  - port: 5000
    targetPort: 5000
```

### Workflow

1. Update the image tag:
   ```bash
   kubectl argo rollouts set image gateway-bluegreen gateway=ghcr.io/nexusrag/gateway:1.3.0 -n nexusrag
   ```

2. Argo Rollouts creates the new (green) ReplicaSet and routes the `gateway-preview` service to it.

3. Pre-promotion analysis runs against the preview service.

4. If analysis passes, the rollout pauses for manual promotion.

5. Test the preview service directly:
   ```bash
   curl http://gateway-preview.nexusrag.svc.cluster.local:5000/ready
   ```

6. Promote to switch live traffic:
   ```bash
   kubectl argo rollouts promote gateway-bluegreen -n nexusrag
   ```

7. The `gateway-active` service now points to the green ReplicaSet. The old (blue) ReplicaSet is scaled down after the delay period.

---

## Choosing Between Canary and Blue-Green

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic shift | Gradual (10% -> 30% -> 60% -> 100%) | Atomic (0% -> 100%) |
| Resource cost | Low (runs alongside stable pods) | High (full duplicate environment) |
| Rollback speed | Instant (traffic re-routed) | Instant (switch active service) |
| Testing in production | Yes, with real traffic | Yes, via preview service |
| Risk | Lower (limited blast radius) | Higher (full switchover) |
| Best for | Stateless services, API changes | Database migrations, breaking changes |

For NexusRAG, canary deployment is recommended for the Gateway and Data API. Blue-green is recommended when the release includes changes to the vector store format or database schema that require a coordinated cutover.

---

## Monitoring During Rollout

During any progressive delivery, monitor these Grafana panels:

1. **Error rate** -- Should remain below 1% across both stable and canary/preview.
2. **Latency p99** -- Should remain below 5 seconds.
3. **LLM error rate** -- A spike may indicate a configuration mismatch in the new version.
4. **WebSocket connections** -- Verify connections are not dropping during traffic shifts.
5. **MongoDB connection pool** -- Ensure the new pods are not exhausting the pool.

Set up a dedicated Slack or PagerDuty channel for rollout notifications:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  annotations:
    notifications.argoproj.io/subscribe.on-rollout-completed.slack: nexusrag-deploys
    notifications.argoproj.io/subscribe.on-rollout-aborted.slack: nexusrag-deploys
```
