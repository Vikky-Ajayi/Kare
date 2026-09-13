import React from 'react';
import { motion } from 'motion/react';
import { ArrowRight, Mic, Brain, Languages, ShieldAlert, Check, X as XIcon } from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const container = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.1, delayChildren: 0.2 } },
};
const item = { hidden: { y: 20, opacity: 0 }, visible: { y: 0, opacity: 1 } };

const FEATURES = [
  { icon: Mic, bg: 'bg-mint', title: 'Voice doctor consultation',
    description: 'Your AI doctor listens to you speak, asks follow-up questions, and responds in full audio — just like a real consultation.' },
  { icon: Brain, bg: 'bg-lavender', title: 'Remembers you',
    description: 'After every conversation, Kare saves clinical notes about you. Next time you talk, it already knows your history.' },
  { icon: Languages, bg: 'bg-peach', title: 'Speaks your language',
    description: 'Full support for English, Yoruba, Hausa, Igbo and Nigerian Pidgin — ask in any of them, get a full audio response.' },
  { icon: ShieldAlert, bg: 'bg-pink', title: 'Drug interaction checker',
    description: 'Type in your medications and instantly see if they interact dangerously, backed by the RxNorm database.' },
];

const Landing = () => {
  return (
    <div className="min-h-screen bg-background text-ink selection:bg-primary selection:text-primary-ink font-sans overflow-x-hidden">
      <Navbar />

      <section className="pt-40 pb-28 px-6 md:px-8">
        <div className="max-w-[1400px] mx-auto">
          <motion.div variants={container} initial="hidden" animate="visible">
            <motion.div variants={item} className="mb-6">
              <span className="badge bg-mint text-ink">Healthcare, reimagined for Nigeria</span>
            </motion.div>

            <motion.h1 variants={item} className="text-5xl md:text-7xl leading-[1.05] mb-8 max-w-3xl">
              Your health companion,<br />in the language you<span className="text-primary-ink"> actually speak</span>.
            </motion.h1>

            <div className="grid lg:grid-cols-12 gap-12 items-end">
              <motion.div variants={item} className="lg:col-span-5">
                <p className="text-lg text-ink/55 leading-relaxed mb-10">
                  A voice-first AI medical assistant that understands code-switched Yoruba, Hausa, Igbo
                  and Pidgin-English — and remembers you between visits.
                </p>
                <div className="flex flex-wrap gap-4">
                  <Link to="/register" className="btn-primary group min-h-[44px]">
                    Start a consultation
                    <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
                  </Link>
                  <Link to="/features" className="btn-outline min-h-[44px]">See how it works</Link>
                </div>
              </motion.div>

              <motion.div variants={item} className="lg:col-span-7 relative">
                <div className="aspect-[16/10] rounded-3xl overflow-hidden relative bg-sand">
                  <img
                    src="https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&q=80&w=2070"
                    alt="Doctor consulting a patient"
                    className="w-full h-full object-cover"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent" />

                  <motion.div
                    initial={{ x: 30, opacity: 0 }} animate={{ x: 0, opacity: 1 }} transition={{ delay: 0.6, duration: 0.6 }}
                    className="absolute top-8 right-8 bg-primary rounded-2xl p-6 text-primary-ink shadow-lg"
                  >
                    <div className="text-4xl font-display font-bold leading-none mb-1">24/7</div>
                    <div className="text-xs font-semibold uppercase tracking-wide">Availability</div>
                  </motion.div>

                  <div className="absolute bottom-8 left-8 flex items-center gap-3 bg-white/90 backdrop-blur-sm rounded-full px-4 py-2">
                    <div className="w-2.5 h-2.5 rounded-full bg-primary animate-pulse" />
                    <span className="text-sm font-semibold text-ink">System online</span>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      <section className="py-24 px-6 md:px-8 bg-sand/40">
        <div className="max-w-4xl mx-auto text-center">
          <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-4">Why it's different</div>
          <h2 className="text-3xl md:text-5xl mb-6">
            Not a form. <span className="text-primary-ink">An agent.</span>
          </h2>
          <p className="text-lg text-ink/55 leading-relaxed max-w-2xl mx-auto">
            Most health apps make you fill in dropdowns in English. Kare listens, decides what to ask
            next, checks your medications on its own, and follows up when it thinks you need it —
            without waiting to be asked.
          </p>
        </div>
      </section>

      <section id="features" className="py-24 px-6 md:px-8">
        <div className="max-w-[1400px] mx-auto">
          <div className="mb-16 max-w-xl">
            <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-3">What's included</div>
            <h2 className="text-4xl md:text-5xl">Everything a consultation needs<span className="text-primary-ink">.</span></h2>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            {FEATURES.map((f) => (
              <motion.div key={f.title} initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
                className="card card-hover">
                <div className={`w-14 h-14 rounded-2xl ${f.bg} flex items-center justify-center mb-6`}>
                  <f.icon size={26} className="text-ink" />
                </div>
                <h4 className="text-2xl mb-3">{f.title}</h4>
                <p className="text-sm text-ink/50 leading-relaxed">{f.description}</p>
              </motion.div>
            ))}
          </div>

          <div className="mt-20 grid md:grid-cols-2 gap-6">
            <div className="card bg-primary/25 border-primary/30">
              <h3 className="text-xl font-display font-bold text-primary-ink mb-4">With Kare</h3>
              <ul className="space-y-3">
                {['Speaks your language, mixed the way you actually talk', 'Remembers every past visit automatically',
                  'Checks in on its own after a consultation', 'Flags emergencies with local numbers, instantly'].map((t) => (
                  <li key={t} className="flex gap-3 text-sm text-ink/80"><Check size={16} className="text-primary-ink flex-shrink-0 mt-0.5" /> {t}</li>
                ))}
              </ul>
            </div>
            <div className="card bg-sand/30">
              <h3 className="text-xl font-display font-bold text-ink/70 mb-4">A typical health app</h3>
              <ul className="space-y-3">
                {['English-only dropdown forms', 'Starts from zero on every visit',
                  'Only responds when you open the app', 'No sense of urgency built in'].map((t) => (
                  <li key={t} className="flex gap-3 text-sm text-ink/50"><XIcon size={16} className="text-ink/30 flex-shrink-0 mt-0.5" /> {t}</li>
                ))}
              </ul>
            </div>
          </div>

          <div className="mt-16 text-center">
            <Link to="/features" className="inline-flex items-center gap-2 text-sm font-semibold text-primary-ink hover:gap-3 transition-all">
              View all features <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
