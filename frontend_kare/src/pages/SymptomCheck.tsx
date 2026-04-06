import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Search, 
  ChevronRight, 
  AlertCircle,
  Thermometer,
  Activity,
  Brain,
  Wind,
  ArrowRight,
  Loader2,
  CheckCircle2,
  XCircle,
  Info
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { SymptomCheckResult } from '../types';

const SymptomCheck = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<SymptomCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleCheckSymptoms = async (symptoms: string) => {
    if (!symptoms.trim()) return;
    
    setIsLoading(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await api.post('/symptom-check', { symptoms });
      setResult(response.data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to analyze symptoms. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const commonSymptoms = [
    { icon: Thermometer, label: 'Fever', color: 'text-primary' },
    { icon: Activity, label: 'Chest Pain', color: 'text-red-500' },
    { icon: Brain, label: 'Headache', color: 'text-primary' },
    { icon: Wind, label: 'Breathless', color: 'text-primary' },
  ];

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1 }
  };

  return (
    <motion.div 
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-4xl mx-auto space-y-12 p-8 pb-32"
    >
      <motion.div variants={itemVariants}>
        <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Diagnostic Tool</div>
        <h1 className="text-5xl font-display font-bold tracking-tighter uppercase">Symptom Checker<span className="text-primary">.</span></h1>
        <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Identify potential health issues based on your symptoms.</p>
      </motion.div>

      <motion.div variants={itemVariants} className="brutalist-card p-12 bg-surface border-2 border-white/10">
        <div className="relative mb-12 group">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-primary transition-colors" size={20} />
          <input 
            type="text"
            placeholder="Search symptoms (e.g. headache, fatigue...)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCheckSymptoms(searchQuery)}
            className="w-full pl-16 pr-6 py-6 bg-black border-2 border-white/10 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white placeholder:text-white/20"
          />
          <button 
            onClick={() => handleCheckSymptoms(searchQuery)}
            disabled={isLoading || !searchQuery.trim()}
            className="absolute right-4 top-1/2 -translate-y-1/2 btn-primary py-3 px-6 disabled:opacity-50"
          >
            {isLoading ? <Loader2 size={16} className="animate-spin" /> : <ArrowRight size={16} />}
          </button>
        </div>

        <div className="space-y-8">
          <h2 className="text-[10px] font-bold text-white/20 uppercase tracking-[0.4em]">Common Symptoms</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-px bg-white/10 border-2 border-white/10">
            {commonSymptoms.map((symptom) => (
              <motion.button 
                key={symptom.label}
                whileHover={{ backgroundColor: 'rgba(0, 255, 209, 0.05)' }}
                onClick={() => {
                  setSearchQuery(symptom.label);
                  handleCheckSymptoms(symptom.label);
                }}
                className="p-10 bg-black transition-all flex flex-col items-center gap-6 group"
              >
                <div className={cn("w-20 h-20 border-2 border-white/10 flex items-center justify-center transition-all group-hover:border-primary group-hover:bg-primary/10", symptom.color)}>
                  <symptom.icon size={36} className="group-hover:scale-110 transition-transform" />
                </div>
                <span className="text-[10px] font-bold uppercase tracking-[0.2em] text-white/40 group-hover:text-white transition-all">{symptom.label}</span>
              </motion.button>
            ))}
          </div>
        </div>
      </motion.div>

      <AnimatePresence>
        {error && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            className="brutalist-card p-8 bg-red-500/10 border-2 border-red-500 flex items-center gap-6"
          >
            <XCircle size={32} className="text-red-500" />
            <p className="text-[10px] font-bold uppercase tracking-widest text-red-500">{error}</p>
          </motion.div>
        )}

        {result && (
          <motion.div 
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-8"
          >
            <div className={cn(
              "brutalist-card p-12 border-l-8 transition-all",
              result.triage_level === 'EMERGENCY' ? "border-l-red-500 bg-red-500/5" :
              result.triage_level === 'URGENT' ? "border-l-orange-500 bg-orange-500/5" :
              "border-l-primary bg-primary/5"
            )}>
              <div className="flex justify-between items-start mb-10">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/20 mb-2">Analysis Result</div>
                  <h3 className="text-4xl font-display font-bold uppercase tracking-tighter">{result.triage_level}</h3>
                </div>
                <div className={cn(
                  "w-16 h-16 border-2 flex items-center justify-center",
                  result.triage_level === 'EMERGENCY' ? "border-red-500 text-red-500" : "border-primary text-primary"
                )}>
                  <Activity size={32} />
                </div>
              </div>
              <p className="text-sm font-bold uppercase tracking-widest text-white leading-relaxed mb-10 max-w-2xl">
                {result.triage_explanation}
              </p>
              
              <div className="grid md:grid-cols-2 gap-12">
                <div className="space-y-6">
                  <h4 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary">Possible Conditions</h4>
                  <ul className="space-y-4">
                    {result.possible_conditions.map((cond, i) => (
                      <li key={i} className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-white/60">
                        <span className="w-2 h-2 bg-primary"></span> {cond}
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="space-y-6">
                  <h4 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary">Recommendations</h4>
                  <ul className="space-y-4">
                    {result.recommendations.map((rec, i) => (
                      <li key={i} className="flex items-center gap-4 text-[10px] font-bold uppercase tracking-widest text-white/60">
                        <CheckCircle2 size={14} className="text-primary" /> {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>

            {result.triage_level === 'EMERGENCY' && (
              <div className="brutalist-card p-10 bg-red-500 text-black border-4 border-black">
                <div className="flex items-center gap-6 mb-6">
                  <AlertCircle size={32} />
                  <h4 className="text-2xl font-display font-bold uppercase tracking-tight">Emergency Warning</h4>
                </div>
                <p className="text-xs font-bold uppercase tracking-widest leading-relaxed">
                  {result.when_to_seek_emergency}
                </p>
              </div>
            )}

            <div className="p-8 border-2 border-white/5 bg-black/40 flex items-start gap-6">
              <Info size={20} className="text-white/20 flex-shrink-0" />
              <p className="text-[8px] font-bold uppercase tracking-widest text-white/20 leading-relaxed italic">
                {result.disclaimer}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid md:grid-cols-2 gap-8">
        <motion.div 
          variants={itemVariants}
          whileHover={{ y: -5 }}
          className="brutalist-card p-10 bg-surface border-l-8 border-l-primary group cursor-pointer hover:bg-black transition-all border-2 border-white/10"
        >
          <div className="flex items-start gap-8">
            <div className="w-16 h-16 bg-black border-2 border-white/10 flex items-center justify-center text-primary flex-shrink-0 group-hover:border-primary transition-all">
              <Activity size={28} />
            </div>
            <div>
              <h3 className="text-2xl font-display font-bold uppercase tracking-tight mb-3">Full Assessment</h3>
              <p className="text-[10px] text-white/40 font-bold uppercase tracking-[0.2em] leading-relaxed mb-8">
                Answer a series of questions for a more accurate symptom analysis.
              </p>
              <button className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary flex items-center gap-3 group-hover:gap-5 transition-all">
                Begin now <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          whileHover={{ y: -5 }}
          className="brutalist-card p-10 bg-surface border-l-8 border-l-red-500 group cursor-pointer hover:bg-black transition-all border-2 border-white/10"
        >
          <div className="flex items-start gap-8">
            <div className="w-16 h-16 bg-black border-2 border-white/10 flex items-center justify-center text-red-500 flex-shrink-0 group-hover:border-red-500 transition-all">
              <AlertCircle size={28} />
            </div>
            <div>
              <h3 className="text-2xl font-display font-bold uppercase tracking-tight mb-3">Emergency Check</h3>
              <p className="text-[10px] text-white/40 font-bold uppercase tracking-[0.2em] leading-relaxed mb-8">
                If you are experiencing severe symptoms, seek immediate help.
              </p>
              <button className="text-[10px] font-bold uppercase tracking-[0.3em] text-red-500 flex items-center gap-3 group-hover:gap-5 transition-all">
                Emergency guide <ArrowRight size={18} />
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
};

export default SymptomCheck;
