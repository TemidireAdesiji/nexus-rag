# NexusRAG Deployment Guide

This guide covers production deployment of NexusRAG using Docker Compose, Kubernetes, AWS EKS, and OCI OKE, including TLS termination, monitoring, backup, and progressive delivery.

---

## Prerequisites

- Docker 24+ and Docker Compose v2
- kubectl 1.28+ (for Kubernetes deployments)
- Helm 3.12+ (for chart-based deployments)
- An OpenAI API key or compatible LLM endpoint
- MongoDB 6+ (managed or self-hosted)
- A domain name with DNS control (for TLS)
- Terraform 1.5+ (for cloud infrastructure provisioning)

---

## 1. Docker Compose Deployment

Docker Compose is the fastest path to a running NexusRAG environment.

### 1.1 Configure Environment

Create a `.env` file in the project root:

```bash
# MongoDB
MONGO_URI=mongodb://mongo:27017
MONGO_DB_NAME=nexusrag

# Gateway
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o
DEFAULT_SEARCH_MODE=combined
RERANKING_ENABLED=true
AGENTIC_MODE=true
CORS_ORIGINS=http://localhost:3000
RATE_LIMIT_RPM=120
GATEWAY_WORKERS=4

# Data API
API_KEY=your-data-api-key

# UI
VITE_GATEWAY_URL=http://localhost:5000
VITE_GATEWAY_WS_URL=ws://localhost:5000
VITE_DATA_API_URL=http://localhost:3456
```

### 1.2 Start Services

```bash
docker compose up -d
```

Verify all services are healthy:

```bash
docker compose ps
curl http://localhost:5000/ready
curl http://localhost:3456/ping
curl http://localhost:3000
```

### 1.3 Scaling

Scale the Gateway horizontally:

```bash
docker compose up -d --scale gateway=3
```

When scaling, place an NGINX or Traefik reverse proxy in front to load-balance across Gateway replicas. See `examples/docker-deployment/README.md` for a complete example.

### 1.4 Volumes

Production deployments should use named volumes for persistence:

```yaml
volumes:
  mongo-data:
    driver: local
  vectorstore-data:
    driver: local
```

Map these in your Compose file to ensure data survives container restarts.

---

## 2. Kubernetes Deployment

### 2.1 Namespace and Secrets

```bash
kubectl create namespace nexusrag

kubectl create secret generic nexusrag-secrets \
  --namespace nexusrag \
  --from-literal=OPENAI_API_KEY=sk-your-key \
  --from-literal=MONGO_URI=mongodb+srv://user:pass@cluster.mongodb.net \
  --from-literal=API_KEY=your-data-api-key \
  --from-literal=REDIS_URL=redis://redis:6379/0
```

### 2.2 ConfigMap

```bash
kubectl apply -f - <<EOF
apiVersion: v1
kind: ConfigMap
metadata:
  name: nexusrag-config
  namespace: nexusrag
data:
  GATEWAY_PORT: "5000"
  GATEWAY_WORKERS: "4"
  LOG_LEVEL: "info"
  ENV: "production"
  DEFAULT_SEARCH_MODE: "combined"
  RERANKING_ENABLED: "true"
  AGENTIC_MODE: "true"
  RATE_LIMIT_RPM: "120"
  CORS_ORIGINS: "https://nexusrag.example.com"
  DATA_API_PORT: "3456"
  NODE_ENV: "production"
EOF
```

### 2.3 Gateway Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gateway
  namespace: nexusrag
spec:
  replicas: 3
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
        image: ghcr.io/nexusrag/gateway:latest
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
---
apiVersion: v1
kind: Service
metadata:
  name: gateway
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-gateway
  ports:
  - port: 5000
    targetPort: 5000
```

### 2.4 Data API Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: data-api
  namespace: nexusrag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nexusrag-data-api
  template:
    metadata:
      labels:
        app: nexusrag-data-api
    spec:
      containers:
      - name: data-api
        image: ghcr.io/nexusrag/data-api:latest
        ports:
        - containerPort: 3456
        envFrom:
        - configMapRef:
            name: nexusrag-config
        - secretRef:
            name: nexusrag-secrets
        livenessProbe:
          httpGet:
            path: /ping
            port: 3456
          initialDelaySeconds: 5
          periodSeconds: 10
        resources:
          requests:
            cpu: "250m"
            memory: "512Mi"
          limits:
            cpu: "1"
            memory: "1Gi"
---
apiVersion: v1
kind: Service
metadata:
  name: data-api
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-data-api
  ports:
  - port: 3456
    targetPort: 3456
```

### 2.5 UI Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ui
  namespace: nexusrag
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nexusrag-ui
  template:
    metadata:
      labels:
        app: nexusrag-ui
    spec:
      containers:
      - name: ui
        image: ghcr.io/nexusrag/ui:latest
        ports:
        - containerPort: 3000
        resources:
          requests:
            cpu: "100m"
            memory: "128Mi"
          limits:
            cpu: "500m"
            memory: "256Mi"
---
apiVersion: v1
kind: Service
metadata:
  name: ui
  namespace: nexusrag
spec:
  selector:
    app: nexusrag-ui
  ports:
  - port: 3000
    targetPort: 3000
```

### 2.6 Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nexusrag-ingress
  namespace: nexusrag
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/proxy-read-timeout: "120"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "120"
    nginx.ingress.kubernetes.io/websocket-services: "gateway"
spec:
  ingressClassName: nginx
  tls:
  - hosts:
    - nexusrag.example.com
    secretName: nexusrag-tls
  rules:
  - host: nexusrag.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: gateway
            port:
              number: 5000
      - path: /ws
        pathType: Prefix
        backend:
          service:
            name: gateway
            port:
              number: 5000
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ui
            port:
              number: 3000
```

---

## 3. AWS EKS with Terraform

### 3.1 Cluster Provisioning

```hcl
# main.tf
module "eks" {
  source          = "terraform-aws-modules/eks/aws"
  version         = "~> 20.0"
  cluster_name    = "nexusrag-cluster"
  cluster_version = "1.29"
  vpc_id          = module.vpc.vpc_id
  subnet_ids      = module.vpc.private_subnets

  eks_managed_node_groups = {
    general = {
      instance_types = ["m6i.xlarge"]
      min_size       = 2
      max_size       = 6
      desired_size   = 3
    }
    gpu = {
      instance_types = ["g5.xlarge"]
      min_size       = 0
      max_size       = 2
      desired_size   = 0
      labels = {
        "nexusrag/workload" = "reranker"
      }
      taints = [{
        key    = "nvidia.com/gpu"
        value  = "present"
        effect = "NO_SCHEDULE"
      }]
    }
  }
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
  name    = "nexusrag-vpc"
  cidr    = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b", "us-east-1c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true
}
```

### 3.2 Apply and Configure

```bash
terraform init
terraform apply

aws eks update-kubeconfig --name nexusrag-cluster --region us-east-1

# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace

# Install cert-manager
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager \
  --namespace cert-manager --create-namespace \
  --set installCRDs=true

# Deploy NexusRAG manifests
kubectl apply -f deploy/k8s/
```

---

## 4. OCI OKE Deployment

### 4.1 Cluster Setup

```bash
# Create OKE cluster using OCI CLI
oci ce cluster create \
  --compartment-id $COMPARTMENT_ID \
  --name nexusrag-oke \
  --kubernetes-version v1.29.1 \
  --vcn-id $VCN_ID \
  --service-lb-subnet-ids "[\"$LB_SUBNET_ID\"]"

# Create node pool
oci ce node-pool create \
  --cluster-id $CLUSTER_ID \
  --compartment-id $COMPARTMENT_ID \
  --name nexusrag-pool \
  --node-shape VM.Standard.E4.Flex \
  --node-shape-config '{"ocpus": 4, "memoryInGBs": 32}' \
  --size 3

# Configure kubectl
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_ID \
  --file $HOME/.kube/config
```

### 4.2 Deploy

Use the same Kubernetes manifests as described in Section 2. Replace the container registry references with your OCI Container Registry (OCIR) paths:

```
<region>.ocir.io/<tenancy>/nexusrag/gateway:latest
<region>.ocir.io/<tenancy>/nexusrag/data-api:latest
<region>.ocir.io/<tenancy>/nexusrag/ui:latest
```

---

## 5. TLS Configuration

### cert-manager with Let's Encrypt

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef:
      name: letsencrypt-prod-key
    solvers:
    - http01:
        ingress:
          class: nginx
```

### Manual TLS

If using pre-existing certificates:

```bash
kubectl create secret tls nexusrag-tls \
  --namespace nexusrag \
  --cert=tls.crt \
  --key=tls.key
```

---

## 6. Monitoring

### Prometheus and Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set grafana.adminPassword=changeme
```

The Gateway exposes a `/metrics` endpoint (Prometheus format) when `METRICS_ENABLED=true`. Add a ServiceMonitor:

```yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: gateway-monitor
  namespace: nexusrag
spec:
  selector:
    matchLabels:
      app: nexusrag-gateway
  endpoints:
  - port: "5000"
    path: /metrics
    interval: 15s
```

Key metrics to dashboard:

- `nexusrag_request_duration_seconds` -- Request latency histogram
- `nexusrag_retrieval_chunks_total` -- Chunks retrieved per query
- `nexusrag_llm_tokens_total` -- Token consumption by type
- `nexusrag_active_websockets` -- Current WebSocket connections
- `nexusrag_reranker_duration_seconds` -- Reranker latency

---

## 7. Backup

### MongoDB Backups

For self-hosted MongoDB:

```bash
# Daily backup via cron
mongodump --uri="$MONGO_URI" --out=/backups/$(date +%Y%m%d)

# Restore
mongorestore --uri="$MONGO_URI" /backups/20260315
```

For MongoDB Atlas, enable automated backups in the Atlas console with a retention policy of at least 7 daily and 4 weekly snapshots.

### Vector Store Backups

FAISS indices are file-based. Back up the vector store directory:

```bash
tar czf vectorstore-backup-$(date +%Y%m%d).tar.gz /data/vectorstore/
```

For Kubernetes, use a CronJob:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: vectorstore-backup
  namespace: nexusrag
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: alpine:3.19
            command: ["sh", "-c", "tar czf /backups/vs-$(date +%Y%m%d).tar.gz /data/vectorstore/"]
            volumeMounts:
            - name: vectorstore
              mountPath: /data/vectorstore
            - name: backups
              mountPath: /backups
          volumes:
          - name: vectorstore
            persistentVolumeClaim:
              claimName: vectorstore-pvc
          - name: backups
            persistentVolumeClaim:
              claimName: backups-pvc
          restartPolicy: OnFailure
```

---

## 8. Progressive Delivery

See `deploy/docs/PROGRESSIVE_DELIVERY.md` for detailed canary and blue-green deployment procedures using Argo Rollouts.

Summary:

1. Install Argo Rollouts in the cluster.
2. Replace Gateway `Deployment` with an Argo `Rollout` resource.
3. Configure a canary strategy that shifts 10% of traffic, waits for analysis, then promotes.
4. Monitor error rates and latency during rollout via the Grafana dashboard.
5. Automated rollback triggers on error rate exceeding 1% or p99 latency exceeding 5 seconds.
