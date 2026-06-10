terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# Random suffix so the storage account name is globally unique.
resource "random_string" "suffix" {
  length  = 6
  upper   = false
  special = false
  numeric = true
}

resource "azurerm_resource_group" "this" {
  name     = var.resource_group_name
  location = var.location

  tags = local.tags
}

# Storage account with HNS enabled = ADLS Gen2.
resource "azurerm_storage_account" "lake" {
  name                     = "olistdl${random_string.suffix.result}"
  resource_group_name      = azurerm_resource_group.this.name
  location                 = azurerm_resource_group.this.location
  account_tier             = "Standard"
  account_replication_type = "LRS" # cheapest replication; fine for portfolio
  account_kind             = "StorageV2"
  is_hns_enabled           = true # <-- makes this ADLS Gen2 instead of plain Blob

  # Keep things locked down; only this script (account key) or RBAC-granted
  # principals can touch data.
  shared_access_key_enabled       = true
  public_network_access_enabled   = true
  allow_nested_items_to_be_public = false
  min_tls_version                 = "TLS1_2"

  blob_properties {
    versioning_enabled = false
  }

  tags = local.tags
}

# Filesystem (the "container" in ADLS Gen2 terminology) for raw zone.
resource "azurerm_storage_data_lake_gen2_filesystem" "raw" {
  name               = "raw"
  storage_account_id = azurerm_storage_account.lake.id
}

# Lifecycle: move blobs older than 30d from Hot -> Cool tier to keep cost ~ $0.
resource "azurerm_storage_management_policy" "lifecycle" {
  storage_account_id = azurerm_storage_account.lake.id

  rule {
    name    = "cool-after-30d"
    enabled = true
    filters {
      blob_types   = ["blockBlob"]
      prefix_match = ["raw/"]
    }
    actions {
      base_blob {
        tier_to_cool_after_days_since_modification_greater_than = 30
      }
    }
  }
}

# Optional: grant the *current* user (the one running `terraform apply`)
# the Storage Blob Data Contributor role on this account. Lets you use
# DefaultAzureCredential via `az login` instead of the account key.
data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "dev_data_contributor" {
  count                = var.grant_current_user_rbac ? 1 : 0
  scope                = azurerm_storage_account.lake.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

locals {
  tags = {
    project     = "olist-analytics"
    environment = var.environment
    managed_by  = "terraform"
  }
}
