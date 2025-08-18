/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
*/
import React, { useMemo, useState, useEffect } from "react";
import ReactDOM from "react-dom/client";

// VS Code Hosting – Pricing + Comparison + FAQ
// Drop-in component for a Landing/Pricing page.
// TailwindCSS required. No external UI libs. No icons needed.
// Checkout URLs are configured via environment variables.

const CHECKOUT_SOLO = import.meta.env.VITE_CHECKOUT_SOLO || "https://your-checkout/solo";
const CHECKOUT_PRO = import.meta.env.VITE_CHECKOUT_PRO || "https://your-checkout/pro";
const CHECKOUT_TEAM = import.meta.env.VITE_CHECKOUT_TEAM || "https://your-checkout/team";

const plans = [
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

type Plan = typeof plans[number];

const comparisonRows = [
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
    label: "Environment drift",
    us: "Template-locked (zero)",
    local: "High",
    diy: "Medium",
    codespaces: "Low",
  },
  {
    label: "Security",
    us: "TLS + isolation + SSO option",
    local: "Depends on user hygiene",
    diy: "You own patching",
    codespaces: "Vendor-managed",
  },
  {
    label: "Data control / residency",
    us: "You choose region/server",
    local: "On device",
    diy: "You choose (maintain)",
    codespaces: "Vendor regions",
  },
  {
    label: "Admin workload",
    us: "Low (we run it)",
    local: "High (tickets/fixes)",
    diy: "High (devops)",
    codespaces: "Low",
  },
];

const faqs = [
  {
    q: "What do I need to use this?",
    a: "Just a modern browser. No installs. Works on Windows, macOS, Linux, and Chromebooks.",
  },
  { q: "Is my code secure?", a: "Traffic is encrypted (HTTPS). Each workspace runs isolated. Team plan supports SSO and org policies." },
  { q: "Can I host inside my region?", a: "Yes. We can deploy in your chosen region for data residency and lower latency." },
  { q: "Do you back up my work?", a: "Yes. We snapshot storage on a schedule; you can also export projects to your own repo." },
  { q: "What happens when I’m idle?", a: "Workspaces auto-suspend to save resources. Your files persist; resume is one click." },
  { q: "Do you offer education discounts?", a: "Yes—contact us with your institution email for student/teacher pricing." },
];

// Add testimonials data
const testimonials = [
  {
    name: "Sarah Chen",
    title: "Senior Developer at TechFlow",
    quote: "Switched from local setup to this hosted VS Code last month. My build times went from 15 minutes to under 2. Game changer for our team.",
    avatar: "SC"
  },
  {
    name: "Marcus Rodriguez",
    title: "Indie Game Developer",
    quote: "As a solo dev, I can't afford expensive hardware. This gives me the power of a high-end machine for the price of a coffee subscription.",
    avatar: "MR"
  },
  {
    name: "Dr. Emily Watson",
    title: "Computer Science Professor",
    quote: "Perfect for my students. No more 'it works on my machine' excuses. Everyone gets the same environment, every time.",
    avatar: "EW"
  }
];

/** A simple hook to manage hash-based routing */
function useHashNavigation() {
  const [hash, setHash] = useState(window.location.hash);

  useEffect(() => {
    const handleHashChange = () => {
      setHash(window.location.hash);
    };

    window.addEventListener('hashchange', handleHashChange, false);
    return () => {
      window.removeEventListener('hashchange', handleHashChange, false);
    };
  }, []);

  return hash;
}

function Check() {
  return (
    <svg
      aria-hidden
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      className="h-5 w-5"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
    >
      <path d="M20 6 9 17l-5-5" />
    </svg>
  );
}

// Add icon components for better visual hierarchy
function CpuIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
    </svg>
  );
}

function RamIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
    </svg>
  );
}

function StorageIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
    </svg>
  );
}

function SecurityIcon() {
  return (
    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
    </svg>
  );
}

function classNames(...xs: (string | false | null | undefined)[]) {
  return xs.filter(Boolean).join(" ");
}

function Header() {
  return (
    <header className="sticky top-0 z-40 border-b border-neutral-900/80 bg-neutral-950/70 backdrop-blur supports-backdrop-blur:bg-neutral-950/70">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <a href="#" className="font-bold tracking-wide transition-colors hover:text-emerald-400">code.fisamy.work</a>
        <nav className="hidden items-center gap-6 text-sm text-neutral-300 md:flex">
          <a href="#pricing" className="transition-colors hover:text-white">Pricing</a>
          <a href="#comparison" className="transition-colors hover:text-white">Compare</a>
          <a href="#testimonials" className="transition-colors hover:text-white">Reviews</a>
          <a href="#faq" className="transition-colors hover:text-white">FAQ</a>
          <a href="#cta" className="rounded-xl border border-neutral-800 px-3 py-1.5 transition-all hover:border-emerald-500/50 hover:bg-neutral-900">Get Started</a>
        </nav>
      </div>
    </header>
  );
}

function Footer() {
  return (
    <footer className="border-t border-neutral-900/80">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6 text-xs text-neutral-400">
        <p>© {new Date().getFullYear()} fisamy.work • All rights reserved.</p>
        <nav className="flex gap-4">
          <a href="#/terms" className="transition-colors hover:text-neutral-200">Terms</a>
          <a href="#/privacy" className="transition-colors hover:text-neutral-200">Privacy</a>
          <a href="#/contact" className="transition-colors hover:text-neutral-200">Contact</a>
        </nav>
      </div>
    </footer>
  );
}

function GenericPage({ title, children }: { title: string, children: React.ReactNode }) {
  return (
    <section className="mx-auto max-w-4xl px-6 py-16 md:py-24">
      <h1 className="text-4xl font-bold leading-tight md:text-5xl mb-8">{title}</h1>
      <div className="prose prose-invert max-w-none text-neutral-300 prose-headings:text-neutral-100 prose-a:text-emerald-400 hover:prose-a:text-emerald-300">
          {children}
      </div>
    </section>
  );
}

function TermsPage() {
  return (
    <GenericPage title="Terms of Service">
      <p>Last updated: {new Date().toLocaleDateString()}</p>
      <p>Please read these terms and conditions carefully before using Our Service.</p>
      
      <h2>Interpretation and Definitions</h2>
      <p>The words of which the initial letter is capitalized have meanings defined under the following conditions. The following definitions shall have the same meaning regardless of whether they appear in singular or in plural.</p>
      
      <h2>Acknowledgment</h2>
      <p>These are the Terms and Conditions governing the use of this Service and the agreement that operates between You and the Company. These Terms and Conditions set out the rights and obligations of all users regarding the use of the Service. Your access to and use of the Service is conditioned on Your acceptance of and compliance with these Terms and Conditions.</p>

      <h2>Termination</h2>
      <p>We may terminate or suspend Your access immediately, without prior notice or liability, for any reason whatsoever, including without limitation if You breach these Terms and Conditions. Upon termination, Your right to use the Service will cease immediately.</p>

      <h2>Governing Law</h2>
      <p>The laws of the Country, excluding its conflicts of law rules, shall govern this Terms and Your use of the Service. Your use of the Application may also be subject to other local, state, national, or international laws.</p>

      <h2>Contact Us</h2>
      <p>If you have any questions about these Terms and Conditions, You can <a href="#/contact">contact us</a>.</p>
    </GenericPage>
  );
}

function PrivacyPage() {
  return (
    <GenericPage title="Privacy Policy">
      <p>Last updated: {new Date().toLocaleDateString()}</p>
      <p>This Privacy Policy describes Our policies and procedures on the collection, use and disclosure of Your information when You use the Service and tells You about Your privacy rights and how the law protects You.</p>
      
      <h2>Collecting and Using Your Personal Data</h2>
      <p>While using Our Service, We may ask You to provide Us with certain personally identifiable information that can be used to contact or identify You. Personally identifiable information may include, but is not limited to: Email address, First name and last name, Usage Data.</p>
      
      <h2>Use of Your Personal Data</h2>
      <p>The Company may use Personal Data for the following purposes: to provide and maintain our Service, including to monitor the usage of our Service, to manage Your Account, for the performance of a contract, and to contact You.</p>

      <h2>Security of Your Personal Data</h2>
      <p>The security of Your Personal Data is important to Us, but remember that no method of transmission over the Internet, or method of electronic storage is 100% secure. While We strive to use commercially acceptable means to protect Your Personal Data, We cannot guarantee its absolute security.</p>
    </GenericPage>
  );
}

function ContactPage() {
  return (
    <GenericPage title="Contact Us">
      <p>If you have any questions, concerns, or feedback, please don't hesitate to reach out. We're here to help.</p>
      
      <h2>Email Support</h2>
      <p>For general inquiries and support for Solo and Pro plans, please email us at:</p>
      <p><a href="mailto:support@code.fisamy.work">support@code.fisamy.work</a></p>
      <p>We aim to respond to all inquiries within 24 hours during business days.</p>
      
      <h2>Sales & Team Plan Inquiries</h2>
      <p>For questions about the Team plan, custom configurations, or on-premise solutions, please contact our sales team:</p>
      <p><a href="mailto:sales@code.fisamy.work">sales@code.fisamy.work</a></p>
    </GenericPage>
  );
}

// Add Testimonials component
function TestimonialsSection() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12" id="testimonials">
      <h2 className="text-2xl font-bold md:text-3xl text-center mb-12">Loved by developers worldwide</h2>
      <div className="grid gap-6 md:grid-cols-3">
        {testimonials.map((testimonial, index) => (
          <div 
            key={index} 
            className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6 transition-all duration-300 hover:border-neutral-700 hover:bg-neutral-800/50 hover:-translate-y-1"
          >
            <div className="flex items-center gap-3 mb-4">
              <div className="h-10 w-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-300 font-semibold text-sm">
                {testimonial.avatar}
              </div>
              <div>
                <div className="font-semibold text-neutral-100">{testimonial.name}</div>
                <div className="text-sm text-neutral-400">{testimonial.title}</div>
              </div>
            </div>
            <p className="text-neutral-300 text-sm leading-relaxed">"{testimonial.quote}"</p>
          </div>
        ))}
      </div>
    </section>
  );
}

function HomePage() {
  const [billing, setBilling] = useState<"monthly" | "yearly">("monthly");

  const headlinePrice = useMemo(() => {
    const best = plans[1]; // Pro
    return billing === "monthly" ? best.priceMonthly : best.priceYearly;
  }, [billing]);

  return (
    <>
      {/* Hero */}
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
                <div className="flex items-center gap-2"><Check /> TLS 1.3</div>
                <div className="flex items-center gap-2"><Check /> Per-user isolation</div>
                <div className="flex items-center gap-2"><Check /> Idle auto-suspend</div>
              </div>
            </div>
            <div className="rounded-3xl border border-neutral-800 bg-neutral-900 p-6 shadow-xl transition-all duration-300 hover:shadow-2xl hover:shadow-emerald-500/10">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Pro plan from</h3>
                <BillingToggle billing={billing} setBilling={setBilling} />
              </div>
              <div className="mt-2 text-5xl font-bold">RM {headlinePrice}
                <span className="text-base font-normal text-neutral-400">/{billing === "monthly" ? "mo" : "yr"}</span>
              </div>
              <ul className="mt-6 space-y-2 text-sm text-neutral-300">
                <li className="flex items-center gap-2"><Check /> 4 vCPU • 8 GB RAM • 40 GB SSD</li>
                <li className="flex items-center gap-2"><Check /> 3 workspaces • 2 concurrent sessions</li>
                <li className="flex items-center gap-2"><Check /> Priority support • API (beta)</li>
              </ul>
              <a href={CHECKOUT_PRO} className="mt-6 inline-flex w-full items-center justify-center rounded-2xl bg-emerald-500 px-5 py-3 font-semibold text-neutral-950 transition-all duration-200 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/30 active:scale-95">
                Start now
              </a>
              <p className="mt-3 text-center text-xs text-neutral-400">Save 2 months with annual billing.</p>
            </div>
          </div>
        </div>
        <BackgroundGlow />
      </section>

      {/* Plans */}
      <section className="mx-auto max-w-6xl px-6 py-12" id="pricing">
        <div className="mb-6 flex flex-col items-start gap-4 md:flex-row md:items-center md:justify-between">
          <h2 className="text-2xl font-bold md:text-3xl">Choose your plan</h2>
          <BillingToggle billing={billing} setBilling={setBilling} />
        </div>
        <div className="grid gap-6 md:grid-cols-3">
          {plans.map((p) => (
            <PlanCard key={p.id} p={p} billing={billing} />
          ))}
        </div>
        <p className="mt-4 text-center text-sm text-neutral-400">Need custom limits or on-prem? <a className="underline decoration-neutral-700 hover:text-neutral-200" href="#cta">Talk to sales</a>.</p>
      </section>

      {/* Testimonials */}
      <TestimonialsSection />

      {/* Comparison */}
      <section className="mx-auto max-w-6xl px-6 py-12" id="comparison">
        <h2 className="text-2xl font-bold md:text-3xl">Why this beats the alternatives</h2>
        
        {/* Desktop comparison table */}
        <div className="mt-6 hidden md:block overflow-x-auto rounded-2xl border border-neutral-800 bg-neutral-900">
          <table className="w-full text-left text-sm">
            <thead className="bg-neutral-900/70 text-neutral-300">
              <tr>
                <th className="px-4 py-3">Criteria</th>
                <th className="px-4 py-3">Our Hosted VS Code</th>
                <th className="px-4 py-3">Local PC</th>
                <th className="px-4 py-3">DIY Cloud VM</th>
                <th className="px-4 py-3">Codespaces</th>
              </tr>
            </thead>
            <tbody>
              {comparisonRows.map((row, idx) => (
                <tr key={idx} className={idx % 2 ? "bg-neutral-900/40" : "bg-neutral-900/20"}>
                  <td className="px-4 py-3 font-medium text-neutral-200">{row.label}</td>
                  <td className="px-4 py-3 text-emerald-300">{row.us}</td>
                  <td className="px-4 py-3 text-neutral-300">{row.local}</td>
                  <td className="px-4 py-3 text-neutral-300">{row.diy}</td>
                  <td className="px-4 py-3 text-neutral-300">{row.codespaces}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Mobile comparison cards */}
        <div className="mt-6 md:hidden space-y-4">
          {comparisonRows.map((row, idx) => (
            <div key={idx} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-4">
              <h3 className="font-semibold text-neutral-100 mb-3">{row.label}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-neutral-400">Our Hosted VS Code:</span>
                  <span className="text-emerald-300 font-medium">{row.us}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">Local PC:</span>
                  <span className="text-neutral-300">{row.local}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">DIY Cloud VM:</span>
                  <span className="text-neutral-300">{row.diy}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-neutral-400">Codespaces:</span>
                  <span className="text-neutral-300">{row.codespaces}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section className="mx-auto max-w-5xl px-6 py-12" id="faq">
        <h2 className="text-2xl font-bold md:text-3xl">FAQs</h2>
        <div className="mt-6 grid gap-4 md:grid-cols-2">
          {faqs.map((f, i) => (
            <div key={i} className="rounded-2xl border border-neutral-800 bg-neutral-900 p-5 transition-all duration-200 hover:border-neutral-700 hover:bg-neutral-800/50">
              <h3 className="font-semibold">{f.q}</h3>
              <p className="mt-2 text-sm text-neutral-300">{f.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="mx-auto max-w-5xl px-6 pb-20" id="cta">
        <div className="rounded-3xl border border-neutral-800 bg-gradient-to-br from-neutral-900 to-neutral-900/40 p-8 text-center">
          <h2 className="text-2xl font-bold md:text-3xl">Stop configuring laptops. Start shipping.</h2>
          <p className="mx-auto mt-2 max-w-2xl text-neutral-300">
            Pick a plan now—upgrade anytime. Cancel anytime. Your code stays yours.
          </p>
          <div className="mt-6 flex flex-col items-center justify-center gap-3 sm:flex-row">
            <a href={CHECKOUT_PRO} className="inline-flex w-full items-center justify-center rounded-2xl bg-emerald-500 px-6 py-3 font-semibold text-neutral-950 transition-all duration-200 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/30 active:scale-95 sm:w-auto">Start with Pro</a>
            <a href={CHECKOUT_SOLO} className="inline-flex w-full items-center justify-center rounded-2xl border border-neutral-700 px-6 py-3 font-semibold text-neutral-100 transition-all duration-200 hover:border-neutral-600 hover:bg-neutral-900 active:scale-95 sm:w-auto">Try Solo</a>
          </div>
          <p className="mt-3 text-xs text-neutral-400">Annual plans: 2 months free. Education discounts available.</p>
        </div>
      </section>
    </>
  );
}

type PlanCardProps = {
  p: Plan;
  billing: "monthly" | "yearly";
};

const PlanCard: React.FC<PlanCardProps> = ({ p, billing }) => {
  const price = billing === "monthly" ? p.priceMonthly : p.priceYearly;
  return (
    <div className={classNames(
      "relative rounded-3xl border bg-neutral-900 p-6 transition-all duration-300 hover:-translate-y-2",
      p.popular 
        ? "border-emerald-500/60 shadow-[0_0_0_1px_rgba(16,185,129,0.3)] hover:shadow-[0_0_0_1px_rgba(16,185,129,0.5)] hover:shadow-lg hover:shadow-emerald-500/20" 
        : "border-neutral-800 shadow-black/10 hover:border-neutral-700 hover:shadow-lg"
    )}>
      {p.popular && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 rounded-full border border-emerald-500/40 bg-emerald-900/50 px-3 py-1 text-xs text-emerald-300 shadow-lg">Most Popular</div>
      )}
      <h3 className="text-xl font-bold">{p.name}</h3>
      <p className="mt-1 text-sm text-neutral-300">{p.tagline}</p>
      <div className="mt-4 text-4xl font-bold">RM {price}
        <span className="text-base font-normal text-neutral-400">/{billing === "monthly" ? "mo" : "yr"}</span>
      </div>
      <ul className="mt-4 space-y-1 text-sm text-neutral-300">
        <li className="flex items-center gap-2">
          <CpuIcon />
          {p.cpu}
        </li>
        <li className="flex items-center gap-2">
          <RamIcon />
          {p.ram}
        </li>
        <li className="flex items-center gap-2">
          <StorageIcon />
          {p.storage}
        </li>
      </ul>
      <div className="my-4 h-px bg-neutral-800" />
      <ul className="space-y-2 text-sm text-neutral-200">
        {p.limits.map((x, i) => (
          <li key={i} className="flex items-center gap-2"><Check /> {x}</li>
        ))}
      </ul>
      <ul className="mt-3 space-y-2 text-sm text-neutral-300">
        {p.features.map((x, i) => (
          <li key={i} className="flex items-center gap-2"><Check /> {x}</li>
        ))}
      </ul>
      <a href={p.cta.href} className={classNames(
        "mt-5 inline-flex w-full items-center justify-center rounded-2xl px-5 py-3 font-semibold transition-all duration-200 active:scale-95",
        p.popular 
          ? "bg-emerald-500 text-neutral-950 hover:bg-emerald-400 hover:shadow-lg hover:shadow-emerald-500/30" 
          : "border border-neutral-700 hover:border-neutral-600 hover:bg-neutral-900"
      )}>
        {p.cta.label}
      </a>
      <p className="mt-2 text-center text-xs text-neutral-400">Cancel anytime • No lock-in</p>
    </div>
  );
};

type BillingToggleProps = {
  billing: "monthly" | "yearly";
  setBilling: (v: "monthly" | "yearly") => void;
};

function BillingToggle({ billing, setBilling }: BillingToggleProps) {
  return (
    <div className="inline-flex overflow-hidden rounded-full border border-neutral-800 bg-neutral-900 p-1 text-xs">
      {(["monthly", "yearly"] as const).map((opt) => (
        <button
          key={opt}
          onClick={() => setBilling(opt)}
          className={classNames(
            "rounded-full px-3 py-1.5 text-sm font-medium transition-all duration-200",
            billing === opt ? "bg-neutral-700 text-neutral-100" : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-800"
          )}
          aria-pressed={billing === opt}
        >
          {opt === 'monthly' ? 'Monthly' : (
            <>
              <span className="sm:hidden">Yearly</span>
              <span className="hidden sm:inline">Yearly (save 2 mo)</span>
            </>
          )}
        </button>
      ))}
    </div>
  );
}

function BackgroundGlow() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden">
      <div className="absolute left-1/2 top-[-10%] h-[40rem] w-[40rem] -translate-x-1/2 rounded-full bg-emerald-500/10 blur-3xl" />
      <div className="absolute right-[-10%] top-1/3 h-[30rem] w-[30rem] rounded-full bg-emerald-500/5 blur-3xl" />
    </div>
  );
}

export default function App() {
  const hash = useHashNavigation();
  
  // Determine the page path from the hash
  let path = '/';
  if (hash.startsWith('#/')) {
    path = hash.substring(1); // e.g., #/terms -> /terms
  }
  
  // Scroll to top when page path changes
  useEffect(() => {
    // Only scroll if it's a page navigation, not an anchor link on the home page
    if (!hash || hash.startsWith('#/')) {
      window.scrollTo(0, 0);
    }
  }, [path]);

  let content;
  switch (path) {
    case '/terms':
      content = <TermsPage />;
      break;
    case '/privacy':
      content = <PrivacyPage />;
      break;
    case '/contact':
      content = <ContactPage />;
      break;
    default:
      content = <HomePage />;
      break;
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100">
      <Header />
      <main>
        {content}
      </main>
      <Footer />
    </div>
  );
}

const container = document.getElementById("root");
if (container) {
  const root = ReactDOM.createRoot(container);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
}
