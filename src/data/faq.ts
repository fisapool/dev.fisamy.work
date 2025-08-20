/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { FAQ } from "../types";

export const faqs: readonly FAQ[] = [
  {
    q: "What do I need to use this?",
    a: "Just a modern browser. No installs. Works on Windows, macOS, Linux, and Chromebooks.",
  },
  {
    q: "Is my code secure?",
    a: "Traffic is encrypted (HTTPS). Each workspace runs isolated. Team plan supports SSO and org policies."
  },
  {
    q: "Can I host inside my region?",
    a: "Yes. We can deploy in your chosen region for data residency and lower latency."
  },
  {
    q: "Do you back up my work?",
    a: "Yes. We snapshot storage on a schedule; you can also export projects to your own repo."
  },
  {
    q: "What happens when I'm idle?",
    a: "Workspaces auto-suspend to save resources. Your files persist; resume is one click."
  },
  {
    q: "Do you offer education discounts?",
    a: "Yes—contact us with your institution email for student/teacher pricing."
  },
] as const;

