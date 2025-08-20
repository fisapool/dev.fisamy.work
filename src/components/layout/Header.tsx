/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { memo } from "react";

export const Header: React.FC = memo(() => {
  return (
    <header className="sticky top-0 z-40 border-b border-neutral-900/80 bg-neutral-950/70 backdrop-blur supports-backdrop-blur:bg-neutral-950/70">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <a 
          href="#" 
          className="font-bold tracking-wide transition-colors hover:text-emerald-400"
          aria-label="code.fisamy.work homepage"
        >
          code.fisamy.work
        </a>
        <nav 
          className="hidden items-center gap-6 text-sm text-neutral-300 md:flex"
          aria-label="Main navigation"
        >
          <a href="#pricing" className="transition-colors hover:text-white">Pricing</a>
          <a href="#comparison" className="transition-colors hover:text-white">Compare</a>
          <a href="#testimonials" className="transition-colors hover:text-white">Reviews</a>
          <a href="#faq" className="transition-colors hover:text-white">FAQ</a>
          <a 
            href="#cta" 
            className="rounded-xl border border-neutral-800 px-3 py-1.5 transition-all hover:border-emerald-500/50 hover:bg-neutral-900"
            aria-label="Get started with VS Code hosting"
          >
            Get Started
          </a>
        </nav>
      </div>
    </header>
  );
});

Header.displayName = "Header";

