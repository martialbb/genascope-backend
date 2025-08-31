#!/usr/bin/env python3
"""Test script to debug S3 access"""

import os
import boto3
from botocore.exceptions import ClientError, NoCredentialsError

def test_s3_access():
    print("=== AWS S3 Access Test ===")
    
    # Check environment variables
    print("\n1. Environment Variables:")
    aws_vars = [
        'AWS_ACCESS_KEY_ID',
        'AWS_SECRET_ACCESS_KEY', 
        'AWS_REGION',
        'AWS_S3_BUCKET',
        'AWS_ROLE_ARN',
        'AWS_ROLE_EXTERNAL_ID'
    ]
    
    for var in aws_vars:
        value = os.getenv(var)
        if var == 'AWS_SECRET_ACCESS_KEY':
            print(f"{var}: {'***SET***' if value else 'NOT SET'}")
        elif var == 'AWS_ACCESS_KEY_ID' and value:
            print(f"{var}: {value[:8]}...")
        else:
            print(f"{var}: {value or 'NOT SET'}")
    
    # Test basic S3 connection
    print("\n2. Testing S3 Connection:")
    try:
        region = os.getenv('AWS_REGION', 'us-west-2')
        s3_client = boto3.client('s3', region_name=region)
        print(f"✓ S3 client created successfully (region: {region})")
        
        # Test bucket access
        bucket = os.getenv('AWS_S3_BUCKET')
        if bucket:
            print(f"\n3. Testing bucket access: {bucket}")
            try:
                response = s3_client.head_bucket(Bucket=bucket)
                print(f"✓ Bucket {bucket} is accessible")
                print(f"Response: {response}")
            except ClientError as e:
                error_code = e.response['Error']['Code']
                print(f"✗ Bucket access failed: {error_code} - {e}")
                
                if error_code == 'AccessDenied':
                    print("  This suggests an IAM permission issue")
                elif error_code == 'NoSuchBucket':
                    print("  The bucket doesn't exist or is in a different region")
            
            # Test bucket region
            try:
                location = s3_client.get_bucket_location(Bucket=bucket)
                actual_region = location['LocationConstraint'] or 'us-east-1'
                print(f"Bucket region: {actual_region}")
                if actual_region != region:
                    print(f"⚠️  Region mismatch! Client: {region}, Bucket: {actual_region}")
            except Exception as e:
                print(f"Could not get bucket location: {e}")
        else:
            print("No AWS_S3_BUCKET environment variable set")
    
    except NoCredentialsError:
        print("✗ No AWS credentials found")
    except Exception as e:
        print(f"✗ S3 client creation failed: {e}")
    
    # Test role assumption if configured
    role_arn = os.getenv('AWS_ROLE_ARN')
    if role_arn:
        print(f"\n4. Testing role assumption: {role_arn}")
        try:
            sts_client = boto3.client('sts', region_name=region)
            
            assume_role_params = {
                'RoleArn': role_arn,
                'RoleSessionName': 'genascope-test-session',
                'DurationSeconds': 900  # 15 minutes
            }
            
            external_id = os.getenv('AWS_ROLE_EXTERNAL_ID')
            if external_id:
                assume_role_params['ExternalId'] = external_id
                print(f"Using external ID: {external_id}")
            
            response = sts_client.assume_role(**assume_role_params)
            credentials = response['Credentials']
            print(f"✓ Role assumption successful")
            print(f"Session expires: {credentials['Expiration']}")
            
            # Test S3 with assumed role credentials
            assumed_s3_client = boto3.client(
                's3',
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken'],
                region_name=region
            )
            
            if bucket:
                print(f"\n5. Testing bucket access with assumed role:")
                try:
                    response = assumed_s3_client.head_bucket(Bucket=bucket)
                    print(f"✓ Bucket {bucket} accessible with assumed role")
                except ClientError as e:
                    print(f"✗ Bucket access with assumed role failed: {e}")
            
        except Exception as e:
            print(f"✗ Role assumption failed: {e}")

if __name__ == "__main__":
    test_s3_access()
