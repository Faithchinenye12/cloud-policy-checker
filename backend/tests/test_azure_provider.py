from types import SimpleNamespace

import pytest

from backend.app.providers.azure import (
    AzureDiscoveryError,
    discover_storage_accounts,
)


class StorageAccounts:
    def __init__(self, accounts=None, error=None):
        self.accounts = accounts or []
        self.error = error

    def list(self):
        if self.error:
            raise self.error
        return self.accounts


def test_discovers_azure_storage_security_settings():
    account = SimpleNamespace(
        name="auditstorage",
        id="/subscriptions/demo/resourceGroups/security/providers/Microsoft.Storage/storageAccounts/auditstorage",
        location="uksouth",
        allow_blob_public_access=False,
        minimum_tls_version="TLS1_2",
        encryption=SimpleNamespace(
            services=SimpleNamespace(blob=SimpleNamespace(enabled=True))
        ),
    )
    client = SimpleNamespace(storage_accounts=StorageAccounts([account]))

    record = discover_storage_accounts(client=client)[0]

    assert record.resource_type == "storage_account"
    assert record.configuration["public_access_blocked"] is True
    assert record.configuration["encryption_enabled"] is True
    assert record.configuration["minimum_tls_version"] == "TLS1_2"


def test_azure_discovery_returns_safe_error():
    client = SimpleNamespace(
        storage_accounts=StorageAccounts(error=RuntimeError("sensitive detail"))
    )

    with pytest.raises(AzureDiscoveryError) as error:
        discover_storage_accounts(client=client)

    assert "sensitive detail" not in str(error.value)
