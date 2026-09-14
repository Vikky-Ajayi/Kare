import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Languages, BrainCircuit, Clock } from 'lucide-react';

const CARDS = [
  { icon: Languages, bg: 'bg-peach', title: 'Understands your language', description: 'Not translated — natively code-switched. Say it the way you\'d say it to a neighbour, mid-sentence language switch and all.' },
  { icon: BrainCircuit, bg: 'bg-lavender', title: 'Remembers everything', description: 'Every consultation adds to a clinical picture Kare actually reads before the next one — no repeating your history from scratch.' },
  { icon: Clock, bg: 'bg-mint', title: 'Always available', description: 'No appointment, no waiting room, no closing time. Symptoms don\'t wait for office hours, so neither does Kare.' },
];

/** Hover reveals the description under the title and gives the icon a
 * small lift — mirrors the reference's "What sets us apart" cards, minus
 * needing real photography to swap in on hover. */
const WhyKare = () => {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <section className="py-24 px-6 md:px-8 bg-sand/40">
      <div className="max-w-[1400px] mx-auto">
        <div className="text-center mb-14 max-w-2xl mx-auto">
          <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-3">Why it's different</div>
          <h2 className="text-4xl md:text-5xl">Not a form. <span className="text-primary-ink">An agent.</span></h2>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          {CARDS.map((c, i) => (
            <div key={c.title} onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}
              className={`rounded-3xl ${c.bg} p-8 min-h-[240px] flex flex-col cursor-default transition-transform hover:-translate-y-1`}
            >
              <motion.div animate={{ scale: hovered === i ? 1.15 : 1, rotate: hovered === i ? -6 : 0 }}
                transition={{ type: 'spring', stiffness: 300, damping: 15 }}
                className="w-14 h-14 rounded-2xl bg-surface flex items-center justify-center mb-6 origin-left"
              >
                <c.icon size={26} className="text-ink" />
              </motion.div>
              <h3 className="text-xl font-display font-bold text-ink mb-2">{c.title}</h3>
              <AnimatePresence>
                {hovered === i && (
                  <motion.p
                    initial={{ opacity: 0, height: 0 }} animate={{ opacity: 1, height: 'auto' }} exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.25 }}
                    className="text-sm text-ink/60 leading-relaxed overflow-hidden"
                  >
                    {c.description}
                  </motion.p>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WhyKare;
