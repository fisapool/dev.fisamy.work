/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { memo } from "react";
import { BillingToggleProps } from "../../types";
import { classNames } from "../../utils/classNames";

export const BillingToggle: React.FC<BillingToggleProps> = memo(({ billing, setBilling }) => {
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
          aria-label={`Switch to ${opt} billing`}
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
});

BillingToggle.displayName = "BillingToggle";

