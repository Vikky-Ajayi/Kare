import React from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { Globe, Mic, Brain, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const About = () => {
  return (
    <div className="min-h-screen bg-black text-white selection:bg-primary selection:text-black font-sans">
      <Navbar />

      <main>
        {/* Hero Section */}
        <section className="pt-48 pb-32 px-8">
          <div className="max-w-[1800px] mx-auto">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className="mb-24"
            >
              <h1 className="text-6xl md:text-9xl font-display font-bold uppercase tracking-tighter leading-[0.8] mb-12" style={{ fontSize: 'clamp(2.5rem, 10vw, 8rem)', hyphens: 'none' }}>
                Built for Africa.<br/>Designed for everyone<span className="text-primary">.</span>
              </h1>
              <p className="text-2xl text-white/40 font-bold uppercase tracking-tight max-w-2xl leading-tight">
                Kare was born from a simple belief — that quality healthcare guidance shouldn't depend on where you live, what language you speak, or how much money you have.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Mission Section */}
        <section className="py-48 bg-surface border-y-4 border-white/10 px-8">
          <div className="max-w-[1200px] mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="mb-16"
            >
              <div className="text-[10px] text-primary font-bold uppercase tracking-[0.5em] mb-12">Our Mission</div>
              <h2 className="text-3xl md:text-5xl font-display font-bold leading-[1.3] tracking-tighter uppercase italic max-w-4xl mx-auto px-8" style={{ fontSize: 'clamp(1.75rem, 5vw, 3.5rem)', hyphens: 'none' }}>
                "We're building a voice-first AI medical assistant that thinks like a doctor, speaks like a friend, and remembers like a family physician who has known you for years."
              </h2>
              <p className="text-xl text-white/40 font-bold uppercase tracking-widest mt-16 max-w-3xl mx-auto leading-relaxed">
                Kare is not a replacement for doctors — it's the knowledgeable friend that helps you know when to see one, what to ask, and what to watch out for.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Differentiators Section */}
        <section className="py-48 px-8">
          <div className="max-w-[1800px] mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10 border-4 border-white/10 items-stretch">
              {[
                {
                  icon: <Globe className="w-12 h-12" />,
                  title: "Built for Nigeria and Africa",
                  description: "Local context, local languages, tropical diseases considered first."
                },
                {
                  icon: <Mic className="w-12 h-12" />,
                  title: "Voice-first",
                  description: "Designed for people who prefer to speak, not type."
                },
                {
                  icon: <Brain className="w-12 h-12" />,
                  title: "Gets smarter per patient",
                  description: "Builds a clinical profile with every conversation."
                }
              ].map((item, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.1 }}
                  className="p-16 bg-black flex flex-col justify-between group hover:bg-surface transition-all min-h-[400px]"
                >
                  <div className="w-20 h-20 flex items-center justify-center border-2 border-white/10 group-hover:border-primary group-hover:text-primary transition-all">
                    {item.icon}
                  </div>
                  <div>
                    <h3 className="text-4xl font-display font-bold uppercase tracking-tighter leading-none mb-8 group-hover:text-primary transition-colors">
                      {item.title}
                    </h3>
                    <p className="text-sm text-white/40 font-bold uppercase tracking-widest leading-relaxed">
                      {item.description}
                    </p>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* Disclaimer */}
        <section className="py-24 px-8 border-t-4 border-white/10">
          <div className="max-w-[1800px] mx-auto text-center">
            <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em] max-w-2xl mx-auto">
              Kare is an AI-powered health information tool. It is not a licensed medical provider and does not replace professional medical advice. Always consult a qualified healthcare professional.
            </p>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default About;
