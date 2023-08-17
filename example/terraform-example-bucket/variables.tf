
variable "bucket_name" {
  type        = string
  description = "(Required) The name of the S3 bucket that will be created."
}

variable "organization_id" {
  type        = string
  description = "(Required) The unique identifier (ID) of the organization."

  validation {
    condition     = can(regex("^o-[a-z0-9]{10,32}$", var.organization_id))
    error_message = "The organization_id must be a valid AWS Organization ID."
  }
}

variable "security_account_id" {
  type        = string
  description = "(Required) The 12-digit AWS account ID of the security operations account, which should be granted cross-account access."

  validation {
    condition     = can(regex("^\\d{12}$", var.security_account_id))
    error_message = "The security_account_id must be a valid 12-digit AWS account identifier."
  }
}

variable "region" {
  type        = string
  description = "(Optional) The AWS region where the S3 bucket will be created."
  default     = "us-east-2"
}




