import boto3
from botocore.stub import Stubber

from backend.app.providers.aws import discover_s3_buckets


def s3_client():
    return boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="testing",
        aws_secret_access_key="testing",
        aws_session_token="testing",
    )


def test_discovers_secure_s3_bucket():
    client = s3_client()
    with Stubber(client) as stubber:
        stubber.add_response(
            "list_buckets",
            {"Buckets": [{"Name": "audit-bucket"}], "Owner": {"ID": "owner"}},
        )
        stubber.add_response(
            "get_bucket_location",
            {"LocationConstraint": "eu-west-2"},
            {"Bucket": "audit-bucket"},
        )
        stubber.add_response(
            "get_public_access_block",
            {"PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            }},
            {"Bucket": "audit-bucket"},
        )
        stubber.add_response(
            "get_bucket_encryption",
            {"ServerSideEncryptionConfiguration": {"Rules": [{
                "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"},
                "BucketKeyEnabled": False,
            }]}},
            {"Bucket": "audit-bucket"},
        )

        records = discover_s3_buckets(client)

    assert len(records) == 1
    assert records[0].cloud_id == "arn:aws:s3:::audit-bucket"
    assert records[0].region == "eu-west-2"
    assert records[0].configuration == {
        "public_access_blocked": True,
        "encryption_enabled": True,
        "discovery_complete": True,
        "discovery_errors": [],
    }


def test_missing_security_configuration_fails_closed():
    client = s3_client()
    with Stubber(client) as stubber:
        stubber.add_response(
            "list_buckets",
            {"Buckets": [{"Name": "legacy-bucket"}], "Owner": {"ID": "owner"}},
        )
        stubber.add_response(
            "get_bucket_location",
            {},
            {"Bucket": "legacy-bucket"},
        )
        stubber.add_client_error(
            "get_public_access_block",
            service_error_code="NoSuchPublicAccessBlockConfiguration",
            expected_params={"Bucket": "legacy-bucket"},
        )
        stubber.add_client_error(
            "get_bucket_encryption",
            service_error_code="ServerSideEncryptionConfigurationNotFoundError",
            expected_params={"Bucket": "legacy-bucket"},
        )

        record = discover_s3_buckets(client)[0]

    assert record.region == "us-east-1"
    assert record.configuration["public_access_blocked"] is False
    assert record.configuration["encryption_enabled"] is False
    assert record.configuration["discovery_complete"] is True
