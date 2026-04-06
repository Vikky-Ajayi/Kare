import React from 'react';
import { motion } from 'motion/react';
import { 
  ArrowRight, 
  Play, 
  Activity, 
  Mic,
  Brain,
  Languages,
  ShieldAlert
} from 'lucide-react';
import { Link } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const Landing = () => {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.3
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  const features = [
    {
      icon: <Mic className="w-10 h-10" />,
      title: "Voice Doctor Consultation",
      description: "Your AI doctor listens to you speak, asks follow-up questions, and responds in full audio — just like a real consultation."
    },
    {
      icon: <Brain className="w-10 h-10" />,
      title: "Remembers You",
      description: "After every conversation, your doctor saves clinical notes about you. Next time you talk, it already knows your history."
    },
    {
      icon: <Languages className="w-10 h-10" />,
      title: "Speaks Your Language",
      description: "Full support for English, Yoruba, Hausa, Igbo, French, and Nigerian Pidgin. Ask in any language, get a full audio response."
    },
    {
      icon: <ShieldAlert className="w-10 h-10" />,
      title: "Drug Interaction Checker",
      description: "Type in your medications and instantly see if they interact dangerously. Powered by the NIH drug database."
    }
  ];

  return (
    <div className="min-h-screen bg-black text-white selection:bg-primary selection:text-black font-sans overflow-x-hidden">
      <Navbar />

      {/* Hero Section */}
      <section className="pt-48 pb-32 px-8">
        <div className="max-w-[1800px] mx-auto">
          <motion.div 
            variants={containerVariants}
            initial="hidden"
            animate="visible"
            className="relative"
          >
            <motion.div variants={itemVariants} className="mb-6">
              <span className="text-[10px] font-bold uppercase tracking-[0.5em] text-primary">Healthcare Reimagined</span>
            </motion.div>
            
            <motion.h1 
              variants={itemVariants} 
              className="text-[10vw] leading-[0.85] font-display font-bold tracking-tighter uppercase mb-16"
              style={{ fontSize: 'clamp(2.5rem, 10vw, 12rem)', hyphens: 'none' }}
            >
              {["kare", ".", "health"].map((word, i) => (
                <motion.span 
                  key={i}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.5 + i * 0.1, duration: 0.3 }}
                  className={word === "." ? "text-primary" : word === "health" ? "text-white/20 block" : ""}
                >
                  {word}
                </motion.span>
              ))}
            </motion.h1>
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-16 items-end">
              <motion.div variants={itemVariants} className="lg:col-span-5">
                <p className="text-2xl text-white/60 leading-tight mb-12 font-display font-medium uppercase tracking-tight">
                  A full-scale, end-to-end AI medical assistant built with a deep focus on accessibility for Africa.
                </p>
                <div className="flex flex-wrap gap-6">
                  <Link to="/register" className="btn-primary group flex items-center gap-3 min-h-[44px]">
                    Start Consultation
                    <ArrowRight className="w-5 h-5 group-hover:translate-x-2 transition-transform" />
                  </Link>
                  <button className="btn-outline flex items-center gap-3 group min-h-[44px]">
                    <div className="w-8 h-8 bg-white text-black flex items-center justify-center group-hover:bg-primary transition-colors">
                      <Play className="w-4 h-4 fill-current" />
                    </div>
                    Watch Demo
                  </button>
                </div>
              </motion.div>
              
              <motion.div variants={itemVariants} className="lg:col-span-7 relative">
                <div className="aspect-[16/10] bg-surface border-4 border-white/10 overflow-hidden relative group">
                  <img 
                    src="https://images.unsplash.com/photo-1576091160550-2173dba999ef?auto=format&fit=crop&q=80&w=2070" 
                    alt="Medical Tech"
                    className="w-full h-full object-cover opacity-40 grayscale group-hover:grayscale-0 group-hover:scale-105 transition-all duration-1000"
                    referrerPolicy="no-referrer"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent opacity-60"></div>
                  
                  {/* Floating Stats */}
                  <motion.div 
                    initial={{ x: 50, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 1, duration: 0.8 }}
                    className="absolute top-12 right-12 bg-primary p-8 text-black border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)]"
                  >
                    <div className="text-5xl font-display font-bold leading-none mb-1">24/7</div>
                    <div className="text-[10px] font-bold uppercase tracking-[0.3em]">Availability</div>
                  </motion.div>

                  <div className="absolute bottom-12 left-12">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-white text-black flex items-center justify-center border-2 border-black">
                        <Activity className="w-6 h-6" />
                      </div>
                      <div>
                        <div className="text-[10px] font-bold uppercase tracking-widest text-white/40">Live Status</div>
                        <div className="text-sm font-bold uppercase tracking-widest text-primary">System Online</div>
                      </div>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Quote Section */}
      <section className="py-48 bg-surface border-y-4 border-white/10 px-8 relative overflow-hidden">
        <div className="absolute top-0 left-0 w-full h-full opacity-[0.03] pointer-events-none">
          <div className="grid grid-cols-12 h-full">
            {[...Array(12)].map((_, i) => (
              <div key={i} className="border-r border-white h-full"></div>
            ))}
          </div>
        </div>
        
        <div className="max-w-[1200px] mx-auto text-center relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 40 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            className="mb-16"
          >
            <div className="w-32 h-32 mx-auto border-4 border-primary p-2 mb-8">
              <img 
                src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?auto=format&fit=crop&q=80&w=200&h=200" 
                alt="Dr. Ade"
                className="w-full h-full object-cover grayscale"
                referrerPolicy="no-referrer"
              />
            </div>
            <div className="font-display text-2xl font-bold uppercase tracking-tight">Dr. Adebayo Peters</div>
            <div className="text-[10px] text-primary font-bold uppercase tracking-[0.4em] mt-2">Chief Medical Officer</div>
          </motion.div>
          <motion.h2 
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="text-3xl md:text-5xl font-display font-bold leading-[1.3] tracking-tighter uppercase italic max-w-4xl mx-auto px-8"
            style={{ fontSize: 'clamp(1.75rem, 5vw, 3.5rem)', hyphens: 'none' }}
          >
            "We needed to build a complete medical ecosystem for our community — including diagnosis, prescriptions, and follow-ups."
          </motion.h2>
        </div>
      </section>

      {/* Scope of Work Grid */}
      <section id="features" className="py-48 px-8">
        <div className="max-w-[1800px] mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-end mb-24 gap-8">
            <div className="space-y-6">
              <div className="text-[10px] text-primary font-bold uppercase tracking-[0.5em]">Everything you need. Nothing you don't.</div>
              <h2 className="text-6xl md:text-9xl font-display font-bold uppercase tracking-tighter leading-[0.8]" style={{ fontSize: 'clamp(3.5rem, 10vw, 8rem)', hyphens: 'none' }}>Scope of<br/>Services<span className="text-primary">.</span></h2>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-white/40 font-bold uppercase tracking-[0.4em] mb-4">Designed by</div>
              <div className="font-display text-3xl font-bold uppercase tracking-tight">KARE HEALTH TECH</div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-px bg-white/10 border-4 border-white/10 items-stretch">
            {features.map((item, idx) => (
              <motion.div 
                key={idx} 
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: idx * 0.1 }}
                whileHover={{ scale: 1.02, zIndex: 10 }}
                className={`p-16 flex flex-col justify-between transition-all group cursor-pointer relative overflow-hidden bg-black hover:bg-surface min-h-[400px]`}
              >
                <div className="flex justify-between items-start relative z-10">
                  <div className="text-[10px] font-bold uppercase tracking-[0.4em] opacity-60">0{idx + 1}</div>
                  <div className={`w-16 h-16 flex items-center justify-center border-2 transition-all group-hover:scale-110 border-white/20 group-hover:border-primary group-hover:text-primary`}>
                    {item.icon}
                  </div>
                </div>
                <div className="relative z-10">
                  <h4 className="text-4xl font-display font-bold leading-none mb-8 uppercase tracking-tighter group-hover:text-primary transition-colors">{item.title}</h4>
                  <p className="text-xs text-white/40 font-bold uppercase tracking-widest leading-relaxed mb-8 opacity-0 group-hover:opacity-100 transition-opacity">
                    {item.description}
                  </p>
                  <div className={`w-12 h-12 flex items-center justify-center border-2 transition-all border-white/20 group-hover:border-primary group-hover:bg-primary group-hover:text-black`}>
                    <ArrowRight className="w-6 h-6" />
                  </div>
                </div>
                {/* Background Pattern */}
                <div className="absolute -bottom-10 -right-10 text-[15rem] font-display font-bold opacity-[0.03] pointer-events-none select-none">
                  {idx + 1}
                </div>
              </motion.div>
            ))}
          </div>
          
          <div className="mt-24 text-center">
            <Link to="/features" className="text-[10px] font-bold uppercase tracking-[0.5em] text-primary hover:underline flex items-center justify-center gap-4 group">
              View All Features
              <ArrowRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
            </Link>
          </div>
        </div>
      </section>

      <Footer />
    </div>
  );
};

export default Landing;
