import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import { FEATURE_IMAGES } from './images';

const PERSONAS = [
  { text: "I'm pregnant and want someone tracking it with me", cta: 'Pregnancy Companion', to: '/register', tint: 'bg-pink/40', arrow: 'bg-pink', image: FEATURE_IMAGES.pregnancy },
  { text: "I have a condition I'm managing day to day", cta: 'Voice Doctor', to: '/register', tint: 'bg-mint/40', arrow: 'bg-mint', image: FEATURE_IMAGES.voice },
  { text: "I don't know what's wrong, I just feel off", cta: 'Symptom Check', to: '/register', tint: 'bg-lavender/40', arrow: 'bg-lavender', image: FEATURE_IMAGES.symptom },
  { text: "I'm on more than one medication", cta: 'Drug Interactions', to: '/register', tint: 'bg-peach/40', arrow: 'bg-peach', image: FEATURE_IMAGES.meds },
];

/** Grid cells tint on hover and reveal a "Go to X" link that isn't there
 * at rest — mirrors the reference's "who is this for" section. */
const WhoItsFor = () => {
  const [hovered, setHovered] = useState<number | null>(null);

  return (
    <section className="py-24 px-6 md:px-8">
      <div className="max-w-[1400px] mx-auto">
        <div className="mb-14 max-w-xl">
          <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-3">Who it's for</div>
          <h2 className="text-4xl md:text-5xl">Wherever you're starting from<span className="text-primary-ink">.</span></h2>
        </div>

        <div className="rounded-3xl border border-ink/8 overflow-hidden grid sm:grid-cols-2">
          {PERSONAS.map((p, i) => (
            <Link key={p.text} to={p.to}
              onMouseEnter={() => setHovered(i)} onMouseLeave={() => setHovered(null)}
              className={`p-8 min-h-[200px] flex flex-col justify-between border-b border-r border-ink/8 last:border-r-0 sm:[&:nth-child(2n)]:border-r-0 transition-colors duration-300 ${hovered === i ? p.tint : 'bg-surface'}`}
            >
              <div className="flex items-start gap-4">
                <img src={p.image} alt="" aria-hidden="true"
                  className="w-14 h-14 rounded-2xl object-cover flex-shrink-0" referrerPolicy="no-referrer" loading="lazy" />
                <p className="text-lg font-display font-bold text-ink leading-snug pt-1">{p.text}</p>
              </div>
              <motion.div initial={false} animate={{ opacity: hovered === i ? 1 : 0, y: hovered === i ? 0 : 6 }}
                transition={{ duration: 0.2 }}
                className="flex items-center gap-2 text-sm font-semibold text-ink mt-4"
              >
                Go to {p.cta}
                <span className={`w-6 h-6 rounded-full ${p.arrow} flex items-center justify-center`}>
                  <ArrowRight size={12} className="text-ink" />
                </span>
              </motion.div>
            </Link>
          ))}
        </div>
      </div>
    </section>
  );
};

export default WhoItsFor;
