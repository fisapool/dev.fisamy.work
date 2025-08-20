/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

export interface Plan {
  id: string;
  name: string;
  tagline: string;
  priceMonthly: number;
  priceYearly: number;
  cpu: string;
  ram: string;
  storage: string;
  limits: string[];
  features: string[];
  cta: {
    label: string;
    href: string;
  };
  popular: boolean;
}

export interface ComparisonRow {
  label: string;
  us: string;
  local: string;
  diy: string;
  codespaces: string;
}

export interface FAQ {
  q: string;
  a: string;
}

export interface Testimonial {
  name: string;
  title: string;
  quote: string;
  avatar: string;
}

export type BillingPeriod = "monthly" | "yearly";

export interface BillingToggleProps {
  billing: BillingPeriod;
  setBilling: (value: BillingPeriod) => void;
}

export interface PlanCardProps {
  plan: Plan;
  billing: BillingPeriod;
}

export interface GenericPageProps {
  title: string;
  children: React.ReactNode;
}

