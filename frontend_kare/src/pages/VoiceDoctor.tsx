import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useSearchParams } from 'react-router-dom';
import {
  Mic, Square, Volume2, VolumeX, Send, AlertTriangle, Stethoscope, User as UserIcon,
  Wrench, FileText, Loader2, Baby,
} from 'lucide-react';
import { cn } from '../lib/utils';
import { LANGUAGES, type LangCode } from '../types';
import { voice as voiceApi, notifications } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { useVoiceConsult } from '../hooks/useVoiceConsult';
import ConsentGate, { hasConsented } from '../components/ConsentGate';

const TOOL_LABEL: Record<string, string> = {
  check_drug_interactions: 'Checked drug interactions',
  get_patient_history: 'Reviewed your file',
  score_triage: 'Assessed urgency',
  update_health_record: 'Updated your record',
  plan_followup: 'Scheduled a check-in',
  search_medical_literature: 'Looked up guidance',
  flag_for_escalation: 'Flagged as urgent',
};

const PHASE_TEXT: Record<string, string> = {
  idle: 'Tap to start', connecting: 'Connecting…', warming: 'Warming up the voice model…',
  ready: 'Tap to speak', listening: 'Listening…', transcribing: 'Got it…',
  thinking: 'Thinking…', speaking: 'Speaking…',
};

const VoiceDoctor = () => {
  const user = useAuthStore((s) => s.user);
  const [params] = useSearchParams();
  const resumeConv = params.get('c');
  const followupId = params.get('f');

  const [language, setLanguage] = useState<LangCode>((user?.preferred_language as LangCode) || 'en');
  const [muted, setMuted] = useState(false);
  const [text, setText] = useState('');
  const [showNotes, setShowNotes] = useState(false);
  const [notes, setNotes] = useState<any>(null);
  const [consented, setConsented] = useState(hasConsented);

  const v = useVoiceConsult(language, resumeConv);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const bottomRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => { if (audioRef.current) v.attachAudio(audioRef.current); }, [v.attachAudio]);
  useEffect(() => { v.setMuted(muted); }, [muted]); // eslint-disable-line
  useEffect(() => { if (followupId) notifications.markClicked(followupId); }, [followupId]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [v.messages.length, v.partial, v.phase]);

  const busy = ['connecting', 'warming', 'transcribing', 'thinking'].includes(v.phase);
  const recording = v.phase === 'listening';

  const openNotes = async () => {
    try { setNotes(await voiceApi.notes()); setShowNotes(true); } catch { /* none yet */ }
  };

  const submitText = () => { if (!text.trim() || busy) return; v.sendText(text.trim()); setText(''); };

  return (
    <div className="flex flex-col gap-5 p-4 md:p-8 h-[calc(100vh-64px)]">
      {!consented && <ConsentGate onAccept={() => setConsented(true)} />}
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-1">AI Consultation</div>
          <h1 className="text-3xl md:text-4xl font-display font-bold tracking-tighter uppercase">
            {resumeConv ? 'Continuing' : 'Voice Doctor'}<span className="text-primary">.</span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <select value={language} onChange={(e) => setLanguage(e.target.value as LangCode)}
            className="text-[10px] font-bold uppercase tracking-widest bg-surface border-2 border-white/10 px-4 py-3 outline-none focus:border-primary text-white">
            {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
          <button onClick={() => setMuted(!muted)}
            className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all">
            {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
          <button onClick={openNotes}
            className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all" title="Doctor's notes">
            <FileText size={18} />
          </button>
        </div>
      </div>

      {v.escalated && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="bg-red-500 text-black px-5 py-3 flex items-center gap-3 border-2 border-black">
          <AlertTriangle size={20} className="flex-shrink-0" />
          <p className="text-[11px] font-bold uppercase tracking-widest">This may be an emergency — follow the guidance above and get help now.</p>
        </motion.div>
      )}

      <div className="flex-1 grid lg:grid-cols-3 gap-5 min-h-0">
        <div className="lg:col-span-2 brutalist-card bg-surface border-2 border-white/10 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 p-5 md:p-6 overflow-y-auto space-y-5 min-h-0">
            {v.messages.length === 0 && !busy && (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-60">
                <Stethoscope size={40} className="text-primary mb-4" />
                <p className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/40 max-w-xs">
                  Speak or type how you're feeling. Kare has read your file.
                </p>
              </div>
            )}
            {v.messages.map((m) => (
              <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className={cn('flex gap-4', m.role === 'user' ? 'flex-row-reverse' : '')}>
                <div className={cn('w-10 h-10 flex-shrink-0 flex items-center justify-center border-2',
                  m.role === 'user' ? 'bg-primary border-black text-black' : 'bg-black border-primary text-primary')}>
                  {m.role === 'user' ? <UserIcon size={18} /> : <Stethoscope size={18} />}
                </div>
                <div className={cn('px-4 py-3 border-2 text-sm leading-relaxed max-w-[85%]',
                  m.role === 'user' ? 'bg-white text-black border-white' : 'bg-black border-white/10 text-white/90')}>
                  {m.content}
                </div>
              </motion.div>
            ))}
            {v.partial && (
              <div className="flex gap-4 flex-row-reverse">
                <div className="w-10 h-10 flex-shrink-0 flex items-center justify-center border-2 bg-primary/40 border-black text-black"><UserIcon size={18} /></div>
                <div className="px-4 py-3 border-2 border-dashed border-white/20 text-sm text-white/50 italic max-w-[85%]">{v.partial}</div>
              </div>
            )}
            {busy && (
              <div className="flex gap-4">
                <div className="w-10 h-10 flex items-center justify-center border-2 bg-black border-primary text-primary"><Stethoscope size={18} /></div>
                <div className="px-4 py-3 border-2 border-white/10 bg-black flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-primary" />
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary">{PHASE_TEXT[v.phase]}</span>
                </div>
              </div>
            )}
            {v.lastTools.length > 0 && (
              <div className="flex flex-wrap gap-2 pl-14">
                {v.lastTools.filter((t) => TOOL_LABEL[t]).map((t, i) => (
                  <span key={i} className="text-[9px] font-bold uppercase tracking-widest text-primary/70 border border-primary/30 px-2 py-1 flex items-center gap-1.5">
                    <Wrench size={10} /> {TOOL_LABEL[t]}
                  </span>
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="p-5 bg-black/40 border-t-2 border-white/10 flex gap-3">
            <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submitText()}
              placeholder="Type your message…" style={{ textTransform: 'none' }}
              className="flex-1 bg-black border-2 border-white/10 px-4 py-3 outline-none focus:border-primary text-sm text-white placeholder:text-white/20" />
            <button onClick={submitText} disabled={busy || !text.trim()}
              className="w-12 h-12 bg-primary text-black flex items-center justify-center border-2 border-black hover:bg-white transition-all disabled:opacity-40">
              <Send size={18} />
            </button>
          </div>
          <div className="px-6 py-3 bg-red-500/90 text-black flex items-center gap-3">
            <AlertTriangle size={14} className="flex-shrink-0" />
            <p className="text-[9px] font-bold uppercase tracking-[0.15em] leading-tight">
              Kare is an assistant, not a replacement for a doctor. In an emergency call your local services.
            </p>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center brutalist-card bg-surface border-2 border-white/10 p-8 gap-8">
          <motion.button whileTap={{ scale: 0.95 }}
            onClick={recording ? v.stopListening : v.startListening} disabled={busy}
            className={cn('w-44 h-44 flex items-center justify-center border-8 border-black transition-all shadow-[10px_10px_0px_0px_rgba(0,0,0,0.3)]',
              recording ? 'bg-red-500' : 'bg-primary', busy && 'opacity-40 cursor-not-allowed')}>
            {recording ? <Square size={56} className="text-black" /> : <Mic size={64} className="text-black" />}
          </motion.button>
          <div className="text-center">
            <div className="text-2xl font-display font-bold uppercase tracking-tighter">{PHASE_TEXT[v.phase]}</div>
            {user?.has_active_pregnancy && (
              <div className="mt-3 text-[10px] font-bold uppercase tracking-widest text-primary flex items-center justify-center gap-2">
                <Baby size={12} /> Pregnancy mode
              </div>
            )}
          </div>
          {recording && (
            <div className="flex gap-1.5 h-10 items-center">
              {[...Array(16)].map((_, i) => (
                <motion.div key={i} animate={{ height: [8, Math.random() * 36 + 8, 8] }}
                  transition={{ duration: 0.4, repeat: Infinity, delay: i * 0.04 }} className="w-1.5 bg-primary" />
              ))}
            </div>
          )}
          {v.error && <p className="text-red-500 text-[10px] font-bold uppercase tracking-widest text-center">{v.error}</p>}
        </div>
      </div>

      <audio ref={audioRef} className="hidden" />

      <AnimatePresence>
        {showNotes && notes && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm" onClick={() => setShowNotes(false)}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg bg-surface border-4 border-white/10 p-8 max-h-[80vh] overflow-y-auto">
              <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary mb-1">Kare's file on you</div>
              <h2 className="text-3xl font-display font-bold uppercase tracking-tighter mb-6">
                Doctor's Notes<span className="text-primary">.</span>
              </h2>
              <p className="text-[10px] uppercase tracking-widest text-white/40 mb-6">{notes.conversation_count} consultation(s)</p>
              {[
                ['Recurring complaints', notes.presenting_complaints],
                ['Previously considered', notes.suspected_conditions],
                ['Flags to watch', notes.important_flags],
              ].map(([label, items]: any) => items?.length > 0 && (
                <section key={label} className="mb-5">
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">{label}</h3>
                  <ul className="space-y-1">
                    {items.map((s: string, i: number) => (
                      <li key={i} className="text-xs text-white/60 flex gap-2"><span className="text-primary">›</span> {s}</li>
                    ))}
                  </ul>
                </section>
              ))}
              {notes.key_concerns && (
                <section className="mb-2">
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">To follow up</h3>
                  <p className="text-xs text-white/60">{notes.key_concerns}</p>
                </section>
              )}
              {notes.last_summary && (
                <section>
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Last session</h3>
                  <p className="text-xs text-white/60">{notes.last_summary}</p>
                </section>
              )}
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VoiceDoctor;
