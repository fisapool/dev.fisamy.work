/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Health Status Component - Supports Checklist Item #6 (Monitoring & Alerts)
 */

import React, { useState, useEffect, memo } from "react";

interface HealthCheck {
  service: string;
  status: "healthy" | "unhealthy" | "loading";
  responseTime?: number;
  lastCheck: Date;
  endpoint: string;
}

interface HealthStatusProps {
  refreshInterval?: number;
}

export const HealthStatus: React.FC<HealthStatusProps> = memo(({ refreshInterval = 30000 }) => {
  const [healthChecks, setHealthChecks] = useState<HealthCheck[]>([]);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const endpoints = [
    { service: "Frontend", endpoint: "/healthz" },
    { service: "API Backend", endpoint: "/api/healthz" },
    { service: "Coder-lite", endpoint: "/api/workspaces/health" },
    { service: "Database", endpoint: "/api/db/health" },
    { service: "Redis", endpoint: "/api/redis/health" },
  ];

  const checkHealth = async () => {
    const checks = await Promise.all(
      endpoints.map(async ({ service, endpoint }) => {
        const startTime = Date.now();
        try {
          const response = await fetch(endpoint, { 
            method: 'GET',
            timeout: 5000,
            headers: { 'Accept': 'application/json' }
          });
          const responseTime = Date.now() - startTime;
          
          return {
            service,
            endpoint,
            status: response.ok ? "healthy" : "unhealthy",
            responseTime,
            lastCheck: new Date(),
          } as HealthCheck;
        } catch (error) {
          return {
            service,
            endpoint,
            status: "unhealthy",
            responseTime: Date.now() - startTime,
            lastCheck: new Date(),
          } as HealthCheck;
        }
      })
    );
    
    setHealthChecks(checks);
    setLastUpdate(new Date());
  };

  useEffect(() => {
    checkHealth();
    const interval = setInterval(checkHealth, refreshInterval);
    return () => clearInterval(interval);
  }, [refreshInterval]);

  const getStatusIcon = (status: HealthCheck["status"]) => {
    switch (status) {
      case "healthy":
        return "🟢";
      case "unhealthy":
        return "🔴";
      case "loading":
        return "🟡";
      default:
        return "⚫";
    }
  };

  const overallHealth = healthChecks.every(check => check.status === "healthy") ? "healthy" : "unhealthy";

  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-bold flex items-center gap-2">
          {getStatusIcon(overallHealth)} System Health
        </h2>
        <div className="text-sm text-neutral-400">
          Last updated: {lastUpdate.toLocaleTimeString()}
        </div>
      </div>
      
      <div className="space-y-3">
        {healthChecks.map((check) => (
          <div key={check.service} className="flex items-center justify-between p-3 bg-neutral-800 rounded">
            <div className="flex items-center gap-3">
              <span className="text-lg">{getStatusIcon(check.status)}</span>
              <div>
                <div className="font-medium">{check.service}</div>
                <div className="text-sm text-neutral-400">{check.endpoint}</div>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm font-medium">
                {check.status === "healthy" ? "Healthy" : "Unhealthy"}
              </div>
              {check.responseTime && (
                <div className="text-xs text-neutral-400">
                  {check.responseTime}ms
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      
      <button
        onClick={checkHealth}
        className="mt-4 w-full px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-medium rounded transition-colors"
      >
        Refresh Now
      </button>
    </div>
  );
});

HealthStatus.displayName = "HealthStatus";
