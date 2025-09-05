# AltWallet Checkout Agent - Helm Chart

This Helm chart deploys the AltWallet Checkout Agent on a Kubernetes cluster with all necessary components for production use.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- Persistent volume support (if persistence is enabled)
- Ingress controller (if ingress is enabled)
- Prometheus Operator (if monitoring is enabled)

## Installation

### Add the Helm Repository

```bash
# Add the AltWallet Helm repository
helm repo add altwallet https://charts.altwallet.com
helm repo update
```

### Install the Chart

```bash
# Install with default values
helm install altwallet-checkout-agent altwallet/altwallet-checkout-agent

# Install with custom values
helm install altwallet-checkout-agent altwallet/altwallet-checkout-agent \
  --values custom-values.yaml

# Install in a specific namespace
helm install altwallet-checkout-agent altwallet/altwallet-checkout-agent \
  --namespace altwallet \
  --create-namespace
```

### Install from Local Chart

```bash
# Install from local chart directory
helm install altwallet-checkout-agent ./altwallet-checkout-agent

# Install with custom values
helm install altwallet-checkout-agent ./altwallet-checkout-agent \
  --values custom-values.yaml
```

## Configuration

### Basic Configuration

```yaml
# values.yaml
image:
  repository: altwallet/checkout-agent
  tag: "1.0.0"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: checkout.altwallet.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: altwallet-checkout-agent-tls
      hosts:
        - checkout.altwallet.com

resources:
  limits:
    cpu: 1000m
    memory: 1Gi
  requests:
    cpu: 500m
    memory: 512Mi
```

### Production Configuration

```yaml
# production-values.yaml
replicaCount: 3

image:
  repository: altwallet/checkout-agent
  tag: "1.0.0"
  pullPolicy: Always

service:
  type: ClusterIP
  port: 8000

ingress:
  enabled: true
  className: "nginx"
  annotations:
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  hosts:
    - host: checkout.altwallet.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: altwallet-checkout-agent-tls
      hosts:
        - checkout.altwallet.com

autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

resources:
  limits:
    cpu: 2000m
    memory: 2Gi
  requests:
    cpu: 1000m
    memory: 1Gi

podDisruptionBudget:
  enabled: true
  minAvailable: 2

redis:
  enabled: true
  auth:
    enabled: true
  master:
    persistence:
      enabled: true
      size: 20Gi
  replica:
    replicaCount: 2
    persistence:
      enabled: true
      size: 20Gi

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s

secrets:
  create: true
  data:
    database-url: "postgresql://user:password@postgres:5432/altwallet"
    redis-url: "redis://:password@redis:6379/0"
    api-key: "your-production-api-key"
    jwt-secret: "your-jwt-secret"
    encryption-key: "your-encryption-key"
```

### Environment-Specific Configurations

#### Development

```yaml
# dev-values.yaml
replicaCount: 1

image:
  tag: "latest"

ingress:
  enabled: false

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 250m
    memory: 256Mi

redis:
  enabled: true
  auth:
    enabled: false
  master:
    persistence:
      enabled: false

monitoring:
  enabled: false

secrets:
  create: true
  data:
    database-url: "postgresql://dev:dev@postgres:5432/altwallet_dev"
    redis-url: "redis://redis:6379/0"
    api-key: "dev-api-key"
    jwt-secret: "dev-jwt-secret"
    encryption-key: "dev-encryption-key"
```

#### Staging

```yaml
# staging-values.yaml
replicaCount: 2

image:
  tag: "staging"

ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: checkout-staging.altwallet.com
      paths:
        - path: /
          pathType: Prefix

autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
  targetCPUUtilizationPercentage: 80

redis:
  enabled: true
  auth:
    enabled: true
  master:
    persistence:
      enabled: true
      size: 10Gi

monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
```

## Configuration Parameters

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imageRegistry` | Global Docker image registry | `""` |
| `global.imagePullSecrets` | Global Docker registry secret names | `[]` |
| `global.storageClass` | Global storage class for dynamic provisioning | `""` |

### Image Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.registry` | Image registry | `docker.io` |
| `image.repository` | Image repository | `altwallet/checkout-agent` |
| `image.tag` | Image tag | `1.0.0` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `image.pullSecrets` | Image pull secrets | `[]` |

### Service Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Service type | `ClusterIP` |
| `service.port` | Service port | `8000` |
| `service.targetPort` | Service target port | `8000` |
| `service.annotations` | Service annotations | `{}` |
| `service.labels` | Service labels | `{}` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `""` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hosts | `[]` |
| `ingress.tls` | Ingress TLS configuration | `[]` |

### Resource Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limits | `1000m` |
| `resources.limits.memory` | Memory limits | `1Gi` |
| `resources.requests.cpu` | CPU requests | `500m` |
| `resources.requests.memory` | Memory requests | `512Mi` |

### Autoscaling Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `autoscaling.enabled` | Enable autoscaling | `false` |
| `autoscaling.minReplicas` | Minimum replicas | `2` |
| `autoscaling.maxReplicas` | Maximum replicas | `10` |
| `autoscaling.targetCPUUtilizationPercentage` | Target CPU utilization | `80` |
| `autoscaling.targetMemoryUtilizationPercentage` | Target memory utilization | `80` |

### Redis Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `redis.enabled` | Enable Redis | `true` |
| `redis.auth.enabled` | Enable Redis authentication | `false` |
| `redis.master.persistence.enabled` | Enable Redis master persistence | `true` |
| `redis.master.persistence.size` | Redis master persistence size | `8Gi` |
| `redis.replica.replicaCount` | Redis replica count | `1` |
| `redis.replica.persistence.enabled` | Enable Redis replica persistence | `true` |
| `redis.replica.persistence.size` | Redis replica persistence size | `8Gi` |

### Monitoring Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `monitoring.enabled` | Enable monitoring | `true` |
| `monitoring.serviceMonitor.enabled` | Enable ServiceMonitor | `true` |
| `monitoring.serviceMonitor.interval` | Scrape interval | `30s` |
| `monitoring.serviceMonitor.scrapeTimeout` | Scrape timeout | `10s` |
| `monitoring.prometheus.enabled` | Enable Prometheus | `false` |
| `monitoring.grafana.enabled` | Enable Grafana | `false` |

### Security Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `podSecurityContext.fsGroup` | Pod security context fsGroup | `1000` |
| `podSecurityContext.runAsNonRoot` | Pod security context runAsNonRoot | `true` |
| `podSecurityContext.runAsUser` | Pod security context runAsUser | `1000` |
| `securityContext.allowPrivilegeEscalation` | Container security context allowPrivilegeEscalation | `false` |
| `securityContext.readOnlyRootFilesystem` | Container security context readOnlyRootFilesystem | `true` |
| `securityContext.runAsNonRoot` | Container security context runAsNonRoot | `true` |
| `securityContext.runAsUser` | Container security context runAsUser | `1000` |

## Environment Variables

The chart supports the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `LOG_LEVEL` | Logging level | `INFO` |
| `LOG_FORMAT` | Logging format | `json` |
| `PORT` | Application port | `8000` |
| `HOST` | Application host | `0.0.0.0` |
| `DATABASE_URL` | Database connection URL | From secret |
| `REDIS_URL` | Redis connection URL | From secret |
| `API_KEY` | API key | From secret |
| `ENABLE_METRICS` | Enable metrics endpoint | `true` |
| `METRICS_PORT` | Metrics port | `9090` |

## Secrets Management

### Using Kubernetes Secrets

```yaml
# Create secrets manually
kubectl create secret generic altwallet-checkout-agent-secrets \
  --from-literal=database-url="postgresql://user:password@postgres:5432/altwallet" \
  --from-literal=redis-url="redis://redis:6379/0" \
  --from-literal=api-key="your-api-key" \
  --from-literal=jwt-secret="your-jwt-secret" \
  --from-literal=encryption-key="your-encryption-key"

# Install with existing secrets
helm install altwallet-checkout-agent altwallet/altwallet-checkout-agent \
  --set secrets.create=false \
  --set secrets.name=altwallet-checkout-agent-secrets
```

### Using External Secret Management

```yaml
# Using External Secrets Operator
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: vault-secret-store
spec:
  provider:
    vault:
      server: "https://vault.example.com"
      path: "secret"
      version: "v2"
      auth:
        kubernetes:
          mountPath: "kubernetes"
          role: "altwallet-checkout-agent"

---
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: altwallet-checkout-agent-secrets
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: vault-secret-store
    kind: SecretStore
  target:
    name: altwallet-checkout-agent-secrets
    creationPolicy: Owner
  data:
  - secretKey: database-url
    remoteRef:
      key: altwallet/database
      property: url
  - secretKey: redis-url
    remoteRef:
      key: altwallet/redis
      property: url
  - secretKey: api-key
    remoteRef:
      key: altwallet/api
      property: key
```

## Health Checks

The chart includes comprehensive health checks:

### Liveness Probe

```yaml
livenessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 30
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 3
```

### Readiness Probe

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 3
```

### Startup Probe

```yaml
startupProbe:
  httpGet:
    path: /health
    port: http
  initialDelaySeconds: 10
  periodSeconds: 10
  timeoutSeconds: 5
  failureThreshold: 30
```

## Monitoring and Observability

### Prometheus Metrics

The chart includes a ServiceMonitor for Prometheus scraping:

```yaml
monitoring:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
```

### Grafana Dashboards

```yaml
monitoring:
  grafana:
    enabled: true
    adminPassword: "admin"
    persistence:
      enabled: true
      size: 1Gi
```

### Logging

The application uses structured JSON logging with configurable levels:

```yaml
env:
  - name: LOG_LEVEL
    value: "INFO"
  - name: LOG_FORMAT
    value: "json"
```

## Network Policies

Enable network policies for enhanced security:

```yaml
networkPolicy:
  enabled: true
  ingress:
    - from:
      - namespaceSelector:
          matchLabels:
            name: ingress-nginx
      ports:
      - protocol: TCP
        port: 8000
```

## Backup and Disaster Recovery

### Persistent Volume Backup

```yaml
backup:
  enabled: true
  schedule: "0 2 * * *"
  retention: "7d"
  storage:
    type: "s3"
    bucket: "altwallet-backups"
    region: "us-west-2"
```

## Troubleshooting

### Common Issues

1. **Pod not starting**: Check resource limits and node capacity
2. **Health check failures**: Verify database and Redis connectivity
3. **Ingress not working**: Check ingress controller and TLS certificates
4. **Metrics not scraping**: Verify Prometheus Operator and ServiceMonitor

### Debug Commands

```bash
# Check pod status
kubectl get pods -l app.kubernetes.io/name=altwallet-checkout-agent

# Check logs
kubectl logs -l app.kubernetes.io/name=altwallet-checkout-agent

# Check service
kubectl get svc -l app.kubernetes.io/name=altwallet-checkout-agent

# Check ingress
kubectl get ingress -l app.kubernetes.io/name=altwallet-checkout-agent

# Check secrets
kubectl get secrets -l app.kubernetes.io/name=altwallet-checkout-agent

# Check configmap
kubectl get configmap -l app.kubernetes.io/name=altwallet-checkout-agent
```

### Health Check Endpoints

- **Health**: `GET /health`
- **Metrics**: `GET /metrics`
- **Readiness**: `GET /health/ready`
- **Liveness**: `GET /health/live`

## Upgrading

### Upgrade the Chart

```bash
# Upgrade to latest version
helm upgrade altwallet-checkout-agent altwallet/altwallet-checkout-agent

# Upgrade with custom values
helm upgrade altwallet-checkout-agent altwallet/altwallet-checkout-agent \
  --values custom-values.yaml

# Check upgrade status
helm status altwallet-checkout-agent
```

### Rollback

```bash
# List releases
helm history altwallet-checkout-agent

# Rollback to previous version
helm rollback altwallet-checkout-agent 1

# Rollback to specific revision
helm rollback altwallet-checkout-agent 2
```

## Uninstalling

```bash
# Uninstall the chart
helm uninstall altwallet-checkout-agent

# Uninstall with namespace
helm uninstall altwallet-checkout-agent --namespace altwallet
```

## Support

- **Documentation**: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- **Issues**: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- **Email**: team@altwallet.com
