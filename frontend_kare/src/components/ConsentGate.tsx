import React, { useState } from 'react';
import { motion } from 'motion/react';
import { ShieldCheck, Check } from 'lucide-react';

const KEY = 'kare_consult_consent_v1';

export function hasConsented(): boolean {
  try { return localStorage.getItem(KEY) === 'yes'; } catch { return false; }
}

/** Blocks the first consultation until the patient accepts. Renders nothing after. */
const ConsentGate = ({ onAccept }: { onAccept: () => void }) => {
  const [seen] = useState(hasConsented);
  const [checks, setChecks] = useState({ voice: false, ai: false });
  if (seen) return null;

  const ready = checks.voice && checks.ai;
  const accept = () => {
    try { localStorage.setItem(KEY, 'yes'); } catch { /* private mode */ }
    onAccept();
  };

  const Item = ({ k, children }: { k: 'voice' | 'ai'; children: React.ReactNode }) => (
    <button onClick={() => setChecks((c) => ({ ...c, [k]: !c[k] }))}
      className="w-full text-left flex gap-3 items-start p-3 border-2 border-white/10 hover:border-primary/40 transition-colors">
      <div className={`w-5 h-5 flex-shrink-0 border-2 flex items-center justify-center mt-0.5 ${checks[k] ? 'bg-primary border-primary' : 'border-white/20'}`}>
        {checks[k] && <Check size={12} className="text-black" />}
      </div>
      <span className="text-xs text-white/60 leading-relaxed">{children}</span>
    </button>
  );

  return (
    <div className="fixed inset-0 z-[60] flex items-center justify-center p-6 bg-black/85 backdrop-blur-sm">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md bg-surface border-4 border-white/10 p-8">
        <ShieldCheck size={28} className="text-primary mb-4" />
        <h2 className="text-2xl font-display font-bold uppercase tracking-tighter mb-2">Before we start<span className="text-primary">.</span></h2>
        <p className="text-[10px] text-white/40 uppercase tracking-widest mb-6 leading-relaxed">
          A quick note on how this works and what happens to what you share.
        </p>
        <div className="space-y-3 mb-6">
          <Item k="voice">
            If you speak, your audio is sent to Sahara to turn into text, then discarded. Only the
            text of the conversation is kept — so Kare can remember you next time.
          </Item>
          <Item k="ai">
            Kare is an AI assistant, not a doctor, nurse or midwife. It can be wrong. For anything
            urgent, or any decision that matters, see a health worker in person.
          </Item>
        </div>
        <button onClick={accept} disabled={!ready}
          className="btn-primary w-full py-3 disabled:opacity-40">I understand — continue</button>
      </motion.div>
    </div>
  );
};

export default ConsentGate;
