import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { ArrowRight, Mic, Baby, Stethoscope, ShieldAlert } from 'lucide-react';
import { FEATURE_IMAGES } from './images';

interface Tab {
  id: string;
  label: string;
  icon: typeof Mic;
  image: string;
  sectionBg: string;
  badgeBg: string;
  titleColor: string;
  ctaBg: string;
  badge: string;
  title: string;
  description: string;
  cta: string;
  to: string;
  card: { label: string; value: string; sub: string; rows: { label: string; value: string; sub: string; bg: string }[] };
}

const TABS: Tab[] = [
  {
    id: 'voice', label: 'Voice Doctor', icon: Mic, image: FEATURE_IMAGES.voice,
    sectionBg: 'bg-mint/50', badgeBg: 'bg-mint', titleColor: 'text-ink', ctaBg: 'bg-ink hover:bg-ink/90',
    badge: 'Voice consultation',
    title: 'Voice Doctor',
    description: "Speak the way you actually talk — code-switched Yoruba, Hausa, Igbo, Pidgin, or English — and Kare responds in full audio, the same register right back.",
    cta: 'Explore Voice Doctor', to: '/features',
    card: {
      label: 'Consultation summary', value: 'Non-urgent', sub: 'Suspected: mild malaria — recommend RDT',
      rows: [
        { label: 'Checked', value: 'Drug interactions', sub: 'None found with current meds', bg: 'bg-primary/30' },
        { label: 'Language', value: 'Yoruba ↔ English', sub: 'Auto-detected mid-conversation', bg: 'bg-sand' },
      ],
    },
  },
  {
    id: 'pregnancy', label: 'Pregnancy', icon: Baby, image: FEATURE_IMAGES.pregnancy,
    sectionBg: 'bg-pink/50', badgeBg: 'bg-pink', titleColor: 'text-ink', ctaBg: 'bg-[#B5527A] hover:bg-[#9c4468]',
    badge: 'Pregnancy care',
    title: 'Pregnancy Companion',
    description: 'A dedicated mode that tracks the pregnancy week by week, checks in stage-aware, and always keeps warning signs one tap away.',
    cta: 'Explore Pregnancy Companion', to: '/features',
    card: {
      label: 'Week 25', value: '104 days to go', sub: 'Trimester 2 · a girl',
      rows: [
        { label: 'This week', value: 'Glucose screening', sub: 'Around now, if not done already', bg: 'bg-pink/50' },
        { label: 'Watch for', value: 'Reduced movement', sub: 'From 28 weeks — go in same day', bg: 'bg-sand' },
      ],
    },
  },
  {
    id: 'symptom', label: 'Symptom Check', icon: Stethoscope, image: FEATURE_IMAGES.symptom,
    sectionBg: 'bg-lavender/50', badgeBg: 'bg-lavender', titleColor: 'text-ink', ctaBg: 'bg-[#6B4FA0] hover:bg-[#5c4389]',
    badge: 'Instant triage',
    title: 'Symptom Check',
    description: 'Describe what you feel in your own words and get a clear triage level — Emergency to Self-care — with next steps, not just a diagnosis guess.',
    cta: 'Explore Symptom Check', to: '/features',
    card: {
      label: 'Assessment', value: 'Semi-urgent', sub: 'Fever + body aches, 2 days',
      rows: [
        { label: 'Possible', value: 'Typhoid or malaria', sub: 'Common in your reported area', bg: 'bg-lavender/60' },
        { label: 'Do next', value: 'See a clinic today', sub: 'Not an emergency — no need for A&E', bg: 'bg-sand' },
      ],
    },
  },
  {
    id: 'meds', label: 'Medications', icon: ShieldAlert, image: FEATURE_IMAGES.meds,
    sectionBg: 'bg-peach/50', badgeBg: 'bg-peach', titleColor: 'text-ink', ctaBg: 'bg-[#B5652B] hover:bg-[#9c5624]',
    badge: 'Medication safety',
    title: 'Drug Interaction Checker',
    description: 'Every medication you add is checked against the rest of your list automatically — before a dangerous combination becomes a hospital visit.',
    cta: 'Explore drug interactions', to: '/features',
    card: {
      label: 'Interaction found', value: '1 moderate', sub: 'Metformin + your new prescription',
      rows: [
        { label: 'Risk', value: 'Increased lactic acidosis risk', sub: 'Flag this to your pharmacist', bg: 'bg-peach/60' },
        { label: 'Source', value: 'RxNorm database', sub: 'Same one clinicians reference', bg: 'bg-sand' },
      ],
    },
  },
];

/** Tabbed feature showcase — the section's whole color theme (background,
 * badge, CTA) shifts with the active tab, mirroring the reference's
 * "Solutions we offer" section. No photography of our own to swap in, so
 * the left panel is a UI mock of the real feature instead of a stock photo
 * — arguably more honest for a product page anyway. */
const SolutionsTabs = () => {
  const [active, setActive] = useState(0);
  const tab = TABS[active];

  return (
    <section className={`py-24 px-6 md:px-8 transition-colors duration-500 ${tab.sectionBg}`}>
      <div className="max-w-[1400px] mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-4xl md:text-5xl mb-3">Solutions we offer<span className="text-primary-ink">.</span></h2>
          <p className="text-ink/50">Four ways Kare meets you where you are</p>
        </div>

        <div className="flex justify-center mb-14">
          <div className="inline-flex flex-wrap justify-center gap-1 bg-surface rounded-full p-1.5 shadow-sm">
            {TABS.map((t, i) => (
              <button key={t.id} onClick={() => setActive(i)}
                className="relative px-5 py-2.5 rounded-full text-sm font-semibold transition-colors"
              >
                {active === i && (
                  <motion.span layoutId="solutions-pill" className="absolute inset-0 bg-ink rounded-full"
                    transition={{ type: 'spring', duration: 0.5, bounce: 0.2 }} />
                )}
                <span className={`relative z-10 ${active === i ? 'text-primary' : 'text-ink/55'}`}>{t.label}</span>
              </button>
            ))}
          </div>
        </div>

          <motion.div key={tab.id} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="grid lg:grid-cols-2 gap-12 items-center"
          >
            <div className="relative">
              <div className="aspect-[4/3] rounded-3xl overflow-hidden bg-surface">
                <img src={tab.image} alt={tab.title} className="w-full h-full object-cover" referrerPolicy="no-referrer" loading="lazy" />
              </div>
              <div className="absolute -bottom-6 left-6 right-6 md:left-10 md:right-auto md:w-80 bg-surface rounded-2xl shadow-xl p-5">
                <div className="text-xs font-semibold text-ink/40 mb-1">{tab.card.label}</div>
                <div className="text-2xl font-display font-bold text-ink mb-0.5">{tab.card.value}</div>
                <div className="text-xs text-ink/45 mb-4">{tab.card.sub}</div>
                {tab.card.rows.map((r) => (
                  <div key={r.label} className={`rounded-xl px-3.5 py-2.5 mb-2 last:mb-0 ${r.bg}`}>
                    <div className="flex items-baseline justify-between">
                      <span className="text-xs font-semibold text-ink/70">{r.label}</span>
                      <span className="text-sm font-bold text-ink">{r.value}</span>
                    </div>
                    <div className="text-[11px] text-ink/45">{r.sub}</div>
                  </div>
                ))}
              </div>
            </div>

            <div className="pt-6 lg:pt-0 lg:pl-8">
              <span className={`badge ${tab.badgeBg} text-ink mb-4`}>{tab.badge}</span>
              <h3 className={`text-3xl md:text-4xl mb-4 ${tab.titleColor}`}>{tab.title}</h3>
              <p className="text-base text-ink/60 leading-relaxed mb-8">{tab.description}</p>
              <Link to={tab.to} className={`inline-flex items-center gap-2 text-white rounded-full px-6 py-3.5 font-display font-semibold transition-colors ${tab.ctaBg}`}>
                {tab.cta} <ArrowRight size={18} />
              </Link>
            </div>
          </motion.div>
      </div>
    </section>
  );
};

export default SolutionsTabs;
