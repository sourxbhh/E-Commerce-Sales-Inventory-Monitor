# Terraform — Azure infra for Olist platform

Provisions:

- `olist-rg` resource group (configurable)
- ADLS Gen2 storage account `olistdl<random>` (HNS enabled, LRS, Standard, StorageV2)
- `raw` filesystem (container) under it
- Lifecycle policy: blobs under `raw/` move to **Cool** tier after 30 days
- Optional: grants the current user `Storage Blob Data Contributor` so you can auth via `az login`

## One-time prerequisites

```powershell
# Install
winget install Hashicorp.Terraform
winget install Microsoft.AzureCLI

# Auth
az login
az account set --subscription "<your subscription id>"
```

## Apply

```powershell
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars     # edit subscription_id
terraform init
terraform plan
terraform apply
```

## Wire outputs into `.env`

```powershell
terraform output adls_raw_uri
terraform output storage_account_name
terraform output -raw storage_account_primary_key   # sensitive
```

Copy those into the matching `AZURE_STORAGE_*` / `ADLS_RAW_URI` variables in the repo-root `.env`.

## Tear down (avoid surprise bills)

```powershell
terraform destroy
```

## Cost expectation

Olist parquet is ~40 MB → ~0.8% of the 5 GB free-tier quota. After the 12-month free tier expires, Cool-tier LRS for that volume runs about **$0.01 / month**.
