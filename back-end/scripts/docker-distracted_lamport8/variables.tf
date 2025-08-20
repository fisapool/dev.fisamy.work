variable "template_type" {
  description = "Type of template (no-gpu or gpu)"
  type        = string
  validation {
    condition     = contains(["no-gpu", "gpu"], var.template_type)
    error_message = "template_type must be either 'no-gpu' or 'gpu'."
  }
}

variable "startup_script_timeout" {
  description = "Timeout for startup script in seconds"
  type        = number
  default     = 300
}

variable "autostop_ttl" {
  description = "Time to live in milliseconds"
  type        = number
  default     = 7200000  # 2 hours
}

variable "cpu_limit" {
  description = "CPU limit for the container"
  type        = number
  default     = 2
}

variable "memory_limit" {
  description = "Memory limit in MB"
  type        = number
  default     = 4096
}

variable "gpu_count" {
  description = "Number of GPUs (0 for no-gpu, 1 for gpu)"
  type        = number
  default     = 0
}

variable "enable_debugging" {
  description = "Enable debugging and verbose logging"
  type        = bool
  default     = true
}

variable "health_check_interval" {
  description = "Health check interval in seconds"
  type        = number
  default     = 5
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 3
}
