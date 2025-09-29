# Secrets Management

This document describes how NexusRAG secrets are handled across development, staging, and production environments.

---

## Secret Inventory

The following secrets are required by NexusRAG:

| Secret | Used By | Purpose |
|--------|---------|---------|
| `OPENAI_API_KEY` | Gateway | Authentication with the OpenAI API (or compatible provider) |
| `AZURE_API_KEY` | Gateway | Authentication with Azure OpenAI (when using Azure provider) |
| `MONGO_URI` | Gateway, Data API | MongoDB connection string including credentials |
| `API_KEY` | Data API | API key for authenticating inbound requests to the Data API |
| `REDIS_URL` | Gateway | Redis connection URL (may include password) |
| `QDRANT_API_KEY` | Gateway | Qdrant vector database API key (when using Qdrant backend) |

---

## Development Environment

In development, secrets are stored in a local `.env` file that is loaded by Docker Compose and the application's dotenv library.

### Setup

```bash
cp .env.example .env
# Edit .env with your development keys
```

### Rules

- The `.env` file is listed in `.gitignore` and must never be committed.
- Use development-tier API keys with low rate limits and spending caps.
- Each developer maintains their own `.env` file locally.
- The `.env.example` file contains placeholder values and documentation for each variable.

### Example .env.example

```bash
# OpenAI API key -- get yours at https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-replace-with-your-key

# MongoDB connection string
MONGO_URI=mongodb://localhost:27017

# Data API key -- any string for local development
API_KEY=dev-api-key-change-me

# Redis (optional in development)
# REDIS_URL=redis://localhost:6379/0
```

---

## Staging Environment

Staging uses Kubernetes Secrets managed through a sealed secrets workflow.

### Sealed Secrets

[Sealed Secrets](https://github.com/bitnami-labs/sealed-secrets) encrypts secrets client-side so they can be safely stored in Git. Only the Sealed Secrets controller running in the cluster can decrypt them.

### Setup

```bash
# Install the Sealed Secrets controller
helm repo add sealed-secrets https://bitnami-labs.github.io/sealed-secrets
helm install sealed-secrets sealed-secrets/sealed-secrets \
  --namespace kube-system

# Install kubeseal CLI
brew install kubeseal  # macOS
# or download from https://github.com/bitnami-labs/sealed-secrets/releases
```

### Creating Sealed Secrets

```bash
# Create a regular secret manifest
kubectl create secret generic nexusrag-secrets \
  --namespace nexusrag-staging \
  --from-literal=OPENAI_API_KEY=sk-staging-key \
  --from-literal=MONGO_URI=mongodb+srv://staging-user:pass@staging-cluster.mongodb.net \
  --from-literal=API_KEY=staging-api-key \
  --from-literal=REDIS_URL=redis://redis-staging:6379/0 \
  --dry-run=client -o yaml \
  | kubeseal --format yaml > deploy/staging/sealed-secrets.yaml
```

The resulting `sealed-secrets.yaml` can be committed to Git. It is encrypted and can only be decrypted by the cluster's Sealed Secrets controller.

### Rotation

To rotate a staging secret:

1. Generate a new secret value.
2. Create a new sealed secret using the process above.
3. Commit and push the updated `sealed-secrets.yaml`.
4. Apply: `kubectl apply -f deploy/staging/sealed-secrets.yaml`.
5. Restart affected deployments to pick up the new values:
   ```bash
   kubectl rollout restart deployment/gateway -n nexusrag-staging
   ```

---

## Production Environment

Production secrets require the highest level of protection. NexusRAG supports two approaches: external secret stores and native Kubernetes Secrets with strict RBAC.

### Option A: External Secrets Operator + AWS Secrets Manager

The [External Secrets Operator](https://external-secrets.io/) synchronizes secrets from AWS Secrets Manager (or other providers) into Kubernetes Secrets.

#### Setup

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  --namespace external-secrets --create-namespace
```

#### SecretStore

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: aws-secrets
  namespace: nexusrag
spec:
  provider:
    aws:
      service: SecretsManager
      region: us-east-1
      auth:
        jwt:
          serviceAccountRef:
            name: external-secrets-sa
```

#### ExternalSecret

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: nexusrag-secrets
  namespace: nexusrag
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets
    kind: SecretStore
  target:
    name: nexusrag-secrets
    creationPolicy: Owner
  data:
  - secretKey: OPENAI_API_KEY
    remoteRef:
      key: nexusrag/production/openai
      property: api_key
  - secretKey: MONGO_URI
    remoteRef:
      key: nexusrag/production/mongodb
      property: connection_string
  - secretKey: API_KEY
    remoteRef:
      key: nexusrag/production/data-api
      property: api_key
  - secretKey: REDIS_URL
    remoteRef:
      key: nexusrag/production/redis
      property: url
```

#### Secret Rotation in AWS

1. Update the secret value in AWS Secrets Manager (via console or CLI).
2. The External Secrets Operator refreshes the Kubernetes Secret within the configured `refreshInterval` (1 hour by default).
3. Restart deployments to pick up the new values:
   ```bash
   kubectl rollout restart deployment/gateway -n nexusrag
   ```

For zero-downtime rotation, reduce `refreshInterval` to 5 minutes and use a rolling restart strategy.

### Option B: HashiCorp Vault

For organizations using Vault:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault
  namespace: nexusrag
spec:
  provider:
    vault:
      server: https://vault.example.com
      path: secret
      version: v2
      auth:
        kubernetes:
          mountPath: kubernetes
          role: nexusrag
```

### Option C: OCI Vault

For Oracle Cloud deployments:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: oci-vault
  namespace: nexusrag
spec:
  provider:
    oracle:
      vault: ocid1.vault.oc1...
      region: us-ashburn-1
      auth:
        tenancy: ocid1.tenancy.oc1...
        user: ocid1.user.oc1...
```

---

## RBAC for Secrets

Restrict access to the `nexusrag-secrets` Kubernetes Secret:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: nexusrag-secret-reader
  namespace: nexusrag
rules:
- apiGroups: [""]
  resources: ["secrets"]
  resourceNames: ["nexusrag-secrets"]
  verbs: ["get"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gateway-secret-binding
  namespace: nexusrag
subjects:
- kind: ServiceAccount
  name: gateway-sa
  namespace: nexusrag
roleRef:
  kind: Role
  name: nexusrag-secret-reader
  apiGroup: rbac.authorization.k8s.io
```

Only the service accounts used by NexusRAG pods should have `get` access to the secrets. No `list` or `watch` permissions are granted to limit exposure.

---

## Secret Hygiene

### Do

- Rotate all secrets on a quarterly schedule (monthly for `OPENAI_API_KEY`).
- Use different secret values for each environment (dev, staging, production).
- Audit secret access logs in AWS CloudTrail, Vault audit log, or Kubernetes audit log.
- Use short-lived credentials where possible (e.g., MongoDB Atlas temporary database users).
- Enable encryption at rest for etcd (Kubernetes) if not using an external secret store.

### Do Not

- Commit secrets to Git, even in private repositories.
- Pass secrets via command-line arguments (visible in process listings).
- Log secret values. The Gateway and Data API redact known secret patterns from logs.
- Share secrets via Slack, email, or other unencrypted channels.
- Use the same API key across environments.

---

## Emergency Secret Rotation

If a secret is compromised:

1. **Revoke the compromised credential** at the provider (OpenAI dashboard, MongoDB Atlas, etc.).
2. **Generate a new credential.**
3. **Update the secret store** (AWS Secrets Manager, Vault, or Sealed Secrets).
4. **Force-sync the Kubernetes Secret:**
   ```bash
   # External Secrets Operator
   kubectl annotate externalsecret nexusrag-secrets -n nexusrag \
     force-sync=$(date +%s) --overwrite
   ```
5. **Restart all affected deployments:**
   ```bash
   kubectl rollout restart deployment/gateway -n nexusrag
   kubectl rollout restart deployment/data-api -n nexusrag
   ```
6. **Verify** services are healthy with the new credentials:
   ```bash
   curl https://nexusrag.example.com/api/platform/info
   ```
7. **Audit** logs for unauthorized usage during the exposure window.
8. **Document** the incident and update the rotation schedule.
