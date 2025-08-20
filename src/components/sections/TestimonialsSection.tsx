/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { memo } from "react";
import { testimonials } from "../../data/testimonials";

export const TestimonialsSection: React.FC = memo(() => {
  return (
    <section className="mx-auto max-w-6xl px-6 py-12" id="testimonials">
      <h2 className="text-2xl font-bold md:text-3xl text-center mb-12">
        Loved by developers worldwide
      </h2>
      <div className="grid gap-6 md:grid-cols-3">
        {testimonials.map((testimonial, index) => (
          <article 
            key={index} 
            className="rounded-2xl border border-neutral-800 bg-neutral-900 p-6 transition-all duration-300 hover:border-neutral-700 hover:bg-neutral-800/50 hover:-translate-y-1"
          >
            <div className="flex items-center gap-3 mb-4">
              <div 
                className="h-10 w-10 rounded-full bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center text-emerald-300 font-semibold text-sm"
                aria-hidden="true"
              >
                {testimonial.avatar}
              </div>
              <div>
                <div className="font-semibold text-neutral-100">{testimonial.name}</div>
                <div className="text-sm text-neutral-400">{testimonial.title}</div>
              </div>
            </div>
            <blockquote className="text-neutral-300 text-sm leading-relaxed">
              "{testimonial.quote}"
            </blockquote>
          </article>
        ))}
      </div>
    </section>
  );
});

TestimonialsSection.displayName = "TestimonialsSection";

