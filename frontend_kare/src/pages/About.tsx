import React from 'react';
import { motion } from 'motion/react';
import { Globe, Mic, Brain } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const About = () => {
  return (
    <div className="min-h-screen bg-background text-ink selection:bg-primary selection:text-primary-ink font-sans">
      <Navbar />

      <main>
        <section className="pt-40 pb-20 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="badge bg-lavender text-ink mb-6">Our story</div>
              <h1 className="text-5xl md:text-7xl mb-8 max-w-3xl">
                Built for Africa. Designed for everyone<span className="text-primary-ink">.</span>
              </h1>
              <p className="text-lg text-ink/55 max-w-2xl leading-relaxed">
                Kare was born from a simple belief — that quality healthcare guidance shouldn't depend
                on where you live, what language you speak, or how much money you have.
              </p>
            </motion.div>
          </div>
        </section>

        <section className="py-20 px-6 md:px-8 bg-sand/40">
          <div className="max-w-3xl mx-auto text-center">
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
              <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-6">Our mission</div>
              <h2 className="text-2xl md:text-4xl leading-snug mb-8">
                We're building a voice-first AI medical assistant that thinks like a doctor, speaks
                like a friend, and remembers like a family physician who has known you for years.
              </h2>
              <p className="text-base text-ink/55 max-w-xl mx-auto leading-relaxed">
                Kare is not a replacement for doctors — it's the knowledgeable friend that helps you
                know when to see one, what to ask, and what to watch out for.
              </p>
            </motion.div>
          </div>
        </section>

        <section className="py-24 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto grid md:grid-cols-3 gap-6">
            {[
              { icon: Globe, bg: 'bg-mint', title: 'Built for Nigeria and Africa', description: 'Local context, local languages, tropical diseases considered first.' },
              { icon: Mic, bg: 'bg-lavender', title: 'Voice-first', description: 'Designed for people who prefer to speak, not type.' },
              { icon: Brain, bg: 'bg-peach', title: 'Gets smarter per patient', description: 'Builds a clinical profile with every conversation.' },
            ].map((item, idx) => (
              <motion.div key={item.title} initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ delay: idx * 0.1 }} className="card card-hover">
                <div className={`w-14 h-14 rounded-2xl ${item.bg} flex items-center justify-center mb-6`}>
                  <item.icon size={26} className="text-ink" />
                </div>
                <h3 className="text-2xl mb-3">{item.title}</h3>
                <p className="text-sm text-ink/50 leading-relaxed">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </section>

        <section className="py-12 px-6 md:px-8">
          <div className="max-w-2xl mx-auto text-center">
            <p className="text-sm text-ink/40 leading-relaxed">
              Kare is an AI-powered health information tool. It is not a licensed medical provider and
              does not replace professional medical advice. Always consult a qualified healthcare professional.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default About;
