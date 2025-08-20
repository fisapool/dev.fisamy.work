import React, { useEffect, useMemo, useState } from "react";
import { Play, Square, Power, Globe, Rocket, Plus, Trash2, ExternalLink, Loader2 } from "lucide-react";
import { safeLog } from "./utils/safeJson.js";

/**
 * Unified Dashboard (single-file starter)
 * - Tailwind-only UI (no shadcn dependency).
 * - Talks to a server-side BFF at VITE_PUBLIC_API_BASE (default: /api).
 * - Replace placeholder Domain Manager <iframe> with your embed when ready.
 *
 * Expected BFF endpoints (JSON):
 *   GET   /me -> { id, name, plan: { name, vcpu, ram_gb, disk_gb } }
 *   GET   /usage -> { vcpu: number, ram_gb: number, disk_gb: number }
 *   GET   /workspaces -> { items: Workspace[] }
 *   POST  /workspaces -> { id }  (create from template, body: { templateId, name })
 *   POST  /workspaces/:id/start -> { ok: true }
 *   POST  /workspaces/:id/stop  -> { ok: true }
 *   DELETE /workspaces/:id      -> { ok: true }
 *   GET   /templates -> { items: Template[] }
 *   GET   /domains -> { items: DomainBinding[] }
 *   POST  /domains (body: { domain, workspaceId }) -> { id }
 *   POST  /domains/:id/verify -> { ok: true }
 *
 * NOTE: Keep provider tokens on the server. Frontend must never hold Coder tokens.
 */

const API_BASE = import.meta?.env?.VITE_PUBLIC_API_BASE || "/api";

// ---- Types (JSDoc) ----
/**
 * @typedef {Object} Workspace
 * @property {string} id
 * @property {string} name
 * @property {string} [url] - e.g. vscode--name--user.dev.fisamy.work
 * @property {string} [templateName] - e.g. "VSCode AI Template"
 * @property {'running'|'stopped'|'starting'|'stopping'|'suspended'} status
 */

/**
 * @typedef {Object} Template
 * @property {string} id
 * @property {string} name
 * @property {string} [tagline]
 * @property {boolean} [recommended]
 */

/**
 * @typedef {Object} DomainBinding
 * @property {string} id
 * @property {string} domain
 * @property {string|null} [workspaceId]
 * @property {'verified'|'pending'|'error'} status
 */

/**
 * @typedef {Object} Plan
 * @property {string} name
 * @property {number} vcpu
 * @property {number} ram_gb
 * @property {number} disk_gb
 */

// ---- API helper ----
/**
 * @template T
 * @param {string} path
 * @param {RequestInit} [opts]
 * @returns {Promise<T>}
 */
async function api(path, opts = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    ...opts,
  });
  if (!res.ok) throw new Error(`${opts.method || "GET"} ${path} -> ${res.status}`);
  return await res.json();
}

// ---- Small UI primitives ----
const Card = ({ className = "", children }) => (
  <div className={`rounded-2xl border border-neutral-800 bg-neutral-900/60 shadow-sm ${className}`}>{children}</div>
);

const SectionTitle = ({ children, action }) => (
  <div className="mb-3 flex items-center justify-between">
    <h2 className="text-xl font-semibold tracking-tight">{children}</h2>
    {action}
  </div>
);

const StatBar = ({ used, total, label }) => {
  const pct = Math.min(100, Math.round((used / Math.max(1, total)) * 100));
  const bar = pct <= 60 ? "bg-green-500" : pct <= 85 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between text-sm text-neutral-300">
        <span>{label}</span>
        <span>
          {used} / {total} ({pct}%)
        </span>
      </div>
      <div className="h-2.5 w-full rounded-full bg-neutral-800">
        <div className={`h-2.5 rounded-full ${bar}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
};

const Pill = ({ tone = "gray", children }) => {
  const map = {
    green: "bg-green-500/15 text-green-400 border-green-500/30",
    yellow: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
    red: "bg-red-500/15 text-red-400 border-red-500/30",
    gray: "bg-neutral-700/30 text-neutral-300 border-neutral-600",
  };
  return <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs ${map[tone]}`}>{children}</span>;
};

// ---- Dashboard ----
const Dashboard = () => {
  const [me, setMe] = useState(null);
  const [usage, setUsage] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [domains, setDomains] = useState([]);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const refreshAll = async () => {
    setLoading(true);
    try {
      const [{ id, name, plan }, u, w, t, d] = await Promise.all([
        api("/me"),
        api("/usage"),
        api("/workspaces"),
        api("/templates"),
        api("/domains"),
      ]);
      setMe({ id, name, plan });
      setUsage(u);
      setWorkspaces(w.items);
      setTemplates(t.items);
      setDomains(d.items);
    } catch (e) {
      safeLog(e, 'Error in refreshAll:');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refreshAll(); }, []);

  const activeCount = useMemo(() => workspaces.filter(w => w.status === "running").length, [workspaces]);
  const suspendedCount = useMemo(() => workspaces.filter(w => ["stopped", "suspended"].includes(w.status)).length, [workspaces]);

  async function start(id) {
    optimisticStatus(id, "starting");
    try { await api(`/workspaces/${id}/start`, { method: "POST" }); optimisticStatus(id, "running"); } 
    catch { optimisticStatus(id, "stopped"); }
  }
  async function stop(id) {
    optimisticStatus(id, "stopping");
    try { await api(`/workspaces/${id}/stop`, { method: "POST" }); optimisticStatus(id, "stopped"); } 
    catch { optimisticStatus(id, "running"); }
  }
  async function remove(id) {
    optimisticDelete(id);
    try { await api(`/workspaces/${id}`, { method: "DELETE" }); }
    catch { refreshAll(); }
  }
  function optimisticStatus(id, status) {
    setWorkspaces(ws => ws.map(w => (w.id === id ? { ...w, status } : w)));
  }
  function optimisticDelete(id) {
    setWorkspaces(ws => ws.filter(w => w.id !== id));
  }

  async function createFromTemplate(t) {
    const name = t.recommended ? `my-first-${slug(t.name)}` : `${slug(t.name)}-${Date.now().toString().slice(-4)}`;
    setCreating(true);
    try {
      const { id } = await api(`/workspaces`, { method: "POST", body: JSON.stringify({ templateId: t.id, name }) });
      setWorkspaces(ws => [{ id, name, templateName: t.name, status: "starting" }, ...ws]);
      // Let background poll bring it to running
      setTimeout(refreshAll, 2000);
    } catch (e) {
      safeLog(e, 'Error creating workspace:');
    } finally {
      setCreating(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center text-neutral-300">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" /> Loading your dashboard...
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl p-6">
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Welcome back{me?.name ? `, ${me.name}` : ""} 👋</h1>
          <p className="mt-1 text-sm text-neutral-400">Manage workspaces, billing and custom domains in one place.</p>
        </div>
        <a href="/" className="inline-flex items-center gap-2 rounded-xl border border-neutral-800 bg-neutral-900 px-4 py-2 text-sm text-neutral-200 hover:bg-neutral-800">
          <ExternalLink className="h-4 w-4" />
          Back to site
        </a>
      </div>

      {/* Top grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card className="p-5">
          <SectionTitle>Quick stats</SectionTitle>
          <div className="grid grid-cols-3 gap-4">
            <div className="rounded-xl bg-neutral-800/50 p-4">
              <div className="text-xs text-neutral-400">Active workspaces</div>
              <div className="mt-1 text-2xl font-semibold text-green-400">{activeCount}</div>
            </div>
            <div className="rounded-xl bg-neutral-800/50 p-4">
              <div className="text-xs text-neutral-400">Suspended</div>
              <div className="mt-1 text-2xl font-semibold text-yellow-400">{suspendedCount}</div>
            </div>
            <div className="rounded-xl bg-neutral-800/50 p-4">
              <div className="text-xs text-neutral-400">Custom domains</div>
              <div className="mt-1 text-2xl font-semibold text-blue-400">{domains.length}</div>
            </div>
          </div>
        </Card>

        <Card className="p-5">
          <SectionTitle>Current plan</SectionTitle>
          {me && usage ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-sm text-neutral-300"><span>{me.plan.name}</span><a className="text-blue-400 hover:underline" href="/billing">Manage subscription</a></div>
              <StatBar label="CPU (vCPU)" used={usage.vcpu} total={me.plan.vcpu} />
              <StatBar label="RAM (GB)" used={usage.ram_gb} total={me.plan.ram_gb} />
              <StatBar label="Disk (GB)" used={usage.disk_gb} total={me.plan.disk_gb} />
            </div>
          ) : (
            <div className="text-sm text-neutral-400">Plan details unavailable.</div>
          )}
        </Card>
      </div>

      {/* Workspaces */}
      <div className="mt-8">
        <SectionTitle
          action={
            <button onClick={() => {
              const rec = templates.find(t => t.recommended) || templates[0];
              if (rec) createFromTemplate(rec);
            }}
              disabled={!templates.length || creating}
              className="inline-flex items-center gap-2 rounded-xl bg-white/10 px-3 py-2 text-sm text-white hover:bg-white/15 disabled:opacity-50">
              <Plus className="h-4 w-4" /> Create workspace
            </button>
          }
        >
          Your workspaces
        </SectionTitle>

        <Card>
          <div className="divide-y divide-neutral-800">
            {workspaces.length === 0 && (
              <div className="p-6 text-sm text-neutral-400">No workspaces yet. Launch one below.</div>
            )}
            {workspaces.map(w => (
              <div key={w.id} className="grid grid-cols-1 gap-3 p-4 md:grid-cols-12 md:items-center">
                <div className="md:col-span-4">
                  <div className="font-medium">{w.name}</div>
                  <div className="text-xs text-neutral-400">{w.templateName || "Custom"}</div>
                </div>
                <div className="md:col-span-4">
                  <div className="flex items-center gap-2">
                    {statusPill(w.status)}
                    {w.url && (
                      <a className="inline-flex items-center gap-1 text-sm text-blue-400 hover:underline" href={w.url} target="_blank" rel="noreferrer">
                        Launch IDE <ExternalLink className="h-3.5 w-3.5" />
                      </a>
                    )}
                  </div>
                </div>
                <div className="md:col-span-4 flex gap-2 md:justify-end">
                  {w.status === "running" ? (
                    <button onClick={() => stop(w.id)} className="inline-flex items-center gap-2 rounded-xl border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800">
                      <Square className="h-4 w-4" /> Stop
                    </button>
                  ) : (
                    <button onClick={() => start(w.id)} className="inline-flex items-center gap-2 rounded-xl border border-neutral-700 px-3 py-1.5 text-sm hover:bg-neutral-800">
                      <Power className="h-4 w-4" /> Start
                    </button>
                  )}
                  <button onClick={() => remove(w.id)} className="inline-flex items-center gap-2 rounded-xl border border-red-900/60 bg-red-900/20 px-3 py-1.5 text-sm text-red-300 hover:bg-red-900/30">
                    <Trash2 className="h-4 w-4" /> Delete
                  </button>
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Templates */}
      <div className="mt-8">
        <SectionTitle>🚀 Launch a new workspace</SectionTitle>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          {templates.map(t => (
            <Card key={t.id} className="p-5">
              <div className="flex items-start justify-between">
                <div>
                  <div className="font-semibold">{t.name}</div>
                  <div className="mt-1 text-sm text-neutral-400">{t.tagline || "Preconfigured environment"}</div>
                </div>
                {t.recommended && <Pill tone="green">Recommended</Pill>}
              </div>
              <button onClick={() => createFromTemplate(t)} disabled={creating} className="mt-4 inline-flex items-center gap-2 rounded-xl bg-white text-neutral-900 px-3 py-2 text-sm font-medium hover:bg-white/90 disabled:opacity-50">
                <Rocket className="h-4 w-4" /> Launch
              </button>
            </Card>
          ))}
          {!templates.length && (
            <Card className="p-5 text-sm text-neutral-400">No templates exposed by the provider.</Card>
          )}
        </div>
      </div>

      {/* Domains */}
      <div className="mt-8">
        <SectionTitle
          action={<a href="#" className="text-sm text-blue-400 hover:underline">Add domain</a>}
        >
          🌐 Custom domains
        </SectionTitle>
        <Card>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr className="border-b border-neutral-800 text-neutral-400">
                  <th className="p-3">Domain</th>
                  <th className="p-3">Workspace</th>
                  <th className="p-3">Status</th>
                  <th className="p-3">Actions</th>
                </tr>
              </thead>
              <tbody>
                {domains.map((d) => (
                  <tr key={d.id} className="border-b border-neutral-900">
                    <td className="p-3 font-medium">{d.domain}</td>
                    <td className="p-3">{d.workspaceId || <span className="text-neutral-500">(unassigned)</span>}</td>
                    <td className="p-3">{domainStatusPill(d.status)}</td>
                    <td className="p-3">
                      <div className="flex gap-2">
                        <button className="rounded-lg border border-neutral-700 px-2 py-1 text-xs hover:bg-neutral-800">Manage</button>
                        {d.status !== "verified" && (
                          <button onClick={() => verifyDomain(d.id)} className="rounded-lg border border-neutral-700 px-2 py-1 text-xs hover:bg-neutral-800">Verify</button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
                {!domains.length && (
                  <tr>
                    <td className="p-4 text-sm text-neutral-400" colSpan={4}>No domains yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Optional: Embedded Domain Manager UI (swap src for your embed URL) */}
        <Card className="mt-4 p-4">
          <div className="mb-2 text-sm text-neutral-400">Embedded Domain Manager</div>
          <div className="aspect-video w-full overflow-hidden rounded-xl border border-neutral-800">
            <iframe
              title="Domain Manager"
              src={import.meta?.env?.VITE_DOMAIN_MANAGER_EMBED || "about:blank"}
              className="h-full w-full"
            />
          </div>
        </Card>
      </div>
    </div>
  );

  async function verifyDomain(id) {
    try { await api(`/domains/${id}/verify`, { method: "POST" }); refreshAll(); } catch (e) { safeLog(e, 'Error verifying domain:'); }
  }
};

function statusPill(status) {
  const map = {
    running: { tone: "green", label: "Running" },
    starting: { tone: "yellow", label: "Starting" },
    stopped: { tone: "gray", label: "Stopped" },
    stopping: { tone: "yellow", label: "Stopping" },
    suspended: { tone: "red", label: "Suspended" },
  };
  const m = map[status];
  return <Pill tone={m.tone}>{m.label}</Pill>;
}

function domainStatusPill(status) {
  const map = {
    verified: { tone: "green", label: "Verified" },
    pending: { tone: "yellow", label: "Pending" },
    error: { tone: "red", label: "Error" },
  };
  const m = map[status];
  return <Pill tone={m.tone}>{m.label}</Pill>;
}

function slug(s) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}

export default Dashboard;
