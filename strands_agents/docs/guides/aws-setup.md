# AWS Credentials Setup Guide

This guide explains how to configure AWS credentials for local development and production deployment.

## Prerequisites

- AWS CLI installed (version 2.x recommended)
- AWS account with access to:
  - Amazon Bedrock
  - AWS Bedrock AgentCore
  - Amazon Cognito
  - AWS Secrets Manager
  - IAM permissions for creating roles and policies

## Local Development Setup

### 1. Install AWS CLI

If not already installed:

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download and run the AWS CLI MSI installer from:
# https://awscli.amazonaws.com/AWSCLIV2.msi
```

### 2. Configure AWS Credentials

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your access key
- **AWS Secret Access Key**: Your secret key
- **Default region**: `us-west-2` (as specified in PRD)
- **Default output format**: `json`

### 3. Verify Configuration

```bash
# Check AWS identity
aws sts get-caller-identity

# Verify Bedrock access
aws bedrock list-foundation-models --region us-west-2

# Check AgentCore availability (if available in your account)
aws bedrock-agent list-agents --region us-west-2
```

### 4. Create AWS Profile (Optional)

For multiple AWS accounts or environments:

```bash
# Add a new profile
aws configure --profile interlinked-dev

# Use the profile
export AWS_PROFILE=interlinked-dev
```

Add to your `.env`:
```
AWS_PROFILE=interlinked-dev
```

## Required IAM Permissions

Your AWS user/role needs the following permissions:

### Development Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream",
        "bedrock-agent:*",
        "bedrock-agent-runtime:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:us-west-2:*:secret:interlinked-aos-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cognito-idp:AdminInitiateAuth",
        "cognito-idp:AdminGetUser"
      ],
      "Resource": "arn:aws:cognito-idp:us-west-2:*:userpool/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:us-west-2:*:log-group:/aws/bedrock/agentcore/*"
    }
  ]
}
```

### Production Deployment Permissions

Additional permissions needed for production deployment:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "iam:CreateRole",
        "iam:AttachRolePolicy",
        "iam:GetRole",
        "iam:PassRole"
      ],
      "Resource": "arn:aws:iam::*:role/interlinked-aos-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "lambda:CreateFunction",
        "lambda:UpdateFunctionCode",
        "lambda:GetFunction",
        "lambda:InvokeFunction"
      ],
      "Resource": "arn:aws:lambda:us-west-2:*:function:interlinked-aos-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "apigateway:*"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:PutMetricAlarm"
      ],
      "Resource": "*"
    }
  ]
}
```

## Production Secrets Configuration

### 1. Create Secrets in AWS Secrets Manager

```bash
# Create Neo4j credentials secret
aws secretsmanager create-secret \
  --name interlinked-aos-prod \
  --description "Neo4j credentials for Interlinked AOS production" \
  --secret-string '{
    "NEO4J_URI": "neo4j+s://your-instance.databases.neo4j.io",
    "NEO4J_USERNAME": "neo4j",
    "NEO4J_PASSWORD": "your_secure_password",
    "NEO4J_DATABASE": "neo4j"
  }' \
  --region us-west-2
```

### 2. Grant Access to AgentCore

Create an IAM policy that allows the AgentCore agent execution role to access secrets:

```bash
aws iam create-policy \
  --policy-name interlinked-aos-secrets-access \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "secretsmanager:GetSecretValue"
        ],
        "Resource": "arn:aws:secretsmanager:us-west-2:*:secret:interlinked-aos-*"
      }
    ]
  }'
```

## Troubleshooting

### Common Issues

1. **"Unable to locate credentials"**
   - Run `aws configure` again
   - Check `~/.aws/credentials` file exists
   - Verify environment variables aren't overriding

2. **"Access Denied"**
   - Verify IAM permissions
   - Check region matches (us-west-2)
   - Ensure you're using the correct profile

3. **"Bedrock not available in region"**
   - Bedrock is only available in certain regions
   - Ensure you're using us-west-2 as specified

### Debug Commands

```bash
# Check current credentials
aws sts get-caller-identity

# List available profiles
aws configure list-profiles

# Check credential configuration
cat ~/.aws/credentials

# Verify environment variables
env | grep AWS
```

## Security Best Practices

1. **Never commit credentials to git**
   - Use `.env` files (already in `.gitignore`)
   - Use AWS Secrets Manager for production

2. **Use IAM roles when possible**
   - For EC2 instances
   - For Lambda functions
   - For ECS tasks

3. **Rotate credentials regularly**
   - Set up automatic rotation in Secrets Manager
   - Update access keys every 90 days

4. **Use least privilege principle**
   - Only grant necessary permissions
   - Use separate roles for dev/prod

5. **Enable MFA for production**
   - Require MFA for sensitive operations
   - Use MFA for AWS Console access

## Next Steps

After configuring credentials:
1. Test local development environment
2. Deploy to dev environment
3. Configure production secrets
4. Deploy to production

For deployment instructions, see [DEPLOYMENT.md](./DEPLOYMENT.md)
