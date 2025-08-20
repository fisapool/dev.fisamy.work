output "agent_id" {
  description = "ID of the Coder agent"
  value       = coder_agent.main.id
}

output "code_server_app_id" {
  description = "ID of the Code Server app"
  value       = coder_app.code-server.id
}

output "workspace_name" {
  description = "Name of the current workspace"
  value       = data.coder_workspace.me.name
}

