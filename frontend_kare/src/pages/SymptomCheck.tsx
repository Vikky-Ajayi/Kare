import React, { useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Loader2, AlertTriangle, CheckCircle2, ArrowRight, Info } from 'lucide-react';
import { cn } from '../lib/utils';
import { LANGUAGES, type LangCode, type SymptomCheckResult } from '../types';
import { symptoms as api, errMsg } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';

const LEVEL_STYLE: Record<string, string> = {
  EMERGENCY: 'border-l-red-500 bg-red-50/60', URGENT: 'border-l-orange-500 bg-orange-50/60',
  SEMI_URGENT: 'border-l-yellow-500 bg-yellow-50/60', NON_URGENT: 'border-l-primary bg-mint/30',
  SELF_CARE: 'border-l-primary bg-mint/30',
};

const SymptomCheck = () => {
  const user = useAuthStore((s) => s.user);
  const [text, setText] = useState('');
  const [language, setLanguage] = useState<LangCode>((user?.preferred_language as LangCode) || 'en');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SymptomCheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const run = async () => {
    if (text.trim().length < 5) return;
    setLoading(true); setError(null); setResult(null);
    try {
      setResult(await api.check({ symptoms: text.trim(), language, include_patient_history: true }));
    } catch (e) {
      setError(errMsg(e, 'Could not analyse your symptoms.'));
    } finally { setLoading(false); }
  };

  return (
    <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="max-w-3xl mx-auto space-y-8 p-6 md:p-8 pb-24">
      <div>
        <div className="text-xs font-semibold text-primary-ink/70 mb-2">Symptom Check</div>
        <h1 className="text-4xl">How are you feeling<span className="text-primary-ink">?</span></h1>
        <p className="text-ink/40 text-sm mt-2">Describe it in your own words. Kare uses your history.</p>
      </div>

      <div className="card space-y-4">
        <textarea rows={4} value={text} onChange={(e) => setText(e.target.value)}
          placeholder="e.g. I've had a headache and fever since yesterday, and my body aches…"
          className="w-full input-field resize-none" />
        <div className="flex gap-3">
          <select value={language} onChange={(e) => setLanguage(e.target.value as LangCode)}
            className="input-field text-sm font-medium">
            {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
          <button onClick={run} disabled={loading || text.trim().length < 5}
            className="btn-primary flex-1 disabled:opacity-40">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <><Search size={16} /> Check symptoms</>}
          </button>
        </div>
      </div>

      <AnimatePresence>
        {error && <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-red-600 text-sm font-medium">{error}</motion.p>}
        {result && (
          <motion.div initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
            <div className={cn('card border-l-8', LEVEL_STYLE[result.triage_level] || LEVEL_STYLE.NON_URGENT)}>
              <div className="text-xs font-semibold text-ink/40 mb-1 uppercase tracking-wide">Assessment</div>
              <h3 className="text-3xl mb-4">{result.triage_level.replace('_', ' ')}</h3>
              <p className="text-sm text-ink/80 leading-relaxed mb-6">{result.triage_explanation}</p>

              {result.possible_conditions?.length > 0 && (
                <div className="mb-5">
                  <h4 className="text-xs font-semibold text-primary-ink/80 mb-2 uppercase tracking-wide">Possible causes</h4>
                  <ul className="space-y-1.5">
                    {result.possible_conditions.map((c, i) => (
                      <li key={i} className="text-sm text-ink/60 flex gap-2">
                        <span className="text-primary-ink">›</span> {c.condition}{c.likelihood ? ` — ${c.likelihood}` : ''}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              <div>
                <h4 className="text-xs font-semibold text-primary-ink/80 mb-2 uppercase tracking-wide flex items-center gap-2"><CheckCircle2 size={12} /> What to do</h4>
                <p className="text-sm text-ink/70 leading-relaxed">{result.recommendations}</p>
              </div>
            </div>

            {result.triage_level === 'EMERGENCY' && (
              <div className="card bg-red-600 text-white border-none flex gap-4">
                <AlertTriangle size={24} className="flex-shrink-0" />
                <div>
                  <h4 className="text-lg font-display font-bold mb-1">Get help now</h4>
                  <p className="text-sm font-medium leading-relaxed">{result.when_to_seek_emergency}</p>
                </div>
              </div>
            )}
            <div className="p-4 rounded-2xl bg-ink/[0.03] flex gap-3">
              <Info size={16} className="text-ink/30 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-ink/40 leading-relaxed">{result.disclaimer}</p>
            </div>
            <a href="/dashboard/voice" className="flex items-center justify-center gap-2 text-sm font-semibold text-primary-ink hover:gap-3 transition-all">
              Talk it through with Kare <ArrowRight size={14} />
            </a>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default SymptomCheck;
