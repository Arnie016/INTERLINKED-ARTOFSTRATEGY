#!/usr/bin/env python3
"""
AWS S3 Bucket Folder Counter

This script verifies AWS credentials and counts the number of folders and their contents in a specified S3 bucket.
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


def count_s3_bucket_folders(bucket_name, max_keys=1000):
    """
    Count folders and their contents in the specified S3 bucket.
    
    Args:
        bucket_name (str): Name of the S3 bucket (without s3:// prefix)
        max_keys (int): Maximum number of objects to retrieve per request
    
    Returns:
        dict: Dictionary with folder counts and statistics
    """
    try:
        s3_client = boto3.client('s3')
        
        print(f"📦 Counting folders and contents in s3://{bucket_name}/")
        print("=" * 80)
        
        # Use paginator to handle buckets with many objects
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=bucket_name, PaginationConfig={'MaxItems': max_keys})
        
        folder_counts = {}
        total_objects = 0
        root_files = 0
        
        for page in pages:
            if 'Contents' not in page:
                print("   (Empty bucket or no objects found)")
                return {"folders": 0, "total_objects": 0, "root_files": 0, "folder_details": {}}
            
            for obj in page['Contents']:
                total_objects += 1
                key = obj['Key']
                
                # Check if it's a root-level file or in a folder
                if '/' in key:
                    # Extract folder path
                    folder = '/'.join(key.split('/')[:-1])
                    folder_counts[folder] = folder_counts.get(folder, 0) + 1
                else:
                    # Root-level file
                    root_files += 1
        
        # Display summary
        print(f"\n📊 Bucket Summary:")
        print(f"   Total Objects: {total_objects}")
        print(f"   Root Files:    {root_files}")
        print(f"   Folders:       {len(folder_counts)}")
        
        if folder_counts:
            print(f"\n📁 Folder Contents:")
            print(f"{'Folder':<40} {'Files'}")
            print("-" * 50)
            
            # Sort folders by file count (descending)
            sorted_folders = sorted(folder_counts.items(), key=lambda x: x[1], reverse=True)
            
            for folder, count in sorted_folders:
                print(f"{folder:<40} {count}")
        
        return {
            "folders": len(folder_counts),
            "total_objects": total_objects,
            "root_files": root_files,
            "folder_details": folder_counts
        }
        
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
    print("AWS S3 Bucket Folder Counter")
    print("=" * 80)
    print()
    
    # Step 1: Check AWS credentials
    identity = check_aws_credentials()
    if not identity:
        sys.exit(1)
    
    # Step 2: Count S3 bucket folders and contents
    bucket_name = "hackathon-book-store"
    folder_stats = count_s3_bucket_folders(bucket_name)
    
    if folder_stats is None:
        sys.exit(1)
    
    print()
    print("=" * 80)
    print("✅ Script completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    main()

