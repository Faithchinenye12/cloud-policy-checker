from types import SimpleNamespace

import pytest

from backend.app.providers.gcp import GcpDiscoveryError, discover_storage_buckets


class StorageClient:
    def __init__(self, buckets=None, error=None):
        self.buckets = buckets or []
        self.error = error

    def list_buckets(self, project=None):
        if self.error:
            raise self.error
        return self.buckets


def test_discovers_gcp_bucket_security_settings():
    bucket = SimpleNamespace(
        name="audit-bucket",
        location="EUROPE-WEST2",
        default_kms_key_name="projects/demo/locations/global/keyRings/ring/cryptoKeys/key",
        iam_configuration=SimpleNamespace(
            public_access_prevention="enforced",
            uniform_bucket_level_access_enabled=True,
        ),
    )

    record = discover_storage_buckets(
        client=StorageClient([bucket]),
        project_id="demo-project",
    )[0]

    assert record.cloud_id == "//storage.googleapis.com/audit-bucket"
    assert record.configuration["public_access_blocked"] is True
    assert record.configuration["encryption_enabled"] is True
    assert record.configuration["customer_managed_encryption"] is True
    assert record.configuration["uniform_bucket_level_access"] is True


def test_gcp_discovery_returns_safe_error():
    client = StorageClient(error=RuntimeError("sensitive detail"))

    with pytest.raises(GcpDiscoveryError) as error:
        discover_storage_buckets(client=client, project_id="demo-project")

    assert "sensitive detail" not in str(error.value)
