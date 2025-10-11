#!/usr/bin/env python3
"""
AWS S3 Bucket Content Checker

This script verifies AWS credentials and lists the contents of a specified S3 bucket.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
import sys


def check_aws_credentials():
    """
    Verify AWS credentials are configured correctly.
    
    Returns:
        dict: AWS account information if credentials are valid
        None: If credentials are invalid or missing
    """
    try:
        sts_client = boto3.client('sts')
        identity = sts_client.get_caller_identity()
        
        print("✅ AWS Credentials Valid!")
        print(f"   Account ID: {identity['Account']}")
        print(f"   User ARN:   {identity['Arn']}")
        print(f"   User ID:    {identity['UserId']}")
        print()
        return identity
        
    except NoCredentialsError:
        print("❌ ERROR: No AWS credentials found.")
        print("   Please configure credentials using:")
        print("   - aws configure")
        print("   - Environment variables (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)")
        print("   - ~/.aws/credentials file")
        return None
        
    except PartialCredentialsError:
        print("❌ ERROR: Incomplete AWS credentials.")
        print("   Please ensure both ACCESS_KEY_ID and SECRET_ACCESS_KEY are set.")
        return None
        
    except ClientError as e:
        print(f"❌ ERROR: Failed to verify credentials: {e}")
        return None


def list_s3_bucket_contents(bucket_name, max_keys=1000):
    """
    List all objects in the specified S3 bucket.
    
    Args:
        bucket_name (str): Name of the S3 bucket (without s3:// prefix)
        max_keys (int): Maximum number of objects to retrieve per request
    
    Returns:
        list: List of objects in the bucket
    """
    try:
        s3_client = boto3.client('s3')
        
        print(f"📦 Listing contents of s3://{bucket_name}/")
        print("=" * 80)
        
        # Use paginator to handle buckets with many objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, PaginationConfig={'MaxItems': max_keys})
        
        objects = []
        total_size = 0
        folder_structure = {}
        
        for page in pages:
            if 'Contents' not in page:
                print("   (Empty bucket or no objects found)")
                return []
            
            for obj in page['Contents']:
                objects.append(obj)
                total_size += obj['Size']
                
                # Extract folder structure
                key = obj['Key']
                if '/' in key:
                    folder = '/'.join(key.split('/')[:-1])
                    folder_structure[folder] = folder_structure.get(folder, 0) + 1
        
        # Display summary
        print(f"\n📊 Summary:")
        print(f"   Total Objects: {len(objects)}")
        print(f"   Total Size:    {format_size(total_size)}")
        
        if folder_structure:
            print(f"\n📁 Folder Structure:")
            for folder, count in sorted(folder_structure.items()):
                print(f"   {folder}/ ({count} files)")
        
        # Display objects
        print(f"\n📄 Objects:")
        print(f"{'Size':<12} {'Last Modified':<25} {'Key'}")
        print("-" * 80)
        
        for obj in sorted(objects, key=lambda x: x['Key']):
            size_str = format_size(obj['Size'])
            modified = obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')
            key = obj['Key']
            print(f"{size_str:<12} {modified:<25} {key}")
        
        return objects
        
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'NoSuchBucket':
            print(f"❌ ERROR: Bucket '{bucket_name}' does not exist.")
        elif error_code == 'AccessDenied':
            print(f"❌ ERROR: Access denied to bucket '{bucket_name}'.")
            print("   Check your IAM permissions for s3:ListBucket action.")
        else:
            print(f"❌ ERROR: Failed to list bucket contents: {e}")
        
        return None
        
    except Exception as e:
        print(f"❌ ERROR: Unexpected error: {e}")
        return None


def format_size(bytes_size):
    """
    Convert bytes to human-readable format.
    
    Args:
        bytes_size (int): Size in bytes
    
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"


def main():
    """Main execution function."""
    print("=" * 80)
    print("AWS S3 Bucket Content Checker")
    print("=" * 80)
    print()
    
    # Step 1: Check AWS credentials
    identity = check_aws_credentials()
    if not identity:
        sys.exit(1)
    
    # Step 2: List S3 bucket contents
    bucket_name = "hackathon-book-store"
    objects = list_s3_bucket_contents(bucket_name)
    
    if objects is None:
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("✅ Script completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()

