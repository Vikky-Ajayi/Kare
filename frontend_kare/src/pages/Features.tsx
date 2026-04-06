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
  ArrowRight
} from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Features = () => {
  const features = [
    {
      icon: <Mic className="w-10 h-10" />,
      title: "Voice Doctor Consultation",
      description: "Your AI doctor listens to you speak, asks follow-up questions, and responds in full audio — just like a real consultation. Hands-free, no typing needed."
    },
    {
      icon: <Brain className="w-10 h-10" />,
      title: "Remembers You",
      description: "After every conversation, your doctor saves clinical notes about you. Next time you talk, it already knows your history, your complaints, and what to follow up on."
    },
    {
      icon: <Languages className="w-10 h-10" />,
      title: "Speaks Your Language",
      description: "Full support for English, Yoruba, Hausa, Igbo, French, and Nigerian Pidgin. Ask in any language, get a full audio response in the same language."
    },
    {
      icon: <ShieldAlert className="w-10 h-10" />,
      title: "Drug Interaction Checker",
      description: "Type in your medications and instantly see if they interact dangerously. Powered by the NIH drug database — the same one doctors use."
    },
    {
      icon: <Stethoscope className="w-10 h-10" />,
      title: "Symptom Triage",
      description: "Describe your symptoms and get a triage assessment — Emergency, Urgent, Semi-Urgent, Non-Urgent, or Self-Care — with clear next steps."
    },
    {
      icon: <History className="w-10 h-10" />,
      title: "Your Full Medical History",
      description: "Store your conditions, medications, allergies, and blood group in one place. Your doctor reads all of it before every consultation."
    },
    {
      icon: <Camera className="w-10 h-10" />,
      title: "Medication Photo Analysis",
      description: "Take a photo of any pill, packaging, or medical document and the AI will identify and explain it."
    },
    {
      icon: <Info className="w-10 h-10" />,
      title: "Always Transparent",
      description: "Every AI response includes a reminder that this supplements — not replaces — seeing a real doctor."
    }
  ];

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
                Everything you need.<br/>Nothing you don't<span className="text-primary">.</span>
              </h1>
              <p className="text-2xl text-white/40 font-bold uppercase tracking-tight max-w-2xl leading-tight">
                Kare is built to be your first point of contact for any health concern. Simple, fast, and reliable.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Statement Section */}
        <section className="py-48 bg-surface border-y-4 border-white/10 px-8">
          <div className="max-w-[1200px] mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="mb-16"
            >
              <div className="text-[10px] text-primary font-bold uppercase tracking-[0.5em] mb-12">The Kare Experience</div>
              <h2 className="text-3xl md:text-5xl font-display font-bold leading-[1.3] tracking-tighter uppercase italic max-w-4xl mx-auto px-8" style={{ fontSize: 'clamp(1.75rem, 5vw, 3.5rem)', hyphens: 'none' }}>
                "We've combined advanced clinical AI with a voice-first interface to create a medical assistant that actually listens, understands, and responds like a human doctor."
              </h2>
            </motion.div>
          </div>
        </section>

        {/* Features Grid Section */}
        <section className="py-48 px-8">
          <div className="max-w-[1800px] mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 border-4 border-white/10 items-stretch">
              {features.map((feature, idx) => (
                <motion.div
                  key={idx}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ delay: idx * 0.05, duration: 0.3 }}
                  whileHover={{ scale: 1.02, zIndex: 10 }}
                  className="p-16 bg-black flex flex-col justify-between group hover:bg-surface transition-all min-h-[450px] relative overflow-hidden"
                >
                  <div className="flex justify-between items-start relative z-10">
                    <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/40 group-hover:text-primary transition-colors">
                      0{idx + 1}
                    </div>
                    <div className="w-20 h-20 flex items-center justify-center border-2 border-white/10 group-hover:border-primary group-hover:text-primary transition-all">
                      {feature.icon}
                    </div>
                  </div>
                  
                  <div className="relative z-10">
                    <h3 className="text-4xl font-display font-bold uppercase tracking-tighter leading-none mb-8 group-hover:text-primary transition-colors">
                      {feature.title}
                    </h3>
                    <p className="text-sm text-white/40 font-bold uppercase tracking-widest leading-relaxed">
                      {feature.description}
                    </p>
                  </div>

                  {/* Decorative background number */}
                  <div className="absolute -bottom-10 -right-10 text-[15rem] font-display font-bold opacity-[0.02] pointer-events-none select-none group-hover:opacity-[0.05] transition-opacity">
                    {idx + 1}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        {/* CTA Section */}
        <section className="py-48 px-8 border-t-4 border-white/10 relative overflow-hidden">
          <div className="max-w-[1200px] mx-auto text-center relative z-10">
            <motion.h2
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="text-3xl md:text-6xl font-display font-bold leading-[1.2] tracking-tighter uppercase mb-16 max-w-5xl mx-auto px-8"
              style={{ fontSize: 'clamp(1.75rem, 6vw, 4rem)', hyphens: 'none' }}
            >
              Ready to experience the future of healthcare?
            </motion.h2>
            <Link to="/register" className="btn-primary inline-flex items-center gap-4 group">
              Get Started Now
              <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </Link>
          </div>
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[40vw] font-display font-bold opacity-[0.02] pointer-events-none select-none uppercase">
            Features
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Features;
