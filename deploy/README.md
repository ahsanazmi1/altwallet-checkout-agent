# AltWallet Checkout Agent - Infrastructure Deployment

This directory contains infrastructure-as-code configurations for deploying the AltWallet Checkout Agent in production environments.

## Available Deployment Options

### 🚀 Kubernetes (Helm Charts)
- **Location**: `helm/`
- **Best for**: Container orchestration, microservices, cloud-native deployments
- **Features**: Auto-scaling, service mesh, advanced monitoring, GitOps workflows

### ☁️ AWS Cloud (Terraform)
- **Location**: `terraform/`
- **Best for**: Cloud-native deployments, managed services, enterprise environments
- **Features**: Complete AWS infrastructure, auto-scaling, monitoring, backup, security

## Quick Start

### Kubernetes Deployment

```bash
# Navigate to Helm directory
cd helm/

# Install with default values
helm install altwallet-checkout-agent ./altwallet-checkout-agent

# Install with custom values
helm install altwallet-checkout-agent ./altwallet-checkout-agent \
  --values custom-values.yaml

# Check deployment status
helm status altwallet-checkout-agent
```

### AWS Cloud Deployment

```bash
# Navigate to Terraform directory
cd terraform/

# Copy example variables
cp terraform.tfvars.example terraform.tfvars

# Edit variables
vim terraform.tfvars

# Initialize and deploy
terraform init
terraform plan
terraform apply
```

## Architecture Comparison

| Feature | Kubernetes (Helm) | AWS Cloud (Terraform) |
|---------|------------------|----------------------|
| **Container Orchestration** | ✅ Native Kubernetes | ✅ ECS Fargate |
| **Auto Scaling** | ✅ HPA/VPA | ✅ Application Auto Scaling |
| **Load Balancing** | ✅ Ingress Controller | ✅ Application Load Balancer |
| **Service Discovery** | ✅ Kubernetes DNS | ✅ AWS Service Discovery |
| **Secrets Management** | ✅ Kubernetes Secrets | ✅ AWS Secrets Manager |
| **Monitoring** | ✅ Prometheus/Grafana | ✅ CloudWatch |
| **Logging** | ✅ Centralized Logging | ✅ CloudWatch Logs |
| **Backup** | ✅ Velero/External Tools | ✅ AWS Backup |
| **Security** | ✅ Network Policies | ✅ Security Groups/WAF |
| **Cost** | Variable (depends on cluster) | Pay-per-use |
| **Complexity** | Medium-High | Low-Medium |
| **Vendor Lock-in** | Low | Medium |

## Deployment Scenarios

### Development Environment

**Kubernetes (Helm)**:
```yaml
# dev-values.yaml
replicaCount: 1
resources:
  limits:
    cpu: 500m
    memory: 512Mi
redis:
  enabled: true
  auth:
    enabled: false
monitoring:
  enabled: false
```

**AWS Cloud (Terraform)**:
```hcl
# terraform.tfvars.dev
environment = "dev"
desired_count = 1
task_cpu = 512
task_memory = 1024
rds_instance_class = "db.t3.micro"
enable_autoscaling = false
```

### Staging Environment

**Kubernetes (Helm)**:
```yaml
# staging-values.yaml
replicaCount: 2
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 5
redis:
  enabled: true
  auth:
    enabled: true
monitoring:
  enabled: true
```

**AWS Cloud (Terraform)**:
```hcl
# terraform.tfvars.staging
environment = "staging"
desired_count = 2
enable_autoscaling = true
min_capacity = 2
max_capacity = 5
enable_backup = true
```

### Production Environment

**Kubernetes (Helm)**:
```yaml
# prod-values.yaml
replicaCount: 3
autoscaling:
  enabled: true
  minReplicas: 3
  maxReplicas: 20
redis:
  enabled: true
  auth:
    enabled: true
  master:
    persistence:
      enabled: true
      size: 50Gi
monitoring:
  enabled: true
  prometheus:
    enabled: true
  grafana:
    enabled: true
```

**AWS Cloud (Terraform)**:
```hcl
# terraform.tfvars.prod
environment = "prod"
desired_count = 3
enable_autoscaling = true
min_capacity = 3
max_capacity = 20
enable_backup = true
enable_waf = true
rds_deletion_protection = true
```

## Feature Matrix

### Core Features

| Feature | Kubernetes | AWS Cloud |
|---------|------------|-----------|
| **Application Deployment** | ✅ | ✅ |
| **Database (PostgreSQL)** | ✅ (External) | ✅ (RDS) |
| **Cache (Redis)** | ✅ (External) | ✅ (ElastiCache) |
| **Load Balancing** | ✅ | ✅ |
| **SSL/TLS Termination** | ✅ | ✅ |
| **Health Checks** | ✅ | ✅ |
| **Auto Scaling** | ✅ | ✅ |
| **Rolling Updates** | ✅ | ✅ |
| **Blue/Green Deployments** | ✅ | ✅ |

### Advanced Features

| Feature | Kubernetes | AWS Cloud |
|---------|------------|-----------|
| **Service Mesh** | ✅ (Istio/Linkerd) | ❌ |
| **GitOps** | ✅ (ArgoCD/Flux) | ❌ |
| **Multi-Cloud** | ✅ | ❌ |
| **Managed Services** | ❌ | ✅ |
| **Serverless** | ❌ | ✅ (Fargate) |
| **Cost Optimization** | Manual | ✅ (Auto) |
| **Disaster Recovery** | Manual | ✅ (Automated) |

### Monitoring and Observability

| Feature | Kubernetes | AWS Cloud |
|---------|------------|-----------|
| **Metrics Collection** | ✅ (Prometheus) | ✅ (CloudWatch) |
| **Log Aggregation** | ✅ (ELK/EFK) | ✅ (CloudWatch) |
| **Distributed Tracing** | ✅ (Jaeger) | ✅ (X-Ray) |
| **Alerting** | ✅ (AlertManager) | ✅ (SNS) |
| **Dashboards** | ✅ (Grafana) | ✅ (CloudWatch) |

## Security Comparison

### Network Security

**Kubernetes**:
- Network Policies for micro-segmentation
- Ingress controllers with SSL termination
- Service mesh for mTLS
- RBAC for access control

**AWS Cloud**:
- Security Groups for network access
- WAF for HTTP/HTTPS protection
- VPC for network isolation
- IAM for access control

### Data Security

**Kubernetes**:
- Kubernetes Secrets (base64 encoded)
- External secret management (Vault, etc.)
- Encryption at rest (etcd)
- Pod Security Policies

**AWS Cloud**:
- AWS Secrets Manager with encryption
- KMS for key management
- Encryption at rest and in transit
- IAM policies for data access

## Cost Considerations

### Kubernetes Costs

- **Cluster Management**: EKS, GKE, or AKS costs
- **Compute**: Node instance costs
- **Storage**: Persistent volume costs
- **Networking**: Load balancer and ingress costs
- **Monitoring**: Third-party tool costs

### AWS Cloud Costs

- **Compute**: ECS Fargate pay-per-use
- **Database**: RDS instance costs
- **Cache**: ElastiCache node costs
- **Load Balancer**: ALB costs
- **Storage**: EBS and S3 costs
- **Monitoring**: CloudWatch costs

## Migration Paths

### From Kubernetes to AWS Cloud

1. **Export Configuration**: Extract Helm values and Kubernetes manifests
2. **Map Resources**: Map Kubernetes resources to AWS services
3. **Data Migration**: Migrate data from external databases to RDS
4. **DNS Update**: Update DNS records to point to ALB
5. **Validation**: Test application functionality
6. **Cleanup**: Remove Kubernetes resources

### From AWS Cloud to Kubernetes

1. **Export Configuration**: Extract Terraform outputs and configurations
2. **Create Manifests**: Convert AWS resources to Kubernetes manifests
3. **Data Migration**: Migrate data from RDS to external databases
4. **DNS Update**: Update DNS records to point to ingress
5. **Validation**: Test application functionality
6. **Cleanup**: Remove AWS resources

## Best Practices

### General

- **Infrastructure as Code**: Use version control for all configurations
- **Environment Parity**: Keep environments as similar as possible
- **Security First**: Implement security from the beginning
- **Monitoring**: Set up comprehensive monitoring and alerting
- **Backup**: Implement automated backup and recovery
- **Documentation**: Maintain up-to-date documentation

### Kubernetes Specific

- **Resource Limits**: Set appropriate CPU and memory limits
- **Health Checks**: Implement comprehensive health checks
- **Rolling Updates**: Use rolling updates for zero-downtime deployments
- **Resource Quotas**: Set namespace resource quotas
- **Network Policies**: Implement network segmentation
- **RBAC**: Use role-based access control

### AWS Cloud Specific

- **Least Privilege**: Use IAM roles with minimal permissions
- **Encryption**: Enable encryption at rest and in transit
- **Auto Scaling**: Implement auto scaling for cost optimization
- **Backup**: Use AWS Backup for automated backups
- **Monitoring**: Use CloudWatch for comprehensive monitoring
- **Cost Optimization**: Use AWS Cost Explorer and recommendations

## Support and Documentation

### Kubernetes (Helm)
- **Documentation**: [helm/README.md](helm/README.md)
- **Chart Repository**: [Helm Charts](https://charts.altwallet.com)
- **Examples**: [helm/examples/](helm/examples/)

### AWS Cloud (Terraform)
- **Documentation**: [terraform/README.md](terraform/README.md)
- **Module Registry**: [Terraform Registry](https://registry.terraform.io/modules/altwallet/checkout-agent/aws)
- **Examples**: [terraform/examples/](terraform/examples/)

### General Support
- **Issues**: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- **Documentation**: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- **Email**: team@altwallet.com

## License

MIT License - see LICENSE file for details.
