import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Mic, 
  Square, 
  Volume2, 
  VolumeX, 
  Send, 
  ChevronLeft,
  Languages,
  AlertCircle,
  User,
  Plus,
  Stethoscope,
  ArrowRight,
  Loader2,
  FileText
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../lib/utils';
import { Message, ClinicalNotes } from '../types';
import { api } from '../services/api';

const VoiceDoctor = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [language, setLanguage] = useState('en');
  const [isMuted, setIsMuted] = useState(false);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [clinicalNotes, setClinicalNotes] = useState<ClinicalNotes | null>(null);
  const [showNotes, setShowNotes] = useState(false);
  const [textInput, setTextInput] = useState('');
  
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  useEffect(() => {
    const startNewConversation = async () => {
      try {
        const response = await api.post('/consultations/start');
        setConversationId(response.data.conversation_id);
      } catch (error) {
        console.error('Error starting conversation:', error);
      }
    };

    startNewConversation();
  }, []);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const fetchClinicalNotes = async () => {
    if (!conversationId) return;
    try {
      const response = await api.get(`/consultations/${conversationId}/notes`);
      setClinicalNotes(response.data);
      setShowNotes(true);
    } catch (error) {
      console.error('Error fetching clinical notes:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder.current = new MediaRecorder(stream);
      audioChunks.current = [];

      mediaRecorder.current.ondataavailable = (event) => {
        audioChunks.current.push(event.data);
      };

      mediaRecorder.current.onstop = async () => {
        const audioBlob = new Blob(audioChunks.current, { type: 'audio/wav' });
        await sendMessage(null, audioBlob);
      };

      mediaRecorder.current.start();
      setIsRecording(true);
    } catch (err) {
      console.error("Error accessing microphone:", err);
    }
  };

  const stopRecording = () => {
    if (mediaRecorder.current && isRecording) {
      mediaRecorder.current.stop();
      setIsRecording(false);
      setIsProcessing(true);
    }
  };

  const sendMessage = async (text: string | null, audioBlob: Blob | null = null) => {
    if (!conversationId) return;
    
    setIsProcessing(true);
    try {
      const formData = new FormData();
      if (text) formData.append('message', text);
      if (audioBlob) formData.append('audio', audioBlob, 'voice.wav');
      formData.append('language', language);

      const response = await api.post(`/consultations/${conversationId}/message`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });

      const { user_message, assistant_message } = response.data;
      
      setMessages(prev => [...prev, user_message, assistant_message]);
      
      if (assistant_message.audio_url && !isMuted) {
        playAudio(assistant_message.audio_url);
      }
    } catch (err) {
      console.error("Error sending message:", err);
    } finally {
      setIsProcessing(false);
      setTextInput('');
    }
  };

  const playAudio = (url: string) => {
    if (audioRef.current) {
      audioRef.current.src = url;
      audioRef.current.play();
    }
  };

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
      className="h-[calc(100vh-140px)] flex flex-col gap-8 p-8"
    >
      <div className="flex justify-between items-end">
        <div className="flex items-center gap-6">
          <Link to="/" className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all group">
            <ChevronLeft size={24} className="group-hover:-translate-x-1 transition-transform" />
          </Link>
          <motion.div variants={itemVariants}>
            <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-1">AI Medical Assistant</div>
            <h1 className="text-4xl font-display font-bold tracking-tighter uppercase">Voice Consultation<span className="text-primary">.</span></h1>
          </motion.div>
        </div>

        <motion.div variants={itemVariants} className="flex items-center gap-4">
          <div className="flex items-center gap-3 border-2 border-white/10 px-6 py-3 bg-surface group focus-within:border-primary transition-all">
            <Languages size={16} className="text-primary" />
            <select 
              value={language} 
              onChange={(e) => setLanguage(e.target.value)}
              className="text-[10px] font-bold uppercase tracking-widest bg-transparent border-none outline-none text-white cursor-pointer"
            >
              <option value="en">English</option>
              <option value="yo">Yoruba</option>
              <option value="ha">Hausa</option>
              <option value="ig">Igbo</option>
            </select>
          </div>
          <button 
            onClick={() => setIsMuted(!isMuted)}
            className="w-14 h-14 border-2 border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all group"
          >
            {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} className="group-hover:scale-110 transition-transform" />}
          </button>
        </motion.div>
      </div>

      <div className="flex-1 grid grid-cols-12 gap-8 min-h-0">
        {/* Chat Area */}
        <motion.div variants={itemVariants} className="col-span-8 brutalist-card flex flex-col overflow-hidden bg-surface border-2 border-white/10">
          <div ref={scrollRef} className="flex-1 p-12 overflow-y-auto space-y-10 scroll-smooth">
            {messages.length === 0 && !isProcessing && !isRecording && (
              <div className="h-full flex flex-col items-center justify-center text-center">
                <motion.div 
                  animate={{ scale: [1, 1.1, 1], opacity: [0.5, 1, 0.5] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="w-32 h-32 border-4 border-primary flex items-center justify-center text-primary mb-10"
                >
                  <Mic size={56} />
                </motion.div>
                <h2 className="text-4xl font-display font-bold uppercase tracking-tight mb-4">Start Consultation</h2>
                <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.3em] max-w-xs leading-relaxed">
                  Tap the microphone to describe your symptoms or type your message below.
                </p>
              </div>
            )}

            {messages.map((msg) => (
              <motion.div 
                key={msg.id}
                initial={{ opacity: 0, x: msg.role === 'user' ? 20 : -20 }}
                animate={{ opacity: 1, x: 0 }}
                className={cn(
                  "flex gap-8 max-w-[85%]",
                  msg.role === 'user' ? "ml-auto flex-row-reverse text-right" : ""
                )}
              >
                <div className={cn(
                  "w-16 h-16 flex-shrink-0 flex items-center justify-center border-4",
                  msg.role === 'user' ? "bg-primary border-black text-black" : "bg-black border-primary text-primary"
                )}>
                  {msg.role === 'user' ? <User size={28} /> : <Stethoscope size={28} />}
                </div>
                <div className={cn(
                  "p-10 border-2 text-sm font-bold uppercase tracking-tight leading-relaxed shadow-[8px_8px_0px_0px_rgba(0,0,0,0.2)]",
                  msg.role === 'user' 
                    ? "bg-white text-black border-white" 
                    : "bg-black border-white/10 text-white"
                )}>
                  {msg.content}
                </div>
              </motion.div>
            ))}

            {isProcessing && (
              <div className="flex gap-8 max-w-[85%]">
                <div className="w-16 h-16 bg-black border-4 border-primary text-primary flex items-center justify-center">
                  <Stethoscope size={28} />
                </div>
                <div className="bg-black border-2 border-white/10 p-10 flex gap-3 items-center">
                  {[0, 1, 2].map(i => (
                    <motion.div
                      key={i}
                      animate={{ scale: [1, 1.5, 1], opacity: [0.3, 1, 0.3] }}
                      transition={{ duration: 0.6, repeat: Infinity, delay: i * 0.2 }}
                      className="w-2.5 h-2.5 bg-primary"
                    />
                  ))}
                  <span className="text-[10px] font-bold uppercase tracking-widest text-primary ml-4">Analyzing Signal...</span>
                </div>
              </div>
            )}
          </div>

          {/* Text Input Area */}
          <div className="p-8 bg-black/40 border-t-2 border-white/10 flex gap-6">
            <input 
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage(textInput)}
              placeholder="Type your message..."
              className="flex-1 bg-black border-2 border-white/10 px-8 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white placeholder:text-white/20"
            />
            <button 
              onClick={() => sendMessage(textInput)}
              disabled={isProcessing || !textInput.trim()}
              className="w-16 h-16 bg-primary text-black flex items-center justify-center border-4 border-black shadow-[4px_4px_0px_0px_rgba(255,255,255,0.1)] hover:bg-white transition-all disabled:opacity-50"
            >
              <Send size={24} />
            </button>
          </div>

          {/* Disclaimer */}
          <div className="px-12 py-6 bg-red-500 text-black flex items-center gap-6 border-t-4 border-black">
            <AlertCircle size={24} className="flex-shrink-0 animate-pulse" />
            <p className="text-[10px] font-bold uppercase tracking-[0.2em] leading-tight">
              DISCLAIMER: Kare AI is an assistant, not a replacement for professional medical advice. 
              In case of emergency, please call your local emergency services immediately.
            </p>
          </div>
        </motion.div>

        {/* Voice Visualization Area */}
        <div className="col-span-4 flex flex-col gap-8">
          <motion.div 
            variants={itemVariants}
            className="brutalist-card flex-1 flex flex-col items-center justify-center p-12 bg-surface relative overflow-hidden group border-2 border-white/10"
          >
            <div className="absolute inset-0 bg-primary/5 pointer-events-none group-hover:bg-primary/10 transition-all"></div>
            
            <div className="relative z-10 flex flex-col items-center w-full">
              <div className="w-72 h-72 relative flex items-center justify-center mb-16">
                <AnimatePresence>
                  {isRecording && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1.3 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      transition={{ duration: 0.3 }}
                      className="absolute inset-0 border-8 border-primary/20"
                    />
                  )}
                </AnimatePresence>
                
                <motion.button 
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={isProcessing}
                  className={cn(
                    "w-56 h-56 flex items-center justify-center text-black transition-all duration-300 relative z-10 border-8 shadow-[12px_12px_0px_0px_rgba(0,0,0,0.3)]",
                    isRecording ? "bg-red-500 border-black" : "bg-primary border-black",
                    isProcessing && "opacity-50 cursor-not-allowed"
                  )}
                >
                  {isRecording ? <Square size={72} /> : <Mic size={88} />}
                </motion.button>
              </div>

              <div className="text-center">
                <h3 className="text-4xl font-display font-bold uppercase tracking-tighter mb-4">
                  {isRecording ? "Listening" : isProcessing ? "Analyzing" : "Tap to Speak"}
                </h3>
                <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/20">
                  {isRecording ? "Describe how you're feeling" : "Start a voice consultation"}
                </div>
              </div>

              {isRecording && (
                <div className="flex gap-3 mt-16 h-16 items-center">
                  {[...Array(20)].map((_, i) => (
                    <motion.div
                      key={i}
                      animate={{ height: [16, Math.random() * 64 + 16, 16] }}
                      transition={{ duration: 0.4, repeat: Infinity, delay: i * 0.03 }}
                      className="w-2 bg-primary"
                    />
                  ))}
                </div>
              )}
            </div>
          </motion.div>

          <motion.div variants={itemVariants} className="brutalist-card p-10 bg-surface border-2 border-white/10">
            <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-white/20 mb-8">Clinical Summary</div>
            <div className="grid grid-cols-1 gap-6">
              <button 
                onClick={fetchClinicalNotes}
                className="p-8 border-2 border-white/10 text-[10px] font-bold uppercase tracking-widest text-white/40 hover:bg-primary hover:text-black hover:border-primary transition-all flex flex-col items-center gap-6 group"
              >
                <FileText size={28} className="group-hover:scale-110 transition-transform" /> Generate Notes
              </button>
            </div>
          </motion.div>
        </div>
      </div>

      <audio ref={audioRef} className="hidden" />

      {/* Clinical Notes Modal */}
      <AnimatePresence>
        {showNotes && clinicalNotes && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="w-full max-w-2xl bg-surface border-4 border-white/10 p-12 brutalist-card max-h-[80vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start mb-12">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary mb-2">Clinical Summary</div>
                  <h2 className="text-4xl font-display font-bold uppercase tracking-tighter">Doctor's Notes<span className="text-primary">.</span></h2>
                </div>
                <button 
                  onClick={() => setShowNotes(false)}
                  className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/20 hover:text-primary hover:border-primary transition-all"
                >
                  <Plus size={24} className="rotate-45" />
                </button>
              </div>

              <div className="space-y-10">
                <section>
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-4">Summary</h3>
                  <p className="text-sm font-bold uppercase tracking-widest text-white/60 leading-relaxed">{clinicalNotes.summary}</p>
                </section>

                <div className="grid md:grid-cols-2 gap-10">
                  <section>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-4">Symptoms</h3>
                    <ul className="space-y-3">
                      {clinicalNotes.symptoms.map((s, i) => (
                        <li key={i} className="text-[10px] font-bold uppercase tracking-widest text-white/40 flex items-center gap-3">
                          <span className="w-1.5 h-1.5 bg-primary"></span> {s}
                        </li>
                      ))}
                    </ul>
                  </section>
                  <section>
                    <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-4">Diagnosis</h3>
                    <ul className="space-y-3">
                      {clinicalNotes.potential_diagnosis.map((d, i) => (
                        <li key={i} className="text-[10px] font-bold uppercase tracking-widest text-white/40 flex items-center gap-3">
                          <span className="w-1.5 h-1.5 bg-primary"></span> {d}
                        </li>
                      ))}
                    </ul>
                  </section>
                </div>

                <section>
                  <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-4">Plan</h3>
                  <ul className="space-y-3">
                    {clinicalNotes.plan.map((p, i) => (
                      <li key={i} className="text-[10px] font-bold uppercase tracking-widest text-white/40 flex items-center gap-3">
                        <ArrowRight size={12} className="text-primary" /> {p}
                      </li>
                    ))}
                  </ul>
                </section>

                <div className="pt-10 border-t-2 border-white/5 flex justify-between items-center">
                  <div className="text-[8px] font-bold uppercase tracking-[0.5em] text-white/10 italic">Consultation ID: {conversationId}</div>
                  <button className="btn-primary py-4 px-10">Save to History</button>
                </div>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </motion.div>
  );
};

export default VoiceDoctor;
