/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 * 
 * Status Page Component - Supports Checklist Item #12 (Incident Response)
 */

import React, { memo } from "react";

interface Incident {
  id: string;
  title: string;
  status: "investigating" | "identified" | "monitoring" | "resolved";
  severity: "minor" | "major" | "critical";
  description: string;
  createdAt: Date;
  updatedAt: Date;
  updates: IncidentUpdate[];
}

interface IncidentUpdate {
  id: string;
  message: string;
  timestamp: Date;
  status: Incident["status"];
}

interface Service {
  name: string;
  status: "operational" | "degraded" | "partial_outage" | "major_outage";
  description?: string;
}

const mockServices: Service[] = [
  { name: "VS Code Workspaces", status: "operational" },
  { name: "Authentication", status: "operational" },
  { name: "File Storage", status: "operational" },
  { name: "GPU Instances", status: "operational" },
  { name: "API", status: "operational" },
];

const mockIncidents: Incident[] = [
  // Example incident - in production this would come from your backend
];

export const StatusPage: React.FC = memo(() => {
  const getStatusColor = (status: Service["status"]) => {
    switch (status) {
      case "operational":
        return "text-green-400 bg-green-400/10 border-green-400/20";
      case "degraded":
        return "text-yellow-400 bg-yellow-400/10 border-yellow-400/20";
      case "partial_outage":
        return "text-orange-400 bg-orange-400/10 border-orange-400/20";
      case "major_outage":
        return "text-red-400 bg-red-400/10 border-red-400/20";
      default:
        return "text-neutral-400 bg-neutral-400/10 border-neutral-400/20";
    }
  };

  const getStatusIcon = (status: Service["status"]) => {
    switch (status) {
      case "operational":
        return "🟢";
      case "degraded":
        return "🟡";
      case "partial_outage":
        return "🟠";
      case "major_outage":
        return "🔴";
      default:
        return "⚫";
    }
  };

  const getSeverityColor = (severity: Incident["severity"]) => {
    switch (severity) {
      case "minor":
        return "text-yellow-400 bg-yellow-400/10";
      case "major":
        return "text-orange-400 bg-orange-400/10";
      case "critical":
        return "text-red-400 bg-red-400/10";
      default:
        return "text-neutral-400 bg-neutral-400/10";
    }
  };

  const allOperational = mockServices.every(service => service.status === "operational");
  const hasActiveIncidents = mockIncidents.some(incident => incident.status !== "resolved");

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      {/* Header */}
      <div className="border-b border-neutral-800 bg-neutral-900/50">
        <div className="max-w-4xl mx-auto px-6 py-8">
          <h1 className="text-3xl font-bold mb-2">code.fisamy.work Status</h1>
          <div className="flex items-center gap-3">
            <span className="text-2xl">
              {allOperational && !hasActiveIncidents ? "🟢" : "🔴"}
            </span>
            <span className="text-lg">
              {allOperational && !hasActiveIncidents 
                ? "All Systems Operational" 
                : "Service Disruption"
              }
            </span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-6 py-8 space-y-8">
        {/* Current Status */}
        <section>
          <h2 className="text-xl font-bold mb-4">Current Status</h2>
          <div className="space-y-3">
            {mockServices.map((service) => (
              <div key={service.name} className="flex items-center justify-between p-4 bg-neutral-900 border border-neutral-800 rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="text-lg">{getStatusIcon(service.status)}</span>
                  <div>
                    <div className="font-medium">{service.name}</div>
                    {service.description && (
                      <div className="text-sm text-neutral-400">{service.description}</div>
                    )}
                  </div>
                </div>
                <div className={`px-3 py-1 rounded-full text-xs border ${getStatusColor(service.status)}`}>
                  {service.status.replace('_', ' ').toUpperCase()}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Active Incidents */}
        {hasActiveIncidents && (
          <section>
            <h2 className="text-xl font-bold mb-4">Active Incidents</h2>
            <div className="space-y-4">
              {mockIncidents
                .filter(incident => incident.status !== "resolved")
                .map((incident) => (
                  <div key={incident.id} className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
                    <div className="flex items-start justify-between mb-3">
                      <h3 className="font-bold text-lg">{incident.title}</h3>
                      <div className="flex gap-2">
                        <span className={`px-2 py-1 rounded text-xs ${getSeverityColor(incident.severity)}`}>
                          {incident.severity.toUpperCase()}
                        </span>
                        <span className="px-2 py-1 rounded text-xs bg-neutral-800 text-neutral-300">
                          {incident.status.replace('_', ' ').toUpperCase()}
                        </span>
                      </div>
                    </div>
                    <p className="text-neutral-300 mb-4">{incident.description}</p>
                    <div className="text-sm text-neutral-400">
                      Last updated: {incident.updatedAt.toLocaleString()}
                    </div>
                  </div>
                ))}
            </div>
          </section>
        )}

        {/* Recent Incidents */}
        <section>
          <h2 className="text-xl font-bold mb-4">Recent Incidents</h2>
          {mockIncidents.length === 0 ? (
            <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6 text-center">
              <span className="text-green-400 text-2xl">🎉</span>
              <p className="mt-2 text-neutral-300">No incidents in the last 7 days</p>
            </div>
          ) : (
            <div className="space-y-4">
              {mockIncidents.map((incident) => (
                <div key={incident.id} className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-medium">{incident.title}</h3>
                    <span className="text-sm text-neutral-400">
                      {incident.createdAt.toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>

        {/* Subscribe to Updates */}
        <section className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-bold mb-3">Stay Updated</h2>
          <p className="text-neutral-300 mb-4">
            Get notified about service updates and incidents
          </p>
          <div className="flex gap-3">
            <input
              type="email"
              placeholder="your@email.com"
              className="flex-1 px-3 py-2 bg-neutral-800 border border-neutral-700 rounded focus:border-emerald-500 focus:outline-none"
            />
            <button className="px-4 py-2 bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-medium rounded transition-colors">
              Subscribe
            </button>
          </div>
        </section>

        {/* Contact Support */}
        <section className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
          <h2 className="text-lg font-bold mb-3">Need Help?</h2>
          <p className="text-neutral-300 mb-4">
            If you're experiencing issues not listed here, please contact support.
          </p>
          <div className="flex gap-4">
            <a
              href="mailto:support@code.fisamy.work"
              className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-100 rounded transition-colors"
            >
              Email Support
            </a>
            <a
              href="#/contact"
              className="px-4 py-2 border border-neutral-700 hover:border-neutral-600 text-neutral-100 rounded transition-colors"
            >
              Contact Form
            </a>
          </div>
        </section>
      </div>
    </div>
  );
});

StatusPage.displayName = "StatusPage";
