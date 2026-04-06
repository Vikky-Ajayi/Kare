import React from 'react';
import { motion, useScroll, useTransform } from 'motion/react';
import { Link } from 'react-router-dom';
import { Stethoscope, Zap, Languages, Clock, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const StatCounter = ({ value, label, sublabel }: { value: string, label: string, sublabel: string }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className={`p-12 bg-black border-2 border-white/10 hover:border-primary transition-all group overflow-hidden ${value === '1:2,500' ? 'px-6' : ''}`}
    >
      <div 
        className={`font-display font-bold text-primary mb-4 group-hover:scale-110 transition-transform origin-left whitespace-nowrap ${value === '1:2,500' ? 'text-4xl sm:text-5xl md:text-6xl' : 'text-7xl'}`}
      >
        {value}
      </div>
      <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-white mb-2">
        {label}
      </div>
      <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">
        {sublabel}
      </div>
    </motion.div>
  );
};

const Impact = () => {
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
                The problem<br/>is real<span className="text-primary">.</span>
              </h1>
              <p className="text-2xl text-white/40 font-bold uppercase tracking-tight max-w-2xl leading-tight">
                In Nigeria alone, there is less than 1 doctor for every 2,500 people. Millions consult Google for symptoms. Millions more wait weeks for something that needed attention days ago.
              </p>
            </motion.div>
          </div>
        </section>

        {/* Stats Grid */}
        <section className="py-24 px-8 bg-surface border-y-4 border-white/10">
          <div className="max-w-[1800px] mx-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <StatCounter 
                value="1:2,500" 
                label="Doctor to Patient" 
                sublabel="Ratio in Nigeria" 
              />
              <StatCounter 
                value="40%" 
                label="Mobile Health" 
                sublabel="Adoption Rate" 
              />
              <StatCounter 
                value="6" 
                label="Native Languages" 
                sublabel="Kare Speaks Fluently" 
              />
              <StatCounter 
                value="24/7" 
                label="Always Available" 
                sublabel="No Appointment Needed" 
              />
            </div>
          </div>
        </section>

        {/* The Gap Section */}
        <section className="py-48 px-8">
          <div className="max-w-[1200px] mx-auto text-center">
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
            >
              <div className="text-[10px] text-primary font-bold uppercase tracking-[0.5em] mb-12">The Gap</div>
              <h2 className="text-3xl md:text-5xl font-display font-bold leading-[1.3] tracking-tighter uppercase italic mb-16 max-w-4xl mx-auto px-8" style={{ fontSize: 'clamp(1.75rem, 5vw, 3.5rem)', hyphens: 'none' }}>
                "Between not feeling well and seeing a doctor, there is a dangerous window of uncertainty. People self-medicate. They wait too long. They don't know what questions to ask. Kare closes that window."
              </h2>
            </motion.div>
          </div>
        </section>

        {/* How Kare Helps Section */}
        <section className="py-48 px-8 bg-surface border-t-4 border-white/10">
          <div className="max-w-[1800px] mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-px bg-white/10 border-4 border-white/10 items-stretch">
              {[
                {
                  icon: <Stethoscope className="w-12 h-12" />,
                  title: "Better triage",
                  description: "Know when something is a real emergency vs when to rest at home."
                },
                {
                  icon: <Zap className="w-12 h-12" />,
                  title: "Safer medication",
                  description: "Catch dangerous drug interactions before they harm you."
                },
                {
                  icon: <Languages className="w-12 h-12" />,
                  title: "Informed patients",
                  description: "Walk into every doctor's visit knowing your history and your questions."
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

        {/* Closing Statement */}
        <section className="py-48 px-8 border-t-4 border-white/10 relative overflow-hidden">
          <div className="max-w-[1200px] mx-auto text-center relative z-10">
            <motion.h2
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              viewport={{ once: true }}
              className="text-3xl md:text-6xl font-display font-bold leading-[1.2] tracking-tighter uppercase mb-16 max-w-5xl mx-auto px-8"
              style={{ fontSize: 'clamp(1.75rem, 6vw, 4rem)', hyphens: 'none' }}
            >
              We are not trying to replace the Nigerian healthcare system. We are trying to make every Nigerian a more informed, empowered patient within it.
            </motion.h2>
            <Link to="/register" className="btn-primary inline-flex items-center gap-4 group">
              Join the Mission
              <ArrowRight className="w-6 h-6 group-hover:translate-x-2 transition-transform" />
            </Link>
          </div>
          {/* Background Decorative Element */}
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[40vw] font-display font-bold opacity-[0.02] pointer-events-none select-none uppercase">
            Impact
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Impact;
