variable "subscription_id" {
  description = "Azure subscription ID to deploy into."
  type        = string
}

variable "resource_group_name" {
  description = "Name of the resource group to create."
  type        = string
  default     = "olist-rg"
}

variable "location" {
  description = "Azure region. eastus is the cheapest free-tier-eligible region."
  type        = string
  default     = "eastus"
}

variable "environment" {
  description = "Tag value for the `environment` tag."
  type        = string
  default     = "dev"
}

variable "grant_current_user_rbac" {
  description = "Grant Storage Blob Data Contributor to the user running terraform apply. Useful for local dev."
  type        = bool
  default     = true
}
