/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Plan } from "../types";

const CHECKOUT_SOLO = import.meta.env.VITE_CHECKOUT_SOLO || "https://your-checkout/solo";
const CHECKOUT_PRO = import.meta.env.VITE_CHECKOUT_PRO || "https://your-checkout/pro";
const CHECKOUT_TEAM = import.meta.env.VITE_CHECKOUT_TEAM || "https://your-checkout/team";

export const plans: readonly Plan[] = [
  {
    id: "solo",
    name: "Solo",
    tagline: "For students & solo devs",
    priceMonthly: 30, // RM
    priceYearly: 300, // RM (2 months free)
    cpu: "2 vCPU",
    ram: "4 GB RAM",
    storage: "20 GB SSD",
    limits: ["1 workspace", "1 concurrent session", "Basic snapshots"],
    features: [
      "Browser VS Code (TLS)",
      "Prebuilt toolchains",
      "Idle auto-suspend",
      "Email support",
    ],
    cta: { label: "Start Solo", href: CHECKOUT_SOLO },
    popular: false,
  },
  {
    id: "pro",
    name: "Pro",
    tagline: "For indie builders & power users",
    priceMonthly: 60,
    priceYearly: 600,
    cpu: "4 vCPU",
    ram: "8 GB RAM",
    storage: "40 GB SSD",
    limits: ["3 workspaces", "2 concurrent sessions", "Daily snapshots"],
    features: [
      "Faster builds & indexing",
      "Team templates",
      "Priority email support",
      "API access (beta)",
    ],
    cta: { label: "Go Pro", href: CHECKOUT_PRO },
    popular: true,
  },
  {
    id: "team",
    name: "Team",
    tagline: "Small teams & cohorts",
    priceMonthly: 199,
    priceYearly: 1990,
    cpu: "4× Pro seats",
    ram: "8 GB RAM per seat",
    storage: "40 GB per seat",
    limits: ["Org dashboard", "SSO option", "Seat transfers"],
    features: [
      "Versioned templates",
      "Audit & backups",
      "Email + chat support",
      "Custom limits available",
    ],
    cta: { label: "Launch Team", href: CHECKOUT_TEAM },
    popular: false,
  },
] as const;

