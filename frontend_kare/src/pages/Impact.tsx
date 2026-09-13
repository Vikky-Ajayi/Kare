import React from 'react';
import { motion } from 'motion/react';
import { Link } from 'react-router-dom';
import { Stethoscope, Zap, Languages, ArrowRight } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';

const StatCard = ({ value, label, sublabel, bg }: { value: string; label: string; sublabel: string; bg: string }) => (
  <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}
    className="card card-hover">
    <div className={`w-12 h-12 rounded-2xl ${bg} mb-6`} />
    <div className="text-4xl font-display font-bold text-ink mb-2 whitespace-nowrap">{value}</div>
    <div className="text-sm font-semibold text-ink/70 mb-1">{label}</div>
    <div className="text-xs text-ink/35">{sublabel}</div>
  </motion.div>
);

const Impact = () => {
  return (
    <div className="min-h-screen bg-background text-ink selection:bg-primary selection:text-primary-ink font-sans">
      <Navbar />

      <main>
        <section className="pt-40 pb-20 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto">
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.3 }}>
              <div className="badge bg-peach text-ink mb-6">The problem</div>
              <h1 className="text-5xl md:text-7xl mb-8 max-w-3xl">
                The gap is real<span className="text-primary-ink">.</span>
              </h1>
              <p className="text-lg text-ink/55 max-w-2xl leading-relaxed">
                In Nigeria, there is roughly one doctor for every 2,500 people. Millions consult Google
                for symptoms. Millions more wait weeks for something that needed attention days ago.
              </p>
            </motion.div>
          </div>
        </section>

        <section className="py-12 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            <StatCard value="1 : 2,500" label="Doctor to patient" sublabel="ratio in Nigeria" bg="bg-mint" />
            <StatCard value="~70%" label="Code-switch daily" sublabel="Yoruba/Hausa/Igbo/Pidgin + English" bg="bg-lavender" />
            <StatCard value="5" label="Languages" sublabel="Kare speaks fluently" bg="bg-peach" />
            <StatCard value="24/7" label="Always available" sublabel="no appointment needed" bg="bg-pink" />
          </div>
        </section>

        <section className="py-24 px-6 md:px-8 bg-sand/40">
          <div className="max-w-3xl mx-auto text-center">
            <motion.div initial={{ opacity: 0, y: 30 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }}>
              <div className="text-xs font-semibold text-primary-ink/70 uppercase tracking-wide mb-6">The gap</div>
              <h2 className="text-2xl md:text-4xl leading-snug">
                Between not feeling well and seeing a doctor, there is a dangerous window of
                uncertainty — people self-medicate, wait too long, or don't know what questions to
                ask. Kare closes that window.
              </h2>
            </motion.div>
          </div>
        </section>

        <section className="py-24 px-6 md:px-8">
          <div className="max-w-[1400px] mx-auto">
            <div className="mb-14 max-w-xl">
              <h2 className="text-4xl">How Kare helps<span className="text-primary-ink">.</span></h2>
            </div>
            <div className="grid md:grid-cols-3 gap-6">
              {[
                { icon: Stethoscope, bg: 'bg-mint', title: 'Better triage', description: 'Know when something is a real emergency vs. when to rest at home.' },
                { icon: Zap, bg: 'bg-lavender', title: 'Safer medication', description: 'Catch dangerous drug interactions before they harm you.' },
                { icon: Languages, bg: 'bg-peach', title: 'Informed patients', description: "Walk into every doctor's visit knowing your history and your questions." },
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
          </div>
        </section>

        <section className="py-24 px-6 md:px-8 bg-mint/40">
          <div className="max-w-3xl mx-auto text-center">
            <motion.h2 initial={{ opacity: 0, scale: 0.96 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }}
              className="text-2xl md:text-4xl leading-snug mb-10">
              We are not trying to replace the Nigerian healthcare system — we are trying to make
              every Nigerian a more informed, empowered patient within it.
            </motion.h2>
            <Link to="/register" className="btn-primary inline-flex group">
              Join the mission
              <ArrowRight size={20} className="group-hover:translate-x-1 transition-transform" />
            </Link>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
};

export default Impact;
