output "storage_account_name" {
  description = "Name of the ADLS Gen2 storage account. Set AZURE_STORAGE_ACCOUNT in .env to this."
  value       = azurerm_storage_account.lake.name
}

output "storage_account_primary_key" {
  description = "Primary access key. Set AZURE_STORAGE_KEY in .env for local-dev auth."
  value       = azurerm_storage_account.lake.primary_access_key
  sensitive   = true
}

output "raw_container_name" {
  description = "Filesystem (container) name for the raw zone."
  value       = azurerm_storage_data_lake_gen2_filesystem.raw.name
}

output "adls_raw_uri" {
  description = "abfss URI to set as ADLS_RAW_URI in .env."
  value       = "abfss://${azurerm_storage_data_lake_gen2_filesystem.raw.name}@${azurerm_storage_account.lake.name}.dfs.core.windows.net/"
}
