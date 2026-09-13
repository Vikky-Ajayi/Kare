import React from 'react';
import { motion } from 'motion/react';
import {
  Mic,
  Brain,
  Languages,
  ShieldAlert,
  Stethoscope,
  History,
  Camera,
  Info,
  ArrowRight,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const PASTELS = ['bg-mint', 'bg-lavender', 'bg-peach', 'bg-pink', 'bg-sand', 'bg-mint', 'bg-lavender', 'bg-peach'];

const FEATURES = [
  { icon: Mic, title: 'Voice doctor consultation',
    description: "Your AI doctor listens to you speak, asks follow-up questions, and responds in full audio — just like a real consultation. Hands-free, no typing needed." },
  { icon: Brain, title: 'Remembers you',
    description: 'After every conversation, Kare saves clinical notes about you. Next time you talk, it already knows your history, your complaints, and what to follow up on.' },
  { icon: Languages, title: 'Speaks your language',
    description: 'Full support for English, Yoruba, Hausa, Igbo and Nigerian Pidgin. Ask in any of them, get a full audio response in the same language.' },
  { icon: ShieldAlert, title: 'Drug interaction checker',
    description: 'Type in your medications and instantly see if they interact dangerously, backed by the RxNorm database — the same one doctors use.' },
  { icon: Stethoscope, title: 'Symptom triage',
    description: 'Describe your symptoms and get a triage assessment — Emergency, Urgent, Semi-Urgent, Non-Urgent, or Self-Care — with clear next steps.' },
  { icon: History, title: 'Your full medical history',
    description: 'Store your conditions, medications, allergies, and blood group in one place. Kare reads all of it before every consultation.' },
  { icon: Camera, title: 'Medication photo analysis',
    description: 'Take a photo of any pill, packaging, or medical document and Kare will identify and explain it.' },
  { icon: Info, title: 'Always transparent',
    description: 'Every response includes a reminder that this supplements — not replaces — seeing a real doctor.' },
];

const Features = () => {
  return (
    <div className="min-h-screen bg-background text-ink selection:bg-primary selection:text-primary-ink font-sans">
      <Navbar />

      <main>
        <section className="pt-40 pb-24 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="badge bg-mint text-ink mb-6">The Kare experience</div>
              <h1 className="text-5xl md:text-7xl mb-8 max-w-3xl">
                Everything a consultation needs<span className="text-primary-ink">.</span>
              </h1>
              <p className="text-lg text-ink/55 max-w-2xl leading-relaxed">
                Kare is built to be your first point of contact for any health concern — combining
                voice-first AI with a clinical memory, so it actually listens, understands, and follows up.
              </p>
            </motion.div>
          </div>
        </section>

        <section className="py-20 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {FEATURES.map((f, idx) => (
              <motion.div
                key={f.title}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.04, duration: 0.3 }}
                className="card card-hover flex flex-col"
              >
                <div className={`w-14 h-14 rounded-2xl ${PASTELS[idx]} flex items-center justify-center mb-6`}>
                  <f.icon size={26} className="text-ink" />
                </div>
                <h3 className="text-xl mb-3">{f.title}</h3>
                <p className="text-sm text-ink/50 leading-relaxed">{f.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="py-24 px-6 md:px-8 bg-mint/40">
          <div className="max-w-3xl mx-auto text-center">
            <motion.h2
              initial={{ opacity: 0, scale: 0.96 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
              className="text-3xl md:text-5xl mb-10"
            >
              Ready to experience healthcare that understands you?
            </motion.h2>
            <Link to="/register" className="btn-primary inline-flex">
              Get started now
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Features;
