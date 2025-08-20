/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { memo } from "react";
import { PlanCardProps } from "../../types";
import { CheckIcon } from "./icons/CheckIcon";
import { CpuIcon, RamIcon, StorageIcon } from "./icons/ResourceIcons";
import { classNames } from "../../utils/classNames";

export const PlanCard: React.FC<PlanCardProps> = memo(({ plan, billing }) => {
  const price = billing === "monthly" ? plan.priceMonthly : plan.priceYearly;
  
  return (
    <div 
      className={classNames(
        "relative rounded-3xl border bg-neutral-900 p-6 transition-all duration-300 hover:-translate-y-2",
        plan.popular 
          ? "border-emerald-500/60 shadow-[0_0_0_1px_rgba(16,185,129,0.3)] hover:shadow-[0_0_0_1px_rgba(16,185,129,0.5)] hover:shadow-lg hover:shadow-emerald-500/20" 
          : "border-neutral-800 shadow-black/10 hover:border-neutral-700 hover:shadow-lg"
      )}
      role="article"
      aria-labelledby={`plan-${plan.id}-title`}
    >
      {plan.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full border border-emerald-500/40 bg-emerald-900/50 px-3 py-1 text-xs text-emerald-300 shadow-lg">
          Most Popular
        </div>
      )}
      
      <h3 id={`plan-${plan.id}-title`} className="text-xl font-bold">{plan.name}</h3>
      <p className="mt-1 text-sm text-neutral-300">{plan.tagline}</p>
      
      <div className="mt-4 text-4xl font-bold">
        RM {price}
        <span className="text-base font-normal text-neutral-400">
          /{billing === "monthly" ? "mo" : "yr"}
        </span>
      </div>
      
      <ul className="mt-4 space-y-1 text-sm text-neutral-300">
        <li className="flex items-center gap-2">
          <CpuIcon />
          {plan.cpu}
        </li>
        <li className="flex items-center gap-2">
          <RamIcon />
          {plan.ram}
        </li>
        <li className="flex items-center gap-2">
          <StorageIcon />
          {plan.storage}
        </li>
      </ul>
      
      <div className="my-4 h-px bg-neutral-800" />
      
      <ul className="space-y-2 text-sm text-neutral-200">
        {plan.limits.map((limit, i) => (
          <li key={i} className="flex items-center gap-2">
            <CheckIcon /> {limit}
        </li>
        ))}
      </ul>
      
      <ul className="mt-3 space-y-2 text-sm text-neutral-300">
        {plan.features.map((feature, i) => (
          <li key={i} className="flex items-center gap-2">
            <CheckIcon /> {feature}
          </li>
        ))}
      </ul>
      
      <a 
        href={plan.cta.href} 
        className={classNames(
          "mt-5 inline-flex w-full items-center justify-center rounded-2xl px-5 py-3 font-semibold transition-all duration-200 active:scale-95",
          plan.popular 
            ? "bg-emerald-500 text-neutral-950 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/30" 
            : "border border-neutral-700 hover:border-neutral-600 hover:bg-neutral-900"
        )}
        aria-label={`${plan.cta.label} - ${plan.name} plan for RM ${price}/${billing === "monthly" ? "month" : "year"}`}
      >
        {plan.cta.label}
      </a>
      
      <p className="mt-2 text-center text-xs text-neutral-400">
        Cancel anytime • No lock-in
      </p>
    </div>
  );
});

PlanCard.displayName = "PlanCard";

