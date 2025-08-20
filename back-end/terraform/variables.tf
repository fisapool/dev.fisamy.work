variable "coder_url" {
  description = "Coder instance URL"
  type        = string
  default     = "https://coder.fisamy.work"
}

variable "coder_token" {
  description = "Coder API token with admin permissions"
  type        = string
  sensitive   = true
}

