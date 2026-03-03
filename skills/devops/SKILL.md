---
name: devops
description: "DevOps and cloud provisioning with Terraform and AWS support."
version: "1.0.0"
user-invocable: true
metadata:
  capabilities:
    - devops/terraform
    - devops/aws
    - devops/provision
  author: "OpenPango Contributor"
  license: "MIT"
---

# DevOps & Cloud Provisioning Skill

Infrastructure as Code with Terraform and AWS integration.

## Features

- **Terraform**: Plan, apply, destroy infrastructure
- **AWS**: EC2, S3, RDS, Lambda provisioning
- **State Management**: Remote state with S3 backend
- **Mock Mode**: Test without AWS credentials

## Configuration

| Environment Variable | Description |
|---------------------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `AWS_REGION` | AWS region (default: us-east-1) |
| `TF_STATE_BUCKET` | S3 bucket for Terraform state |

## Usage

```python
from skills.devops.terraform import TerraformRunner

runner = TerraformRunner()

# Plan infrastructure
runner.plan()

# Apply changes
runner.apply()

# Destroy infrastructure
runner.destroy()
```
