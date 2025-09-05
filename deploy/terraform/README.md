# AltWallet Checkout Agent - Terraform Deployment

This directory contains Terraform configurations for deploying the AltWallet Checkout Agent on AWS with a complete, production-ready infrastructure.

## Architecture

The Terraform configuration creates a comprehensive AWS infrastructure including:

- **VPC**: Virtual Private Cloud with public and private subnets
- **Application Load Balancer**: HTTPS-enabled load balancer with SSL termination
- **ECS Fargate**: Container orchestration for the application
- **RDS PostgreSQL**: Managed database for persistent data
- **ElastiCache Redis**: In-memory cache for performance
- **Secrets Manager**: Secure storage for sensitive configuration
- **CloudWatch**: Logging and monitoring
- **Auto Scaling**: Automatic scaling based on metrics
- **WAF**: Web Application Firewall for security
- **Backup**: Automated backup solution

## Prerequisites

- [Terraform](https://www.terraform.io/downloads.html) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with appropriate credentials
- AWS account with sufficient permissions
- Domain name (optional, for custom domain)

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/altwallet/checkout-agent.git
cd checkout-agent/deploy/terraform

# Copy example variables
cp terraform.tfvars.example terraform.tfvars
```

### 2. Configure Variables

Edit `terraform.tfvars` with your specific values:

```hcl
# Basic Configuration
project_name = "altwallet-checkout-agent"
environment  = "dev"
aws_region   = "us-west-2"

# Secrets (REQUIRED)
api_key        = "your-api-key-here"
jwt_secret     = "your-jwt-secret-here"
encryption_key = "your-encryption-key-here"
rds_password   = "your-secure-password-here"

# Optional: Custom Domain
domain_name = "checkout.altwallet.com"
create_ssl_certificate = true
create_route53_zone = true
```

### 3. Initialize and Deploy

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan

# Apply the configuration
terraform apply
```

### 4. Access the Application

After deployment, you can access the application:

```bash
# Get the application URL
terraform output application_url

# Check health
curl $(terraform output -raw health_check_url)

# View metrics
curl $(terraform output -raw metrics_url)
```

## Configuration Options

### Environment-Specific Configurations

#### Development Environment

```hcl
# terraform.tfvars.dev
environment = "dev"
desired_count = 1
task_cpu = 512
task_memory = 1024
rds_instance_class = "db.t3.micro"
elasticache_node_type = "cache.t3.micro"
enable_autoscaling = false
enable_backup = false
log_retention_in_days = 7
```

#### Staging Environment

```hcl
# terraform.tfvars.staging
environment = "staging"
desired_count = 2
task_cpu = 1024
task_memory = 2048
rds_instance_class = "db.t3.small"
elasticache_node_type = "cache.t3.small"
enable_autoscaling = true
min_capacity = 2
max_capacity = 5
enable_backup = true
log_retention_in_days = 30
```

#### Production Environment

```hcl
# terraform.tfvars.prod
environment = "prod"
desired_count = 3
task_cpu = 2048
task_memory = 4096
rds_instance_class = "db.r5.large"
elasticache_node_type = "cache.r5.large"
enable_autoscaling = true
min_capacity = 3
max_capacity = 20
enable_backup = true
enable_waf = true
log_retention_in_days = 90
rds_deletion_protection = true
```

### Custom Domain Setup

To use a custom domain:

```hcl
# terraform.tfvars
domain_name = "checkout.altwallet.com"
create_ssl_certificate = true
create_route53_zone = true

# Or use existing Route53 zone
route53_zone_id = "Z1234567890ABC"
certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/12345678-1234-1234-1234-123456789012"
```

### External Services

To use external database or Redis instead of creating new ones:

```hcl
# terraform.tfvars
create_rds = false
create_elasticache = false
database_url = "postgresql://user:password@external-db:5432/altwallet"
redis_url = "redis://external-redis:6379/0"
```

## Module Usage

### Using the Module in Your Own Terraform

```hcl
module "altwallet_checkout_agent" {
  source = "github.com/altwallet/checkout-agent//deploy/terraform/modules/altwallet-checkout-agent"

  # General Configuration
  name_prefix = "my-altwallet"
  environment = "prod"
  region      = "us-west-2"

  # VPC Configuration
  create_vpc = true
  vpc_cidr   = "10.0.0.0/16"

  # Application Configuration
  container_image = "altwallet/checkout-agent"
  container_tag   = "1.0.0"
  desired_count   = 3

  # Secrets
  api_key        = var.api_key
  jwt_secret     = var.jwt_secret
  encryption_key = var.encryption_key
  rds_password   = var.rds_password

  # Auto Scaling
  enable_autoscaling = true
  min_capacity      = 3
  max_capacity      = 20

  # Monitoring
  enable_cloudwatch_alarms = true
  alarm_sns_topic_arn      = aws_sns_topic.alerts.arn

  tags = {
    Project     = "AltWallet"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
```

## Infrastructure Components

### VPC and Networking

- **VPC**: Isolated network environment
- **Public Subnets**: For load balancers and NAT gateways
- **Private Subnets**: For application and database resources
- **Internet Gateway**: Internet access for public resources
- **NAT Gateways**: Internet access for private resources
- **Route Tables**: Traffic routing configuration

### Application Layer

- **Application Load Balancer**: HTTPS termination and traffic distribution
- **ECS Fargate**: Serverless container platform
- **Auto Scaling**: Automatic scaling based on CPU, memory, and request metrics
- **Health Checks**: Application health monitoring

### Data Layer

- **RDS PostgreSQL**: Managed relational database
- **ElastiCache Redis**: In-memory cache and session store
- **Secrets Manager**: Secure storage for sensitive data

### Security

- **Security Groups**: Network-level access control
- **WAF**: Web Application Firewall for HTTP/HTTPS protection
- **SSL/TLS**: End-to-end encryption
- **IAM Roles**: Least-privilege access control

### Monitoring and Logging

- **CloudWatch Logs**: Centralized logging
- **CloudWatch Metrics**: Performance monitoring
- **CloudWatch Alarms**: Automated alerting
- **SNS**: Notification delivery

### Backup and Recovery

- **AWS Backup**: Automated backup solution
- **RDS Snapshots**: Database backup
- **ElastiCache Snapshots**: Cache backup
- **Cross-Region Replication**: Disaster recovery

## Security Considerations

### Network Security

- All application resources are deployed in private subnets
- Security groups restrict access to necessary ports only
- WAF provides additional HTTP/HTTPS protection
- SSL/TLS encryption for all communications

### Data Security

- Secrets stored in AWS Secrets Manager with encryption
- Database encryption at rest and in transit
- Redis encryption in transit
- Regular security updates and patches

### Access Control

- IAM roles with least-privilege permissions
- No hardcoded credentials in configuration
- Separate roles for different components
- Regular access reviews and audits

## Monitoring and Alerting

### CloudWatch Metrics

The deployment includes comprehensive monitoring:

- **Application Metrics**: Request count, response time, error rate
- **Infrastructure Metrics**: CPU, memory, disk usage
- **Database Metrics**: Connection count, query performance
- **Cache Metrics**: Hit rate, memory usage

### CloudWatch Alarms

Automated alerts for:

- High CPU utilization (>80%)
- High memory utilization (>80%)
- High request count (>1000/minute)
- High response time (>2 seconds)
- Service health issues
- Database connection issues

### SNS Notifications

Email notifications for:

- Critical alarms
- Service failures
- Performance degradation
- Security events

## Cost Optimization

### Resource Sizing

- Right-sized instances based on actual usage
- Auto-scaling to handle traffic spikes
- Spot instances for non-critical workloads
- Reserved instances for predictable workloads

### Storage Optimization

- Automated cleanup of old logs
- Lifecycle policies for backups
- Compression for stored data
- Efficient data retention policies

### Network Optimization

- VPC endpoints for AWS services
- Efficient routing and load balancing
- CDN for static content (optional)

## Backup and Disaster Recovery

### Automated Backups

- Daily database backups with 7-day retention
- Weekly cache snapshots
- Cross-region backup replication
- Point-in-time recovery capability

### Disaster Recovery Plan

1. **RTO (Recovery Time Objective)**: 4 hours
2. **RPO (Recovery Point Objective)**: 1 hour
3. **Backup Strategy**: Daily automated backups
4. **Recovery Process**: Automated restoration from backups

## Troubleshooting

### Common Issues

#### Application Not Starting

```bash
# Check ECS service status
aws ecs describe-services --cluster altwallet-checkout-agent-cluster --services altwallet-checkout-agent-service

# Check task logs
aws logs get-log-events --log-group-name /ecs/altwallet-checkout-agent --log-stream-name <stream-name>
```

#### Database Connection Issues

```bash
# Check RDS status
aws rds describe-db-instances --db-instance-identifier altwallet-checkout-agent-db

# Test connectivity
aws rds describe-db-instances --db-instance-identifier altwallet-checkout-agent-db --query 'DBInstances[0].Endpoint'
```

#### Load Balancer Issues

```bash
# Check ALB status
aws elbv2 describe-load-balancers --names altwallet-checkout-agent-alb

# Check target health
aws elbv2 describe-target-health --target-group-arn <target-group-arn>
```

### Debug Commands

```bash
# Get all outputs
terraform output

# Get specific output
terraform output application_url

# Check resource status
terraform show

# Validate configuration
terraform validate

# Format configuration
terraform fmt
```

## Maintenance

### Regular Tasks

1. **Security Updates**: Monthly security patches
2. **Backup Verification**: Weekly backup testing
3. **Performance Review**: Monthly performance analysis
4. **Cost Review**: Monthly cost optimization review

### Updates and Upgrades

```bash
# Update Terraform providers
terraform init -upgrade

# Plan infrastructure changes
terraform plan

# Apply updates
terraform apply

# Update application version
terraform apply -var="container_tag=1.1.0"
```

## Cleanup

To destroy the infrastructure:

```bash
# Plan destruction
terraform plan -destroy

# Destroy infrastructure
terraform destroy

# Confirm destruction
yes
```

**Warning**: This will permanently delete all resources and data. Ensure you have backups before proceeding.

## Support

- **Documentation**: [GitHub Repository](https://github.com/altwallet/checkout-agent)
- **Issues**: [GitHub Issues](https://github.com/altwallet/checkout-agent/issues)
- **Email**: team@altwallet.com

## License

MIT License - see LICENSE file for details.
