import React from 'react';
import { motion } from 'motion/react';

const STEPS = [
  { n: 1, bg: 'bg-mint', title: 'Speak, in your language', description: 'Open Voice Doctor and talk the way you actually talk — English, Yoruba, Hausa, Igbo, or Pidgin, mixed however feels natural.' },
  { n: 2, bg: 'bg-sand', title: 'Kare listens and asks back', description: "It follows up like a real consultation, pulls up your history, and checks anything that might interact with what you're on." },
  { n: 3, bg: 'bg-lavender', title: 'Get a clear next step', description: 'A plain-language assessment — what it might be, what to watch for, and when to actually see someone in person.' },
  { n: 4, bg: 'bg-peach', title: 'Kare checks in on you', description: "It decides on its own when a follow-up is worth sending, and writes it like it remembers you — because it does." },
];

/** Cards enter fanned out and settle into place — mirrors the reference's
 * "How the ecosystem works" step section, staggered on scroll-into-view. */
const HowItWorks = () => (
  <section className="py-24 px-6 md:px-8">
    <div className="max-w-[1400px] mx-auto">
      <div className="mb-14 max-w-xl">
        <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-3">How it works</div>
        <h2 className="text-4xl md:text-5xl">Four steps, start to finish<span className="text-primary-ink">.</span></h2>
      </div>

      <div className="grid md:grid-cols-4 gap-5">
        {STEPS.map((s, i) => (
          <motion.div
            key={s.n}
            initial={{ opacity: 0, x: -28 * (4 - i), y: 16, rotate: -2 }}
            whileInView={{ opacity: 1, x: 0, y: 0, rotate: 0 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.55, delay: i * 0.12, ease: [0.22, 1, 0.36, 1] }}
            className={`rounded-3xl ${s.bg} p-7 min-h-[220px] flex flex-col`}
          >
            <div className="w-9 h-9 rounded-full bg-ink text-primary flex items-center justify-center text-sm font-display font-bold mb-6">
              {s.n}
            </div>
            <h3 className="text-lg font-display font-bold text-ink mb-2 leading-snug">{s.title}</h3>
            <p className="text-sm text-ink/60 leading-relaxed">{s.description}</p>
          </motion.div>
        ))}
      </div>
    </div>
  </section>
);

export default HowItWorks;
