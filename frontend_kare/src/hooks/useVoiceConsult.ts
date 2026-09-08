import { useCallback, useEffect, useRef, useState } from 'react';
import { WS_BASE_URL, voice } from '../services/api';
import { useAuthStore } from '../store/useAuthStore';
import { AudioQueue, MicRecorder } from '../lib/audio';
import type { LangCode, Message } from '../types';

type Phase = 'idle' | 'connecting' | 'warming' | 'ready' | 'listening' | 'transcribing' | 'thinking' | 'speaking';

interface State {
  phase: Phase;
  messages: Message[];
  partial: string;
  conversationId: string | null;
  lastTools: string[];
  escalated: boolean;
  error: string | null;
}

export function useVoiceConsult(language: LangCode, initialConversationId?: string | null) {
  const token = useAuthStore((s) => s.accessToken);
  const [state, setState] = useState<State>({
    phase: 'idle', messages: [], partial: '', conversationId: initialConversationId ?? null,
    lastTools: [], escalated: false, error: null,
  });
  const set = (p: Partial<State>) => setState((s) => ({ ...s, ...p }));

  const ws = useRef<WebSocket | null>(null);
  const mic = useRef<MicRecorder | null>(null);
  const audioEl = useRef<HTMLAudioElement | null>(null);
  const audioQ = useRef<AudioQueue | null>(null);
  const muted = useRef(false);

  const setMuted = (m: boolean) => { muted.current = m; if (m) audioQ.current?.clear(); };

  const attachAudio = useCallback((el: HTMLAudioElement) => {
    audioEl.current = el;
    audioQ.current = new AudioQueue(el);
    audioQ.current.onDone = () => setState((s) => (s.phase === 'speaking' ? { ...s, phase: 'ready' } : s));
  }, []);

  const loadHistory = useCallback(async (id: string) => {
    try {
      const data = await voice.messages(id);
      set({ messages: data.messages, conversationId: id });
    } catch { /* new conversation */ }
  }, []);

  useEffect(() => {
    if (initialConversationId) loadHistory(initialConversationId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialConversationId]);

  const openStream = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    set({ phase: 'connecting', error: null });
    const sock = new WebSocket(`${WS_BASE_URL}/voice/stream`);
    sock.binaryType = 'arraybuffer';
    ws.current = sock;

    sock.onopen = () => {
      sock.send(JSON.stringify({ type: 'auth', token }));
      sock.send(JSON.stringify({ type: 'start', language, conversation_id: state.conversationId }));
    };
    sock.onmessage = (ev) => {
      if (ev.data instanceof ArrayBuffer) {
        if (!muted.current) audioQ.current?.push(ev.data);
        return;
      }
      const m = JSON.parse(ev.data);
      switch (m.type) {
        case 'warming': set({ phase: 'warming' }); break;
        case 'ready': set({ phase: 'ready' }); break;
        case 'partial': set({ partial: m.text }); break;
        case 'final':
          setState((s) => ({
            ...s, partial: '',
            messages: [...s.messages, { id: crypto.randomUUID(), role: 'user', content: m.text, created_at: new Date().toISOString() }],
          }));
          break;
        case 'thinking': set({ phase: 'thinking' }); break;
        case 'reply':
          setState((s) => ({
            ...s, phase: muted.current ? 'ready' : 'speaking',
            conversationId: m.conversation_id, lastTools: m.tool_calls || [], escalated: !!m.escalated,
            messages: [...s.messages, { id: crypto.randomUUID(), role: 'assistant', content: m.text, created_at: new Date().toISOString() }],
          }));
          break;
        case 'turn_complete': set({ conversationId: m.conversation_id }); break;
        case 'error': set({ error: m.detail, phase: 'ready' }); break;
      }
    };
    sock.onerror = () => set({ error: 'Connection error', phase: 'idle' });
    sock.onclose = () => { ws.current = null; setState((s) => (s.phase === 'connecting' ? { ...s, phase: 'idle' } : s)); };
  }, [token, language, state.conversationId]);

  const startListening = useCallback(async () => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      openStream();
      await new Promise((r) => setTimeout(r, 400));
    }
    audioQ.current?.clear();
    try {
      mic.current = new MicRecorder((pcm) => {
        if (ws.current?.readyState === WebSocket.OPEN) ws.current.send(pcm);
      });
      await mic.current.start();
      set({ phase: 'listening', partial: '' });
    } catch {
      set({ error: 'Microphone access denied' });
    }
  }, [openStream]);

  const stopListening = useCallback(() => {
    mic.current?.stop();
    mic.current = null;
    ws.current?.send(JSON.stringify({ type: 'end_turn' }));
    set({ phase: 'transcribing' });
  }, []);

  const sendText = useCallback(async (text: string) => {
    if (!text.trim()) return;
    setState((s) => ({
      ...s, phase: 'thinking',
      messages: [...s.messages, { id: crypto.randomUUID(), role: 'user', content: text, created_at: new Date().toISOString() }],
    }));
    try {
      const r = await voice.chat({ text, language, conversation_id: state.conversationId, include_audio: !muted.current });
      setState((s) => ({
        ...s, phase: 'ready', conversationId: r.conversation_id, lastTools: r.tool_calls || [], escalated: !!r.escalated,
        messages: [...s.messages, { id: crypto.randomUUID(), role: 'assistant', content: r.assistant_message, created_at: new Date().toISOString() }],
      }));
      if (r.audio_base64 && !muted.current) {
        const bytes = Uint8Array.from(atob(r.audio_base64), (c) => c.charCodeAt(0));
        audioQ.current?.push(bytes.buffer);
        set({ phase: 'speaking' });
      }
    } catch (e: any) {
      set({ phase: 'ready', error: e?.response?.data?.detail || 'The assistant is unavailable right now.' });
    }
  }, [language, state.conversationId]);

  const end = useCallback(() => {
    mic.current?.stop();
    ws.current?.close();
    ws.current = null;
    if (state.conversationId) voice.end(state.conversationId).catch(() => {});
  }, [state.conversationId]);

  useEffect(() => () => { mic.current?.stop(); ws.current?.close(); }, []);

  return { ...state, attachAudio, openStream, startListening, stopListening, sendText, end, setMuted, loadHistory };
}
