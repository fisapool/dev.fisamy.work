/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Workspace Manager Component - Supports Checklist Items #8 (Onboarding) & #9 (Quotas)
 */

import React, { useState, useEffect, memo } from "react";
import { useAnalytics } from "../../hooks/useAnalytics";

interface Workspace {
  id: string;
  userId: string;
  userEmail: string;
  plan: string;
  status: "provisioning" | "active" | "suspended" | "terminated";
  url?: string;
  resources: {
    cpu: string;
    memory: string;
    disk: string;
    diskUsed: number;
    diskQuota: number;
  };
  idleMinutes: number;
  lastActivity: Date;
  createdAt: Date;
  port: number;
}

interface WorkspaceManagerProps {
  adminMode?: boolean;
}

export const WorkspaceManager: React.FC<WorkspaceManagerProps> = memo(({ adminMode = false }) => {
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);
  const { trackWorkspace, trackError } = useAnalytics();

  useEffect(() => {
    fetchWorkspaces();
  }, []);

  const fetchWorkspaces = async () => {
    try {
      const endpoint = adminMode ? '/api/admin/workspaces' : '/api/user/workspaces';
      const response = await fetch(endpoint, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
      });
      
      if (!response.ok) throw new Error('Failed to fetch workspaces');
      
      const data = await response.json();
      setWorkspaces(data.workspaces || []);
    } catch (error) {
      console.error('Failed to fetch workspaces:', error);
      trackError(error as Error, { context: 'workspace_fetch' });
    } finally {
      setLoading(false);
    }
  };

  const handleWorkspaceAction = async (workspaceId: string, action: 'start' | 'stop' | 'restart' | 'suspend' | 'delete') => {
    try {
      const response = await fetch(`/api/workspaces/${workspaceId}/${action}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) throw new Error(`Failed to ${action} workspace`);

      await trackWorkspace(action as any, workspaceId);
      await fetchWorkspaces(); // Refresh list
    } catch (error) {
      console.error(`Failed to ${action} workspace:`, error);
      trackError(error as Error, { context: `workspace_${action}`, workspaceId });
    }
  };

  const getStatusColor = (status: Workspace["status"]) => {
    switch (status) {
      case "active":
        return "text-green-400 bg-green-400/10 border-green-400/20";
      case "provisioning":
        return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
      case "suspended":
        return "text-orange-400 bg-orange-400/10 border-orange-400/20";
      case "terminated":
        return "text-red-400 bg-red-400/10 border-red-400/20";
      default:
        return "text-neutral-400 bg-neutral-400/10 border-neutral-400/20";
    }
  };

  const getStatusIcon = (status: Workspace["status"]) => {
    switch (status) {
      case "active":
        return "🟢";
      case "provisioning":
        return "🟡";
      case "suspended":
        return "🟠";
      case "terminated":
        return "🔴";
      default:
        return "⚫";
    }
  };

  const formatDiskUsage = (used: number, quota: number) => {
    const usedGB = (used / 1024 / 1024 / 1024).toFixed(1);
    const quotaGB = (quota / 1024 / 1024 / 1024).toFixed(0);
    const percentage = ((used / quota) * 100).toFixed(1);
    return `${usedGB}GB / ${quotaGB}GB (${percentage}%)`;
  };

  const getDiskUsageColor = (used: number, quota: number) => {
    const percentage = (used / quota) * 100;
    if (percentage > 90) return "text-red-400";
    if (percentage > 75) return "text-yellow-400";
    return "text-green-400";
  };

  const formatLastActivity = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor((diffMs % (1000 * 60 * 60)) / (1000 * 60));
    
    if (diffHours > 0) {
      return `${diffHours}h ${diffMinutes}m ago`;
    }
    return `${diffMinutes}m ago`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-neutral-400">Loading workspaces...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">
          {adminMode ? "All Workspaces" : "My Workspaces"}
        </h2>
        <button
          onClick={fetchWorkspaces}
          className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-medium rounded transition-colors"
        >
          Refresh
        </button>
      </div>

      {workspaces.length === 0 ? (
        <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-8 text-center">
          <div className="text-neutral-400 mb-4">No workspaces found</div>
          {!adminMode && (
            <a
              href="#pricing"
              className="inline-flex px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-medium rounded transition-colors"
            >
              Create Your First Workspace
            </a>
          )}
        </div>
      ) : (
        <div className="grid gap-4">
          {workspaces.map((workspace) => (
            <div key={workspace.id} className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <span className="text-lg">{getStatusIcon(workspace.status)}</span>
                    <h3 className="font-bold text-lg">{workspace.id}</h3>
                    <span className={`px-2 py-1 rounded text-xs border ${getStatusColor(workspace.status)}`}>
                      {workspace.status.toUpperCase()}
                    </span>
                  </div>
                  {adminMode && (
                    <div className="text-sm text-neutral-400">
                      User: {workspace.userEmail} • Plan: {workspace.plan.toUpperCase()}
                    </div>
                  )}
                  {workspace.url && workspace.status === "active" && (
                    <a
                      href={workspace.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-emerald-400 hover:text-emerald-300 text-sm underline"
                    >
                      Open Workspace →
                    </a>
                  )}
                </div>
                <div className="flex gap-2">
                  {workspace.status === "active" && (
                    <>
                      <button
                        onClick={() => handleWorkspaceAction(workspace.id, 'stop')}
                        className="px-3 py-1 bg-yellow-500 hover:bg-yellow-400 text-neutral-950 text-sm rounded transition-colors"
                      >
                        Stop
                      </button>
                      <button
                        onClick={() => handleWorkspaceAction(workspace.id, 'restart')}
                        className="px-3 py-1 bg-blue-500 hover:bg-blue-400 text-white text-sm rounded transition-colors"
                      >
                        Restart
                      </button>
                    </>
                  )}
                  {workspace.status === "suspended" && (
                    <button
                      onClick={() => handleWorkspaceAction(workspace.id, 'start')}
                      className="px-3 py-1 bg-green-500 hover:bg-green-400 text-neutral-950 text-sm rounded transition-colors"
                    >
                      Resume
                    </button>
                  )}
                  {adminMode && (
                    <button
                      onClick={() => handleWorkspaceAction(workspace.id, 'delete')}
                      className="px-3 py-1 bg-red-500 hover:bg-red-400 text-white text-sm rounded transition-colors"
                    >
                      Delete
                    </button>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-neutral-400">Resources</div>
                  <div>{workspace.resources.cpu}</div>
                  <div>{workspace.resources.memory}</div>
                </div>
                <div>
                  <div className="text-neutral-400">Disk Usage</div>
                  <div className={getDiskUsageColor(workspace.resources.diskUsed, workspace.resources.diskQuota)}>
                    {formatDiskUsage(workspace.resources.diskUsed, workspace.resources.diskQuota)}
                  </div>
                </div>
                <div>
                  <div className="text-neutral-400">Last Activity</div>
                  <div>{formatLastActivity(workspace.lastActivity)}</div>
                  <div className="text-xs text-neutral-500">
                    Idle: {workspace.idleMinutes}m
                  </div>
                </div>
                <div>
                  <div className="text-neutral-400">Created</div>
                  <div>{workspace.createdAt.toLocaleDateString()}</div>
                  {adminMode && (
                    <div className="text-xs text-neutral-500">
                      Port: {workspace.port}
                    </div>
                  )}
                </div>
              </div>

              {/* Quota Warning */}
              {workspace.resources.diskUsed / workspace.resources.diskQuota > 0.9 && (
                <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded text-red-400 text-sm">
                  ⚠️ Disk quota almost full. Please clean up files or upgrade your plan.
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
});

WorkspaceManager.displayName = "WorkspaceManager";
