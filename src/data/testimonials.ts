/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import { Testimonial } from "../types";

export const testimonials: readonly Testimonial[] = [
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
] as const;

