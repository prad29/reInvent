# AWS Production Deployment Guide for reInvent

This guide provides three AWS deployment architectures for the reInvent platform, scaled for different user loads.

## Table of Contents
- [Small Scale Deployment](#small-scale-deployment-10-100-concurrent-users)
- [Medium Scale Deployment](#medium-scale-deployment-100-1000-concurrent-users)
- [Full Scale Deployment](#full-scale-deployment-1000-10000-concurrent-users)
- [Deployment Checklist](#deployment-checklist-for-all-scales)
- [Performance Tuning](#performance-tuning)

---

## Small Scale Deployment (10-100 concurrent users)

### Infrastructure Components

**Compute:**
- 1x EC2 instance (t3.medium or t3.large)
  - 2-4 vCPUs, 4-8 GB RAM
  - Run both frontend and backend
  - Docker or direct deployment

**Database:**
- RDS PostgreSQL (db.t3.medium)
  - Single AZ deployment
  - 20-50 GB storage with autoscaling
  - Automated backups enabled

**Storage:**
- S3 bucket for file uploads
  - Standard storage class
  - Versioning enabled
- EBS volumes for vector stores (if using ChromaDB locally)

**Caching:**
- ElastiCache Redis (cache.t3.micro)
  - Single node
  - For session management

**Networking:**
- 1 VPC with public/private subnets
- Application Load Balancer (ALB)
- Route 53 for DNS
- ACM for SSL/TLS certificates

**Optional AI Infrastructure:**
- EC2 GPU instance (g4dn.xlarge) if running Ollama locally
  - Or use external API services (OpenAI, etc.)

**Estimated Costs:** $150-300/month

### Architecture Diagram (Conceptual)
```
Internet
    |
Route 53 + ACM
    |
Application Load Balancer
    |
EC2 Instance (t3.medium/large)
├── Frontend (SvelteKit)
└── Backend (FastAPI)
    |
    ├── RDS PostgreSQL (db.t3.medium)
    ├── ElastiCache Redis (cache.t3.micro)
    ├── S3 Bucket (file uploads)
    └── [Optional] EC2 GPU (g4dn.xlarge) for Ollama
```

---

## Medium Scale Deployment (100-1,000 concurrent users)

### Infrastructure Components

**Compute:**
- ECS Fargate or EKS cluster
  - 3-5 tasks/pods (2 vCPU, 4 GB RAM each)
  - Auto-scaling based on CPU/memory (50-80% threshold)
  - Or 3x EC2 instances (t3.xlarge) with Auto Scaling Group

**Database:**
- RDS PostgreSQL (db.r5.large or db.r6g.xlarge)
  - Multi-AZ deployment for HA
  - 100-500 GB storage
  - Read replicas (1-2) for analytics/reporting
  - Automated backups + point-in-time recovery

**Storage:**
- S3 for file uploads
  - Intelligent-Tiering storage class
  - CloudFront CDN for static assets
  - Lifecycle policies for old data
- EFS for shared vector store data (if needed)

**Caching:**
- ElastiCache Redis (cache.r5.large)
  - Redis Cluster mode with 2-3 nodes
  - Multi-AZ with automatic failover

**Vector Database:**
- Managed vector service:
  - Pinecone (managed, external)
  - Or RDS PostgreSQL with pgvector extension
  - Or self-hosted Qdrant on EC2

**Networking:**
- Application Load Balancer (ALB)
  - Multi-AZ
  - WAF for security
- VPC with public/private subnets across 2-3 AZs
- NAT Gateways for private subnet outbound
- Route 53 with health checks
- ACM for SSL/TLS

**AI Infrastructure:**
- Dedicated GPU instances for Ollama (if self-hosting)
  - 2-3x g5.xlarge or g5.2xlarge instances
  - Behind internal load balancer
- Or use AWS SageMaker endpoints
- Or external API services

**Monitoring & Security:**
- CloudWatch for logs and metrics
- CloudWatch Alarms for auto-scaling and alerts
- AWS Systems Manager for secrets
- IAM roles with least privilege
- Security Groups with minimal ports

**CI/CD:**
- CodePipeline + CodeBuild for automated deployments
- ECR for Docker images

**Estimated Costs:**
- Without GPU: $800-2,000/month
- With GPU: $1,500-3,500/month

### Architecture Diagram (Conceptual)
```
Internet
    |
Route 53 + CloudFront CDN
    |
WAF + Application Load Balancer (Multi-AZ)
    |
    ├── ECS/EKS Cluster (3-5 tasks/pods)
    │   ├── Frontend + Backend (Auto-scaling)
    │   └── Container Registry (ECR)
    |
    ├── RDS PostgreSQL (Multi-AZ)
    │   └── Read Replicas (1-2)
    |
    ├── ElastiCache Redis Cluster (2-3 nodes)
    |
    ├── S3 + Intelligent-Tiering
    │   └── CloudFront Distribution
    |
    ├── EFS (shared storage)
    |
    ├── Vector DB (Pinecone/Qdrant/pgvector)
    |
    └── [Optional] GPU Cluster
        └── Internal LB → g5.xlarge instances (2-3)
```

---

## Full Scale Deployment (1,000-10,000+ concurrent users)

### Infrastructure Components

**Compute:**
- EKS (Kubernetes) cluster
  - 10-50 pods across multiple node groups
  - Horizontal Pod Autoscaler (HPA)
  - Cluster Autoscaler for nodes
  - Node groups: c6i.2xlarge or c6i.4xlarge instances
  - Mix of on-demand and Spot instances for cost optimization

**Database:**
- Amazon Aurora PostgreSQL Serverless v2 or Provisioned
  - Writer: db.r6g.2xlarge (or larger)
  - 3-5 Read replicas across AZs
  - Aurora Global Database for DR
  - 500 GB - 2 TB storage with autoscaling
  - Connection pooling (RDS Proxy)

**Storage:**
- S3 for file uploads
  - Multi-region replication
  - Intelligent-Tiering + Glacier for archives
  - CloudFront with multiple edge locations
  - S3 Transfer Acceleration
- EFS for shared application data (if needed)

**Caching:**
- ElastiCache Redis Cluster
  - 6-12 nodes (cache.r6g.xlarge or larger)
  - Multi-AZ with cluster mode enabled
  - Separate clusters for sessions vs. application cache

**Vector Database:**
- Enterprise managed solution:
  - Pinecone (dedicated deployment)
  - Qdrant Cloud (enterprise tier)
  - OpenSearch Service with k-NN plugin
  - Or Aurora PostgreSQL with pgvector at scale

**Networking:**
- Multi-region deployment (primary + DR region)
- Application Load Balancer (ALB) per region
  - Cross-zone load balancing
- Global Accelerator for multi-region routing
- WAF with rate limiting and bot protection
- VPC peering or Transit Gateway for multi-VPC
- Multiple NAT Gateways per AZ
- Route 53 with latency/geolocation routing
- Private Link for secure service connections

**AI Infrastructure:**
- Dedicated GPU cluster for Ollama models
  - 5-20x g5.4xlarge or p3.2xlarge instances
  - EKS node group with GPU support
  - Model caching and load balancing
- SageMaker for custom models
- Bedrock for AWS managed LLMs
- Mix of self-hosted and API services

**Message Queue/Processing:**
- SQS for async job processing
- SNS for notifications
- EventBridge for event-driven workflows

**Monitoring, Logging & Security:**
- CloudWatch with custom dashboards
- CloudWatch Logs Insights
- X-Ray for distributed tracing
- Prometheus + Grafana on EKS
- AWS Secrets Manager for all secrets
- KMS for encryption at rest
- AWS Config for compliance
- GuardDuty for threat detection
- AWS Backup for automated backups
- Separate VPCs per environment (dev/staging/prod)

**CI/CD:**
- CodePipeline with multi-stage deployments
- Blue/Green or Canary deployments
- Automated testing and security scanning
- ECR with image scanning

**Disaster Recovery:**
- Multi-region active-passive or active-active
- Cross-region database replication
- RTO: < 1 hour, RPO: < 5 minutes
- Regular DR drills

**Cost Optimization:**
- Savings Plans / Reserved Instances (30-50% savings)
- Spot instances for non-critical workloads
- Auto-scaling policies
- S3 lifecycle policies
- CloudWatch cost anomaly detection

**Estimated Costs:** $5,000-20,000+/month depending on:
- GPU usage (largest cost driver)
- Database size and IOPS
- Data transfer volumes
- Number of concurrent users

### Architecture Diagram (Conceptual)
```
Global Users
    |
AWS Global Accelerator
    |
    ├── Region 1 (Primary)                  ├── Region 2 (DR)
    │   |                                   │   |
    │   Route 53 (Geo-routing)              │   Route 53
    │   |                                   │   |
    │   WAF + CloudFront (Edge)             │   WAF + CloudFront
    │   |                                   │   |
    │   Application Load Balancer           │   Application Load Balancer
    │   |                                   │   |
    │   EKS Cluster                          │   EKS Cluster
    │   ├── Node Group 1 (c6i instances)    │   └── Standby nodes
    │   ├── Node Group 2 (Spot instances)   │
    │   └── GPU Node Group (g5 instances)   │
    │       ├── 10-50 Application Pods      │
    │       └── Ollama GPU Pods (5-20)      │
    │   |                                   │   |
    │   RDS Proxy                           │   RDS Proxy
    │   |                                   │   |
    │   Aurora PostgreSQL Global            │   Aurora (Read replica)
    │   ├── Writer (db.r6g.2xlarge)         │   └── Synced from Region 1
    │   └── Read Replicas (3-5)             │
    │   |                                   │   |
    │   ElastiCache Redis Cluster           │   ElastiCache Redis
    │   └── 6-12 nodes (Multi-AZ)           │
    │   |                                   │   |
    │   S3 (Multi-region replication) ←─────┼───┘
    │   ├── Intelligent-Tiering             │
    │   └── Glacier for archives            │
    │   |                                   │
    │   Vector Database                     │
    │   ├── OpenSearch/Pinecone/Qdrant      │
    │   └── High availability               │
    │   |                                   │
    │   Monitoring & Security               │
    │   ├── CloudWatch + X-Ray              │
    │   ├── Prometheus + Grafana            │
    │   ├── GuardDuty                       │
    │   └── AWS Config                      │
    |                                       |
    SQS/SNS/EventBridge                     Replicated
```

---

## Deployment Checklist for All Scales

### Pre-Deployment Requirements

#### Environment Variables

Create a `.env.production` file with the following configuration:

```bash
# Core Configuration
DATABASE_URL=postgresql://user:pass@rds-endpoint.region.rds.amazonaws.com:5432/reinvent
REDIS_URL=redis://elasticache-endpoint.region.cache.amazonaws.com:6379

# File Storage (S3)
DATA_DIR=/mnt/efs  # or use S3 with custom storage backend
STORAGE_PROVIDER=s3
AWS_REGION=us-east-1
S3_BUCKET_NAME=reinvent-uploads-prod
AWS_ACCESS_KEY_ID=AKIA...  # Use IAM roles instead when possible
AWS_SECRET_ACCESS_KEY=...  # Use IAM roles instead when possible

# AI Services
OLLAMA_BASE_URL=http://ollama-internal-lb.local:11434
OPENAI_API_BASE_URL=https://api.openai.com/v1
OPENAI_API_KEY=sk-...

# Security
WEBUI_AUTH=true
CORS_ALLOW_ORIGIN=https://yourdomain.com
WEBUI_SECRET_KEY=<generate-secure-random-64-char-key>
JWT_SECRET_KEY=<generate-secure-random-64-char-key>

# Vector Store
VECTOR_DB=qdrant  # or chromadb, opensearch, pinecone
QDRANT_URL=https://qdrant-endpoint.cloud.qdrant.io
QDRANT_API_KEY=...

# Or for OpenSearch
OPENSEARCH_URL=https://opensearch-endpoint.region.es.amazonaws.com
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=...

# Or for Pinecone
PINECONE_API_KEY=...
PINECONE_ENVIRONMENT=us-east-1-aws

# Feature Flags
ENABLE_RAG_WEB_SEARCH=true
ENABLE_IMAGE_GENERATION=true
ENABLE_OAUTH=true

# OAuth Configuration (if enabled)
OAUTH_PROVIDERS=google,microsoft
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...

# Performance
UVICORN_WORKERS=4  # Adjust based on CPU cores
POOL_SIZE=20
MAX_OVERFLOW=40

# Monitoring
ENABLE_TELEMETRY=true
SENTRY_DSN=https://...  # Optional error tracking
```

#### Docker Build & Push

```bash
# Clone repository
git clone https://github.com/your-org/open-webui.git
cd open-webui

# Build production image
docker build -t reinvent:latest -f Dockerfile .

# Tag for ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1
ECR_REPO=${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/reinvent

docker tag reinvent:latest ${ECR_REPO}:latest
docker tag reinvent:latest ${ECR_REPO}:$(git rev-parse --short HEAD)

# Login to ECR
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin ${ECR_REPO}

# Push to ECR
docker push ${ECR_REPO}:latest
docker push ${ECR_REPO}:$(git rev-parse --short HEAD)
```

#### Database Setup

```bash
# Migrations run automatically on startup via config.py
# Or run manually:
cd backend

# Install dependencies
pip install -e ".[postgres]"

# Set DATABASE_URL
export DATABASE_URL="postgresql://user:pass@rds-endpoint/reinvent"

# Run Alembic migrations
alembic upgrade head
```

### Infrastructure as Code (Terraform Example)

Here's a basic Terraform structure for medium-scale deployment:

```hcl
# variables.tf
variable "environment" {
  default = "production"
}

variable "region" {
  default = "us-east-1"
}

variable "app_name" {
  default = "reinvent"
}

# vpc.tf
module "vpc" {
  source = "terraform-aws-modules/vpc/aws"

  name = "${var.app_name}-${var.environment}"
  cidr = "10.0.0.0/16"

  azs             = ["${var.region}a", "${var.region}b", "${var.region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = false  # Use multiple for HA

  tags = {
    Environment = var.environment
    Application = var.app_name
  }
}

# rds.tf
resource "aws_db_instance" "postgres" {
  identifier        = "${var.app_name}-${var.environment}"
  engine            = "postgres"
  engine_version    = "15.4"
  instance_class    = "db.r5.large"
  allocated_storage = 100
  storage_encrypted = true

  db_name  = "reinvent"
  username = "dbadmin"
  password = random_password.db_password.result

  multi_az               = true
  vpc_security_group_ids = [aws_security_group.rds.id]
  db_subnet_group_name   = aws_db_subnet_group.main.name

  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"

  skip_final_snapshot = false
  final_snapshot_identifier = "${var.app_name}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
}

# elasticache.tf
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id       = "${var.app_name}-${var.environment}"
  replication_group_description = "Redis cluster for ${var.app_name}"

  engine               = "redis"
  engine_version       = "7.0"
  node_type            = "cache.r5.large"
  num_cache_clusters   = 3
  parameter_group_name = "default.redis7"
  port                 = 6379

  automatic_failover_enabled = true
  multi_az_enabled          = true

  subnet_group_name  = aws_elasticache_subnet_group.main.name
  security_group_ids = [aws_security_group.redis.id]

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
}

# ecs.tf or eks.tf depending on choice
# s3.tf for storage
# alb.tf for load balancer
# etc.
```

### Key Configuration by Scale

| Component | Small | Medium | Large |
|-----------|-------|--------|-------|
| **Compute** | 1 EC2 | 3-5 containers | 10-50 pods |
| **Database** | Single AZ | Multi-AZ + replicas | Aurora Global |
| **Redis** | Single node | Cluster 2-3 nodes | Cluster 6-12 nodes |
| **Load Balancer** | Single ALB | Multi-AZ ALB | Global Accelerator + ALB |
| **Regions** | 1 | 1 | 2+ (multi-region) |
| **Auto-scaling** | Manual | Basic HPA | Advanced HPA + CA |
| **Monitoring** | CloudWatch | CloudWatch + basic alarms | Full observability stack |
| **DR/Backup** | Automated snapshots | Multi-AZ + backups | Multi-region + continuous backup |
| **CDN** | Optional | CloudFront | CloudFront + edge locations |
| **WAF** | Optional | Basic rules | Advanced + rate limiting |
| **Estimated Users** | 10-100 | 100-1,000 | 1,000-10,000+ |

---

## Performance Tuning

### Application Level

**Backend (FastAPI/Uvicorn):**
```python
# uvicorn configuration
uvicorn open_webui.main:app \
  --workers 4 \
  --host 0.0.0.0 \
  --port 8080 \
  --limit-concurrency 1000 \
  --backlog 2048 \
  --timeout-keep-alive 30
```

**Database Connection Pooling:**
```python
# In backend/open_webui/internal/db.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600,
)
```

**Redis for Sessions:**
```bash
# Enable Redis for session storage
REDIS_URL=redis://elasticache-endpoint:6379/0
```

**WebSocket Tuning:**
- Limit connections per pod: 1,000-5,000
- Use sticky sessions on ALB for WebSocket
- Configure Socket.IO adapter for Redis (multi-pod)

### Database Optimization

**PostgreSQL Configuration:**
```sql
-- Connection pooling with RDS Proxy
-- Recommended settings for RDS PostgreSQL

-- For db.r5.large (16 GB RAM)
shared_buffers = 4GB
effective_cache_size = 12GB
maintenance_work_mem = 1GB
work_mem = 32MB

-- Indexes for common queries
CREATE INDEX idx_chats_user_id ON chats(user_id);
CREATE INDEX idx_messages_chat_id ON messages(chat_id);
CREATE INDEX idx_messages_created_at ON messages(created_at DESC);
CREATE INDEX idx_knowledge_user_id ON knowledge(user_id);

-- Partitioning for large tables (if needed)
CREATE TABLE messages_2024 PARTITION OF messages
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

**Query Optimization:**
- Use EXPLAIN ANALYZE for slow queries
- Add appropriate indexes
- Use connection pooling (RDS Proxy)
- Regular VACUUM and ANALYZE
- Monitor slow query logs

### Storage Optimization

**S3 Configuration:**
```bash
# Use S3 Transfer Acceleration for large files
S3_TRANSFER_ACCELERATION=true

# Configure lifecycle policies
aws s3api put-bucket-lifecycle-configuration \
  --bucket reinvent-uploads-prod \
  --lifecycle-configuration file://lifecycle.json
```

**lifecycle.json:**
```json
{
  "Rules": [
    {
      "Id": "Archive old uploads",
      "Status": "Enabled",
      "Transitions": [
        {
          "Days": 90,
          "StorageClass": "INTELLIGENT_TIERING"
        },
        {
          "Days": 365,
          "StorageClass": "GLACIER"
        }
      ]
    }
  ]
}
```

**CloudFront Configuration:**
- Enable compression (gzip/brotli)
- Cache static assets (images, JS, CSS)
- Use edge locations close to users
- Set appropriate cache TTLs

### Caching Strategy

**Application-level Caching:**
```python
# Cache frequent queries in Redis
# Example: Model list, user permissions, system config

import redis
import json

redis_client = redis.from_url(REDIS_URL)

def get_models_cached():
    cache_key = "models:list"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    models = fetch_models_from_db()
    redis_client.setex(cache_key, 300, json.dumps(models))  # 5 min TTL
    return models
```

**API Response Caching:**
- Cache static responses (model lists, prompts)
- Use ETag/If-None-Match for conditional requests
- Cache embedding computations

### Auto-Scaling Configuration

**ECS/EKS Horizontal Pod Autoscaler:**
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: reinvent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: reinvent
  minReplicas: 3
  maxReplicas: 50
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
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

### Monitoring & Alerts

**CloudWatch Alarms:**
- CPU utilization > 80%
- Memory utilization > 85%
- Database connections > 80% of max
- Redis memory > 80%
- ALB 5xx errors > threshold
- Response time > 2 seconds (p95)
- Disk space < 20%

**Custom Metrics:**
```python
# Push custom metrics to CloudWatch
import boto3

cloudwatch = boto3.client('cloudwatch')

def track_api_latency(endpoint, duration):
    cloudwatch.put_metric_data(
        Namespace='reInvent/API',
        MetricData=[
            {
                'MetricName': 'APILatency',
                'Dimensions': [
                    {'Name': 'Endpoint', 'Value': endpoint}
                ],
                'Value': duration,
                'Unit': 'Milliseconds'
            }
        ]
    )
```

---

## Security Best Practices

### Network Security

1. **VPC Configuration:**
   - Use private subnets for backend services
   - NAT Gateway for outbound traffic
   - Security groups with least privilege
   - Network ACLs as additional layer

2. **WAF Rules:**
   - Rate limiting per IP
   - SQL injection protection
   - XSS protection
   - Block known bad IPs
   - Geo-blocking if needed

3. **Encryption:**
   - TLS 1.3 for all connections
   - RDS encryption at rest
   - S3 encryption at rest (SSE-S3 or KMS)
   - ElastiCache encryption in transit and at rest

### Application Security

1. **Secrets Management:**
   - Use AWS Secrets Manager or Systems Manager Parameter Store
   - Rotate credentials regularly
   - Never commit secrets to Git

2. **IAM Roles:**
   - Use IAM roles for EC2/ECS/EKS (not access keys)
   - Principle of least privilege
   - Separate roles per service

3. **Authentication:**
   - Enable MFA for admin accounts
   - Use OAuth for user authentication
   - Implement rate limiting on login endpoints
   - Session timeout configuration

---

## Cost Optimization Tips

1. **Reserved Instances / Savings Plans:**
   - Commit to 1-3 year terms for 30-50% savings
   - Recommended for: RDS, ElastiCache, steady-state compute

2. **Spot Instances:**
   - Use for non-critical workloads
   - EKS node groups with mix of on-demand and spot
   - Can save 50-90% on compute

3. **Auto-Scaling:**
   - Scale down during off-peak hours
   - Use scheduled scaling for predictable patterns

4. **Storage Optimization:**
   - S3 Intelligent-Tiering for automatic cost optimization
   - Lifecycle policies to move old data to Glacier
   - Delete unused snapshots and AMIs

5. **Monitoring:**
   - Use AWS Cost Explorer
   - Set up budget alerts
   - Tag all resources for cost allocation

---

## Deployment Steps

### Phase 1: Infrastructure Setup
1. Set up VPC, subnets, security groups
2. Deploy RDS PostgreSQL
3. Deploy ElastiCache Redis
4. Create S3 bucket and CloudFront distribution
5. Set up ECR repository

### Phase 2: Application Deployment
1. Build and push Docker image
2. Deploy to ECS/EKS
3. Run database migrations
4. Configure environment variables
5. Set up ALB and target groups

### Phase 3: Monitoring & Security
1. Configure CloudWatch dashboards
2. Set up alarms and notifications
3. Enable WAF rules
4. Configure backup policies
5. Test disaster recovery

### Phase 4: Performance Testing
1. Load testing with realistic traffic
2. Tune auto-scaling policies
3. Optimize database queries
4. Configure caching
5. Monitor and iterate

---

## Support & Maintenance

### Regular Maintenance Tasks

**Daily:**
- Monitor CloudWatch dashboards
- Check error logs
- Review cost anomalies

**Weekly:**
- Review security alerts
- Check backup status
- Update dependencies (if needed)

**Monthly:**
- Security patching
- Performance review
- Cost optimization review
- DR drill

**Quarterly:**
- Architecture review
- Capacity planning
- Disaster recovery testing

### Troubleshooting Common Issues

**High Latency:**
- Check database slow queries
- Review Redis cache hit rate
- Check network latency between services
- Review CloudWatch metrics

**Database Connection Errors:**
- Check RDS Proxy connection pool
- Verify security group rules
- Review connection pool settings in application

**Out of Memory:**
- Increase pod/instance memory limits
- Check for memory leaks
- Review Redis memory usage
- Optimize large query results

---

## Additional Resources

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [EKS Best Practices Guide](https://aws.github.io/aws-eks-best-practices/)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [ElastiCache Best Practices](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/BestPractices.html)

---

## Contact & Support

For issues specific to reInvent deployment, please refer to the main project documentation and community forums.

For AWS-specific questions, consult AWS Support or AWS documentation.
