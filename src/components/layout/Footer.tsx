/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { memo } from "react";

export const Footer: React.FC = memo(() => {
  const currentYear = new Date().getFullYear();
  
  return (
    <footer className="border-t border-neutral-900/80">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-4 px-6 py-6 text-xs text-neutral-400">
        <p>© {currentYear} fisamy.work • All rights reserved.</p>
        <nav className="flex gap-4" aria-label="Footer navigation">
          <a href="#/terms" className="transition-colors hover:text-neutral-200">Terms</a>
          <a href="#/privacy" className="transition-colors hover:text-neutral-200">Privacy</a>
          <a href="#/contact" className="transition-colors hover:text-neutral-200">Contact</a>
        </nav>
      </div>
    </footer>
  );
});

Footer.displayName = "Footer";

