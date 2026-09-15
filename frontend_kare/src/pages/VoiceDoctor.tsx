import React, { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { useSearchParams } from 'react-router-dom';
import {
  Mic, Square, Volume2, VolumeX, Send, AlertTriangle, Stethoscope, User as UserIcon,
  Wrench, FileText, Loader2, Baby, PlayCircle, PauseCircle,
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
  const [params, setSearchParams] = useSearchParams();
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
  const replayRef = useRef<HTMLAudioElement | null>(null);
  const replayUrl = useRef<string | null>(null);
  const [replaying, setReplaying] = useState<string | null>(null); // message id: loading or playing
  const [replayingState, setReplayingState] = useState<'loading' | 'playing' | null>(null);

  useEffect(() => { if (audioRef.current) v.attachAudio(audioRef.current); }, [v.attachAudio]);
  useEffect(() => () => { if (replayUrl.current) URL.revokeObjectURL(replayUrl.current); }, []);
  useEffect(() => { v.setMuted(muted); }, [muted]); // eslint-disable-line
  useEffect(() => { if (followupId) notifications.markClicked(followupId); }, [followupId]);

  // No ?c= in the URL (i.e. arrived via the sidebar, not a Dashboard/
  // notification link) — pick up the patient's own most recent open
  // consultation instead of showing a blank panel. Kare is supposed to
  // remember you; the chat history shouldn't reset just because you
  // navigated away and came back.
  useEffect(() => {
    if (resumeConv) return;
    let cancelled = false;
    voiceApi.conversations().then((list) => {
      if (cancelled) return;
      const openConv = list.find((c) => c.status === 'active');
      if (openConv) {
        v.loadHistory(openConv.id);
        setSearchParams({ c: openConv.id }, { replace: true });
      }
    }).catch(() => {});
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [resumeConv]);
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' });
  }, [v.messages.length, v.partial, v.phase]);

  const busy = ['connecting', 'warming', 'transcribing', 'thinking'].includes(v.phase);
  const recording = v.phase === 'listening';

  const openNotes = async () => {
    try { setNotes(await voiceApi.notes()); setShowNotes(true); } catch { /* none yet */ }
  };

  const submitText = () => { if (!text.trim() || busy) return; v.sendText(text.trim()); setText(''); };

  // Re-synthesises on demand rather than caching audio from when the reply
  // first arrived — that cache would only cover the current tab's session
  // and go empty the moment a conversation is resumed from history (only
  // text is persisted server-side). One extra Sahara call per replay is a
  // small price for "always works, even on a message from last week".
  const playReply = async (m: { id: string; content: string }) => {
    if (replaying === m.id) {
      replayRef.current?.pause();
      setReplaying(null); setReplayingState(null);
      return;
    }
    replayRef.current?.pause();
    setReplaying(m.id); setReplayingState('loading');
    try {
      const blob = await voiceApi.synthesize(m.content, language);
      if (replayUrl.current) URL.revokeObjectURL(replayUrl.current);
      const url = URL.createObjectURL(blob);
      replayUrl.current = url;
      if (replayRef.current) {
        replayRef.current.src = url;
        setReplayingState('playing');
        await replayRef.current.play();
      }
    } catch {
      setReplaying(null); setReplayingState(null);
    }
  };

  return (
    <div className="flex flex-col gap-5 p-4 md:p-8 h-[calc(100vh-64px)]">
      {!consented && <ConsentGate onAccept={() => setConsented(true)} />}
      <div className="flex flex-wrap justify-between items-end gap-4">
        <div>
          <div className="text-xs font-semibold text-primary-ink/70 mb-1">AI Consultation</div>
          <h1 className="text-3xl md:text-4xl">
            {resumeConv ? 'Continuing' : 'Voice Doctor'}<span className="text-primary-ink">.</span>
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <select value={language} onChange={(e) => setLanguage(e.target.value as LangCode)}
            className="text-sm font-medium bg-surface border-2 border-ink/10 rounded-2xl px-4 py-3 outline-none focus:border-primary text-ink">
            {LANGUAGES.map((l) => <option key={l.code} value={l.code}>{l.label}</option>)}
          </select>
          <button onClick={() => setMuted(!muted)}
            className="w-12 h-12 rounded-full bg-surface border-2 border-ink/10 flex items-center justify-center text-ink/40 hover:text-primary-ink hover:border-primary transition-all">
            {muted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>
          <button onClick={openNotes}
            className="w-12 h-12 rounded-full bg-surface border-2 border-ink/10 flex items-center justify-center text-ink/40 hover:text-primary-ink hover:border-primary transition-all" title="Doctor's notes">
            <FileText size={18} />
          </button>
        </div>
      </div>

      {v.escalated && (
        <motion.div initial={{ opacity: 0, y: -8 }} animate={{ opacity: 1, y: 0 }}
          className="bg-red-600 text-white rounded-2xl px-5 py-4 flex items-center gap-3">
          <AlertTriangle size={20} className="flex-shrink-0" />
          <p className="text-sm font-semibold">This may be an emergency — follow the guidance above and get help now.</p>
        </motion.div>
      )}

      <div className="flex-1 grid lg:grid-cols-3 gap-5 min-h-0">
        <div className="lg:col-span-2 card !p-0 flex flex-col overflow-hidden min-h-0">
          <div className="flex-1 p-5 md:p-6 overflow-y-auto space-y-5 min-h-0">
            {v.messages.length === 0 && !busy && (
              <div className="h-full flex flex-col items-center justify-center text-center opacity-60">
                <div className="w-14 h-14 rounded-2xl bg-mint flex items-center justify-center mb-4">
                  <Stethoscope size={26} className="text-ink" />
                </div>
                <p className="text-sm font-medium text-ink/40 max-w-xs">
                  Speak or type how you're feeling. Kare has read your file.
                </p>
              </div>
            )}
            {v.messages.map((m) => (
              <motion.div key={m.id} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
                className={cn('flex gap-3 items-end', m.role === 'user' ? 'flex-row-reverse' : '')}>
                <div className={cn('w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center',
                  m.role === 'user' ? 'bg-primary text-primary-ink' : 'bg-mint text-ink')}>
                  {m.role === 'user' ? <UserIcon size={16} /> : <Stethoscope size={16} />}
                </div>
                <div className={cn('px-4 py-3 rounded-2xl text-sm leading-relaxed max-w-[85%]',
                  m.role === 'user' ? 'bg-primary/25 text-ink rounded-tr-sm' : 'bg-background text-ink/90 rounded-tl-sm')}>
                  {m.content}
                </div>
                {m.role === 'assistant' && (
                  <button onClick={() => playReply(m)} title="Play this reply"
                    className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-ink/30 hover:text-primary-ink hover:bg-mint/40 transition-all">
                    {replaying === m.id && replayingState === 'loading'
                      ? <Loader2 size={16} className="animate-spin" />
                      : replaying === m.id && replayingState === 'playing'
                      ? <PauseCircle size={18} />
                      : <PlayCircle size={18} />}
                  </button>
                )}
              </motion.div>
            ))}
            {v.partial && (
              <div className="flex gap-3 flex-row-reverse">
                <div className="w-9 h-9 rounded-full flex-shrink-0 flex items-center justify-center bg-primary/40 text-primary-ink"><UserIcon size={16} /></div>
                <div className="px-4 py-3 rounded-2xl border-2 border-dashed border-ink/15 text-sm text-ink/45 italic max-w-[85%]">{v.partial}</div>
              </div>
            )}
            {busy && (
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-full flex items-center justify-center bg-mint text-ink"><Stethoscope size={16} /></div>
                <div className="px-4 py-3 rounded-2xl bg-background flex items-center gap-2">
                  <Loader2 size={14} className="animate-spin text-primary-ink" />
                  <span className="text-sm font-medium text-primary-ink">{PHASE_TEXT[v.phase]}</span>
                </div>
              </div>
            )}
            {v.lastTools.length > 0 && (
              <div className="flex flex-wrap gap-2 pl-12">
                {v.lastTools.filter((t) => TOOL_LABEL[t]).map((t, i) => (
                  <span key={i} className="badge bg-sand text-ink/70">
                    <Wrench size={10} /> {TOOL_LABEL[t]}
                  </span>
                ))}
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          <div className="p-5 bg-background/60 border-t border-ink/8 flex gap-3">
            <input value={text} onChange={(e) => setText(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && submitText()}
              placeholder="Type your message…"
              className="flex-1 input-field text-sm" />
            <button onClick={submitText} disabled={busy || !text.trim()}
              className="w-12 h-12 rounded-full bg-primary text-primary-ink flex items-center justify-center hover:bg-ink hover:text-white transition-all disabled:opacity-40 flex-shrink-0">
              <Send size={18} />
            </button>
          </div>
          <div className="px-6 py-3 bg-red-600 text-white flex items-center gap-3 rounded-b-3xl">
            <AlertTriangle size={14} className="flex-shrink-0" />
            <p className="text-xs font-medium leading-tight">
              Kare is an assistant, not a replacement for a doctor. In an emergency call your local services.
            </p>
          </div>
        </div>

        <div className="flex flex-col items-center justify-center card p-8 gap-8">
          <motion.button whileTap={{ scale: 0.95 }}
            onClick={recording ? v.stopListening : v.startListening} disabled={busy}
            className={cn('w-40 h-40 rounded-full flex items-center justify-center transition-all shadow-[0_8px_30px_rgba(23,61,48,0.15)]',
              recording ? 'bg-red-600' : 'bg-primary', busy && 'opacity-40 cursor-not-allowed')}>
            {recording ? <Square size={48} className="text-white" /> : <Mic size={56} className="text-primary-ink" />}
          </motion.button>
          <div className="text-center">
            <div className="text-xl font-display font-bold text-ink">{PHASE_TEXT[v.phase]}</div>
            {user?.has_active_pregnancy && (
              <div className="mt-3 badge bg-pink text-ink mx-auto w-fit">
                <Baby size={12} /> Pregnancy mode
              </div>
            )}
          </div>
          {recording && (
            <div className="flex gap-1.5 h-10 items-center">
              {[...Array(16)].map((_, i) => (
                <motion.div key={i} animate={{ height: [8, Math.random() * 36 + 8, 8] }}
                  transition={{ duration: 0.4, repeat: Infinity, delay: i * 0.04 }} className="w-1.5 rounded-full bg-primary-ink" />
              ))}
            </div>
          )}
          {v.error && <p className="text-red-600 text-sm font-medium text-center">{v.error}</p>}
        </div>
      </div>

      <audio ref={audioRef} className="hidden" />
      <audio ref={replayRef} className="hidden"
        onEnded={() => { setReplaying(null); setReplayingState(null); }}
        onError={() => { setReplaying(null); setReplayingState(null); }} />

      <AnimatePresence>
        {showNotes && notes && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-ink/50 backdrop-blur-sm" onClick={() => setShowNotes(false)}>
            <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.95 }}
              onClick={(e) => e.stopPropagation()}
              className="w-full max-w-lg card max-h-[80vh] overflow-y-auto">
              <div className="text-xs font-semibold text-primary-ink/70 mb-1">Kare's file on you</div>
              <h2 className="text-3xl mb-6">
                Doctor's notes<span className="text-primary-ink">.</span>
              </h2>
              <p className="text-sm text-ink/40 mb-6">{notes.conversation_count} consultation(s)</p>
              {[
                ['Recurring complaints', notes.presenting_complaints],
                ['Previously considered', notes.suspected_conditions],
                ['Flags to watch', notes.important_flags],
              ].map(([label, items]: any) => items?.length > 0 && (
                <section key={label} className="mb-5">
                  <h3 className="text-xs font-semibold text-primary-ink/70 mb-2 uppercase tracking-wide">{label}</h3>
                  <ul className="space-y-1">
                    {items.map((s: string, i: number) => (
                      <li key={i} className="text-sm text-ink/60 flex gap-2"><span className="text-primary-ink">›</span> {s}</li>
                    ))}
                  </ul>
                </section>
              ))}
              {notes.key_concerns && (
                <section className="mb-2">
                  <h3 className="text-xs font-semibold text-primary-ink/70 mb-2 uppercase tracking-wide">To follow up</h3>
                  <p className="text-sm text-ink/60">{notes.key_concerns}</p>
                </section>
              )}
              {notes.last_summary && (
                <section>
                  <h3 className="text-xs font-semibold text-primary-ink/70 mb-2 uppercase tracking-wide">Last session</h3>
                  <p className="text-sm text-ink/60">{notes.last_summary}</p>
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
