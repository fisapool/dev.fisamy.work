/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { ComparisonRow } from "../types";

export const comparisonRows: readonly ComparisonRow[] = [
  {
    label: "Time to first code",
    us: "2–5 min (click → workspace)",
    local: "1–3 days (installs/SDKs)",
    diy: "4–8 hrs (VM + hardening)",
    codespaces: "5–10 min",
  },
  {
    label: "Total cost of ownership",
    us: "Flat plan (predictable)",
    local: "Upgrades + repairs",
    diy: "Cloud bill + your ops time",
    codespaces: "Metered minutes + storage",
  },
  {
    label: "Performance on low-end devices",
    us: "Server does the heavy lifting",
    local: "Struggles on cheap laptops",
    diy: "Good if sized right",
    codespaces: "Good",
  },
  {
    label: "Remote team collaboration",
    us: "Everyone same env + settings",
    local: "Sync nightmares",
    diy: "Possible but complex",
    codespaces: "Good",
  },
  {
    label: "Maintenance burden",
    us: "Zero (we handle it)",
    local: "Ongoing updates, troubleshooting",
    diy: "High (you own the stack)",
    codespaces: "Low",
  },
  {
    label: "Data privacy / compliance",
    us: "SOC2, region choice",
    local: "Your responsibility",
    diy: "Your responsibility",
    codespaces: "Microsoft's policies",
  },
] as const;

