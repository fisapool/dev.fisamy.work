/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState, useMemo, memo } from "react";
import { plans } from "../../data/plans";
import { comparisonRows } from "../../data/comparison";
import { faqs } from "../../data/faq";
import { BillingToggle } from "../ui/BillingToggle";
import { PlanCard } from "../ui/PlanCard";
import { TestimonialsSection } from "../sections/TestimonialsSection";
import { CheckIcon } from "../ui/icons/CheckIcon";
import { SecurityIcon } from "../ui/icons/ResourceIcons";
import { BillingPeriod } from "../../types";

const CHECKOUT_PRO = import.meta.env.VITE_CHECKOUT_PRO || "https://your-checkout/pro";
const CHECKOUT_SOLO = import.meta.env.VITE_CHECKOUT_SOLO || "https://your-checkout/solo";

const BackgroundGlow: React.FC = memo(() => (
  <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
    <div className="absolute left-1/2 top-[-10%] h-[40rem] w-[40rem] -translate-x-1/2 rounded-full bg-emerald-500/10 blur-3xl" />
    <div className="absolute right-[-10%] top-1/3 h-[30rem] w-[30rem] rounded-full bg-emerald-500/5 blur-3xl" />
  </div>
));

export const HomePage: React.FC = memo(() => {
  const [billing, setBilling] = useState<BillingPeriod>("monthly");

  const headlinePrice = useMemo(() => {
    const proPlan = plans[1]; // Pro plan
    return billing === "monthly" ? proPlan.priceMonthly : proPlan.priceYearly;
  }, [billing]);

  return (
    <>
      <BackgroundGlow />
      
      {/* Hero Section */}
      <section className="relative isolate overflow-hidden">
        <div className="mx-auto max-w-6xl px-6 py-16 md:py-24">
          <div className="grid gap-8 md:grid-cols-2 md:items-center">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-neutral-800 bg-neutral-900/60 px-3 py-1 text-xs text-neutral-300">
                <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-emerald-400" />
                Ready in minutes • TLS by default • No installs
              </span>
              <h1 className="mt-4 text-4xl font-bold leading-tight md:text-5xl">
                VS Code in your browser.
                <span className="block text-neutral-300">Fast. Secure. Zero setup.</span>
              </h1>
              <p className="mt-4 max-w-xl text-neutral-300">
                Stop wrestling with SDKs on every laptop. We run the dev boxes; you write the code.
                Choose a plan and start in under five minutes.
              </p>
              <div className="mt-6 flex flex-wrap items-center gap-3 text-sm text-neutral-400">
                <div className="flex items-center gap-2"><CheckIcon /> TLS 1.3</div>
                <div className="flex items-center gap-2"><CheckIcon /> Per-user isolation</div>
                <div className="flex items-center gap-2"><CheckIcon /> Idle auto-suspend</div>
              </div>
            </div>
            <div className="rounded-3xl border border-neutral-800 bg-neutral-900 p-6 shadow-xl transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs text-neutral-400">Start from</p>
                  <p className="text-2xl font-bold">RM {headlinePrice}<span className="text-sm text-neutral-400">/{billing === "monthly" ? "mo" : "yr"}</span></p>
                </div>
                <SecurityIcon className="h-8 w-8 text-emerald-400" />
              </div>
              <p className="mt-2 text-xs text-neutral-400">Pro plan • Most popular</p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="mx-auto max-w-6xl px-6 py-12" id="pricing">
        <div className="mb-6 flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-2xl font-bold md:text-3xl">Choose your plan</h2>
          <BillingToggle billing={billing} setBilling={setBilling} />
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((plan) => (
            <PlanCard key={plan.id} plan={plan} billing={billing} />
          ))}
        </div>
        <p className="mt-4 text-center text-sm text-neutral-400">
          Need custom limits or on-prem? <a className="underline decoration-neutral-700 hover:text-neutral-200" href="#cta">Talk to sales</a>.
        </p>
      </section>

      {/* Testimonials */}
      <TestimonialsSection />

      {/* Comparison Section */}
      <section className="mx-auto max-w-6xl px-6 py-12" id="comparison">
        <h2 className="text-2xl font-bold md:text-3xl">Why choose us over alternatives?</h2>
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[600px] border-collapse">
            <thead>
              <tr className="border-b border-neutral-800">
                <th className="text-left p-3 font-semibold">Feature</th>
                <th className="text-center p-3 font-semibold text-emerald-400">Us</th>
                <th className="text-center p-3 font-semibold text-neutral-400">Local Dev</th>
                <th className="text-center p-3 font-semibold text-neutral-400">DIY Cloud</th>
                <th className="text-center p-3 font-semibold text-neutral-400">Codespaces</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row, idx) => (
                <tr key={idx} className="border-b border-neutral-800/50">
                  <td className="p-3 font-medium">{row.label}</td>
                  <td className="p-3 text-center text-sm text-emerald-300">{row.us}</td>
                  <td className="p-3 text-center text-sm text-neutral-400">{row.local}</td>
                  <td className="p-3 text-center text-center text-sm text-neutral-400">{row.diy}</td>
                  <td className="p-3 text-center text-sm text-neutral-400">{row.codespaces}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="mx-auto max-w-6xl px-6 py-12" id="faq">
        <h2 className="text-2xl font-bold md:text-3xl text-center mb-8">Frequently Asked Questions</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {faqs.map((faq, i) => (
            <article key={i} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 transition-all duration-200 hover:border-neutral-700 hover:bg-neutral-800/50">
              <h3 className="font-semibold">{faq.q}</h3>
              <p className="mt-2 text-sm text-neutral-300">{faq.a}</p>
            </article>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="mx-auto max-w-5xl px-6 pb-20" id="cta">
        <div className="rounded-3xl border border-neutral-800 bg-gradient-to-br from-neutral-900 to-neutral-900/40 p-8 text-center">
          <h2 className="text-2xl font-bold md:text-3xl">Stop configuring laptops. Start shipping.</h2>
          <p className="mx-auto mt-2 max-w-2xl text-neutral-300">
            Pick a plan now—upgrade anytime. Cancel anytime. Your code stays yours.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a href={CHECKOUT_PRO} className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-500 px-6 py-3 font-semibold text-neutral-950 transition-all duration-200 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/30 active:scale-95 sm:w-auto">
              Start with Pro
            </a>
            <a href={CHECKOUT_SOLO} className="inline-flex w-full items-center justify-center rounded-2xl border border-neutral-700 px-6 py-3 font-semibold text-neutral-100 transition-all duration-200 hover:border-neutral-600 hover:bg-neutral-900 active:scale-95 sm:w-auto">
              Try Solo
            </a>
          </div>
          <p className="mt-3 text-xs text-neutral-400">Annual plans: 2 months free. Education discounts available.</p>
        </div>
      </section>
    </>
  );
});

HomePage.displayName = "HomePage";

