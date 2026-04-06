import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  History, 
  FileText, 
  Download, 
  Search,
  ChevronRight,
  Calendar,
  ArrowRight,
  Filter,
  Plus,
  Trash2,
  X,
  Save,
  Loader2
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { MedicalCondition } from '../types';

const MedicalHistory = () => {
  const [conditions, setConditions] = useState<MedicalCondition[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newCondition, setNewCondition] = useState({
    name: '',
    date_diagnosed: new Date().toISOString().split('T')[0],
    status: 'Active',
    notes: '',
    icd10_code: ''
  });

  useEffect(() => {
    const fetchConditions = async () => {
      try {
        setIsLoading(true);
        const response = await api.get('/medical-history');
        setConditions(response.data);
      } catch (error) {
        console.error('Error fetching medical history:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchConditions();
  }, []);

  const handleDeleteCondition = async (id: string) => {
    try {
      await api.delete(`/medical-history/${id}`);
      setConditions(conditions.filter(c => c.id !== id));
    } catch (error) {
      console.error('Error deleting condition:', error);
    }
  };

  const handleAddCondition = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await api.post('/medical-history', newCondition);
      setConditions([response.data, ...conditions]);
      setShowAddModal(false);
      setNewCondition({
        name: '',
        date_diagnosed: new Date().toISOString().split('T')[0],
        status: 'Active',
        notes: '',
        icd10_code: ''
      });
    } catch (error) {
      console.error('Error adding condition:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredConditions = conditions.filter(c => 
    c.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.notes?.toLowerCase().includes(searchQuery.toLowerCase())
  );

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
      <div className="flex justify-between items-end">
        <motion.div variants={itemVariants}>
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Patient Archives</div>
          <h1 className="text-5xl font-display font-bold tracking-tighter uppercase">Medical History<span className="text-primary">.</span></h1>
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Access your past records, lab results, and consultations.</p>
        </motion.div>
        <motion.button 
          variants={itemVariants}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          className="px-10 py-5 border-4 border-white/10 text-white font-bold uppercase tracking-[0.2em] flex items-center gap-4 hover:bg-white hover:text-black hover:border-white transition-all group"
        >
          <Download size={24} className="group-hover:-translate-y-1 transition-transform" /> Export All
        </motion.button>
      </div>

      <motion.div variants={itemVariants} className="brutalist-card p-10 bg-surface border-2 border-white/10 flex gap-6 items-center">
        <div className="relative flex-1 group">
          <Search className="absolute left-6 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-primary transition-colors" size={20} />
          <input 
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search conditions, notes, or dates..."
            className="w-full pl-16 pr-6 py-6 bg-black border-2 border-white/10 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white placeholder:text-white/20"
          />
        </div>
        <button 
          onClick={() => setShowAddModal(true)}
          className="w-20 h-20 border-2 border-white/10 flex items-center justify-center text-white/40 hover:text-primary hover:border-primary transition-all group"
        >
          <Plus size={24} className="group-hover:rotate-90 transition-transform" />
        </button>
      </motion.div>

      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-8 bg-black/80 backdrop-blur-sm">
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="w-full max-w-xl bg-surface border-4 border-white/10 p-12 brutalist-card"
            >
              <div className="flex justify-between items-start mb-12">
                <div>
                  <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary mb-2">New Entry</div>
                  <h2 className="text-4xl font-display font-bold uppercase tracking-tighter">Add Condition<span className="text-primary">.</span></h2>
                </div>
                <button 
                  onClick={() => setShowAddModal(false)}
                  className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/20 hover:text-primary hover:border-primary transition-all"
                >
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleAddCondition} className="space-y-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Condition Name</label>
                  <input 
                    required
                    type="text"
                    value={newCondition.name}
                    onChange={(e) => setNewCondition({...newCondition, name: e.target.value})}
                    className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Diagnosis Date</label>
                    <input 
                      required
                      type="date"
                      value={newCondition.date_diagnosed}
                      onChange={(e) => setNewCondition({...newCondition, date_diagnosed: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Status</label>
                    <select 
                      value={newCondition.status}
                      onChange={(e) => setNewCondition({...newCondition, status: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    >
                      <option value="Active">Active</option>
                      <option value="Recovered">Recovered</option>
                      <option value="Chronic">Chronic</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">ICD-10 Code (Optional)</label>
                  <input 
                    type="text"
                    value={newCondition.icd10_code}
                    onChange={(e) => setNewCondition({...newCondition, icd10_code: e.target.value})}
                    className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                  />
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Clinical Notes</label>
                  <textarea 
                    rows={4}
                    value={newCondition.notes}
                    onChange={(e) => setNewCondition({...newCondition, notes: e.target.value})}
                    className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white resize-none"
                  />
                </div>

                <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-6 bg-primary text-black font-bold uppercase tracking-[0.3em] flex items-center justify-center gap-4 hover:bg-white transition-all border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" /> : <Save size={20} />}
                  Save Condition
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div className="space-y-10">
        <motion.h2 variants={itemVariants} className="text-[10px] font-bold text-white/20 uppercase tracking-[0.4em] px-4">
          {isLoading ? 'Loading Records...' : `Medical Conditions (${filteredConditions.length})`}
        </motion.h2>
        <div className="grid gap-8">
          {filteredConditions.map((record) => (
            <motion.div
              key={record.id}
              variants={itemVariants}
              whileHover={{ x: 10 }}
              className="brutalist-card p-10 bg-surface border-2 border-white/10 flex items-center justify-between hover:bg-black hover:border-primary transition-all group cursor-pointer relative overflow-hidden"
            >
              <div className="absolute top-0 left-0 w-1 h-full bg-primary/20 group-hover:bg-primary transition-all"></div>
              <div className="flex items-center gap-10">
                <div className={cn("w-24 h-24 border-2 border-white/10 flex items-center justify-center text-primary group-hover:border-primary group-hover:bg-primary/10 transition-all")}>
                  <FileText size={40} className="group-hover:scale-110 transition-transform" />
                </div>
                <div>
                  <div className="flex items-center gap-4 mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Condition</span>
                    <span className="w-2 h-2 bg-white/10"></span>
                    <span className="text-[10px] font-bold text-primary uppercase tracking-[0.3em]">{record.status}</span>
                  </div>
                  <h3 className="text-3xl font-display font-bold uppercase tracking-tight mb-4 group-hover:text-primary transition-all">{record.name}</h3>
                  <div className="flex items-center gap-10">
                    <div className="flex items-center gap-3 text-[10px] text-white/20 font-bold uppercase tracking-[0.2em]">
                      <Calendar size={16} className="text-primary" /> Diagnosed: {new Date(record.date_diagnosed).toLocaleDateString()}
                    </div>
                    {record.icd10_code && (
                      <div className="flex items-center gap-3 text-[10px] text-white/20 font-bold uppercase tracking-[0.2em]">
                        <History size={16} className="text-primary" /> ICD-10: {record.icd10_code}
                      </div>
                    )}
                  </div>
                  {record.notes && (
                    <p className="mt-4 text-[10px] text-white/40 font-bold uppercase tracking-widest leading-relaxed max-w-xl">
                      Notes: {record.notes}
                    </p>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-10">
                <motion.button 
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteCondition(record.id);
                  }}
                  className="w-14 h-14 border-2 border-white/10 flex items-center justify-center text-white/20 hover:text-red-500 hover:border-red-500 transition-all group/dl"
                >
                  <Trash2 size={24} className="group-hover/dl:scale-110 transition-transform" />
                </motion.button>
                <div className="w-14 h-14 border-2 border-white/10 flex items-center justify-center text-white/10 group-hover:text-primary group-hover:border-primary transition-all">
                  <ArrowRight size={28} className="group-hover:translate-x-1 transition-transform" />
                </div>
              </div>
            </motion.div>
          ))}
          {!isLoading && filteredConditions.length === 0 && (
            <div className="text-center py-20 border-2 border-dashed border-white/10">
              <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">No records found</p>
            </div>
          )}
        </div>
      </div>
    </motion.div>
  );
};

export default MedicalHistory;
