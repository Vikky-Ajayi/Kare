import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Pill, 
  Plus, 
  Clock, 
  Calendar,
  ChevronRight,
  AlertCircle,
  ArrowRight,
  Trash2,
  Search,
  X,
  Save,
  Loader2
} from 'lucide-react';
import { cn } from '../lib/utils';
import { api } from '../services/api';
import { Medication } from '../types';

const Medications = () => {
  const [medications, setMedications] = useState<Medication[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [newMedication, setNewMedication] = useState({
    drug_name: '',
    dosage: '',
    frequency: '',
    start_date: new Date().toISOString().split('T')[0],
    end_date: '',
    notes: ''
  });

  useEffect(() => {
    const fetchMedications = async () => {
      try {
        setIsLoading(true);
        const response = await api.get('/medications');
        setMedications(response.data);
      } catch (error) {
        console.error('Error fetching medications:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchMedications();
  }, []);

  const handleDeleteMedication = async (id: string) => {
    try {
      await api.delete(`/medications/${id}`);
      setMedications(medications.filter(m => m.id !== id));
    } catch (error) {
      console.error('Error deleting medication:', error);
    }
  };

  const handleAddMedication = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    try {
      const response = await api.post('/medications', newMedication);
      setMedications([response.data, ...medications]);
      setShowAddModal(false);
      setNewMedication({
        drug_name: '',
        dosage: '',
        frequency: '',
        start_date: new Date().toISOString().split('T')[0],
        end_date: '',
        notes: ''
      });
    } catch (error) {
      console.error('Error adding medication:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredMedications = medications.filter(m => 
    m.drug_name.toLowerCase().includes(searchQuery.toLowerCase())
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
          <div className="text-[10px] font-bold uppercase tracking-[0.3em] text-primary mb-2">Prescription Management</div>
          <h1 className="text-5xl font-display font-bold tracking-tighter uppercase">Medications<span className="text-primary">.</span></h1>
          <p className="text-white/40 text-[10px] font-bold uppercase tracking-[0.3em] mt-2">Manage your prescriptions and reminders.</p>
        </motion.div>
        <motion.button 
          variants={itemVariants}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={() => setShowAddModal(true)}
          className="px-10 py-5 bg-primary text-black font-bold uppercase tracking-[0.2em] flex items-center gap-4 hover:bg-white transition-all border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] group"
        >
          <Plus size={24} className="group-hover:rotate-90 transition-transform" /> Add New
        </motion.button>
      </div>

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
                  <div className="text-[10px] font-bold uppercase tracking-[0.4em] text-primary mb-2">New Prescription</div>
                  <h2 className="text-4xl font-display font-bold uppercase tracking-tighter">Add Medication<span className="text-primary">.</span></h2>
                </div>
                <button 
                  onClick={() => setShowAddModal(false)}
                  className="w-12 h-12 border-2 border-white/10 flex items-center justify-center text-white/20 hover:text-primary hover:border-primary transition-all"
                >
                  <X size={24} />
                </button>
              </div>

              <form onSubmit={handleAddMedication} className="space-y-8">
                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Drug Name</label>
                  <input 
                    required
                    type="text"
                    value={newMedication.drug_name}
                    onChange={(e) => setNewMedication({...newMedication, drug_name: e.target.value})}
                    className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                  />
                </div>

                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Dosage</label>
                    <input 
                      required
                      type="text"
                      placeholder="e.g. 500mg"
                      value={newMedication.dosage}
                      onChange={(e) => setNewMedication({...newMedication, dosage: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Frequency</label>
                    <input 
                      required
                      type="text"
                      placeholder="e.g. Twice daily"
                      value={newMedication.frequency}
                      onChange={(e) => setNewMedication({...newMedication, frequency: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-8">
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Start Date</label>
                    <input 
                      required
                      type="date"
                      value={newMedication.start_date}
                      onChange={(e) => setNewMedication({...newMedication, start_date: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    />
                  </div>
                  <div className="space-y-3">
                    <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">End Date (Optional)</label>
                    <input 
                      type="date"
                      value={newMedication.end_date}
                      onChange={(e) => setNewMedication({...newMedication, end_date: e.target.value})}
                      className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white"
                    />
                  </div>
                </div>

                <div className="space-y-3">
                  <label className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Notes</label>
                  <textarea 
                    rows={3}
                    value={newMedication.notes}
                    onChange={(e) => setNewMedication({...newMedication, notes: e.target.value})}
                    className="w-full bg-black border-2 border-white/10 px-6 py-4 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white resize-none"
                  />
                </div>

                <button 
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-6 bg-primary text-black font-bold uppercase tracking-[0.3em] flex items-center justify-center gap-4 hover:bg-white transition-all border-4 border-black shadow-[8px_8px_0px_0px_rgba(255,255,255,0.1)] disabled:opacity-50"
                >
                  {isSubmitting ? <Loader2 className="animate-spin" /> : <Save size={20} />}
                  Save Medication
                </button>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      <div className="grid md:grid-cols-3 gap-8">
        <motion.div 
          variants={itemVariants}
          whileHover={{ y: -5 }}
          className="brutalist-card p-10 bg-primary text-black border-4 border-black shadow-[12px_12px_0px_0px_rgba(0,0,0,0.3)] group cursor-pointer"
        >
          <div className="flex items-center gap-6 mb-8">
            <div className="w-14 h-14 bg-black text-primary flex items-center justify-center border-4 border-black group-hover:scale-110 transition-transform">
              <Clock size={28} />
            </div>
            <h3 className="text-[10px] font-bold uppercase tracking-[0.3em]">Next Dose</h3>
          </div>
          <p className="text-5xl font-display font-bold mb-3 uppercase tracking-tighter leading-none">08:00 AM</p>
          <p className="text-black/60 text-[10px] font-bold uppercase tracking-[0.2em]">Metformin (500mg)</p>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          whileHover={{ y: -5 }}
          className="brutalist-card p-10 bg-surface border-2 border-white/10 group cursor-pointer"
        >
          <div className="flex items-center gap-6 mb-8">
            <div className="w-14 h-14 bg-black border-2 border-white/10 flex items-center justify-center text-primary group-hover:border-primary transition-all">
              <Calendar size={28} />
            </div>
            <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Adherence</h3>
          </div>
          <p className="text-5xl font-display font-bold text-white mb-3 uppercase tracking-tighter leading-none">94%</p>
          <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.2em]">Last 30 days</p>
        </motion.div>

        <motion.div 
          variants={itemVariants}
          whileHover={{ y: -5 }}
          className="brutalist-card p-10 bg-surface border-2 border-white/10 group cursor-pointer"
        >
          <div className="flex items-center gap-6 mb-8">
            <div className="w-14 h-14 bg-black border-2 border-white/10 flex items-center justify-center text-red-500 group-hover:border-red-500 transition-all">
              <AlertCircle size={28} />
            </div>
            <h3 className="text-[10px] font-bold uppercase tracking-[0.3em] text-white/20">Refills</h3>
          </div>
          <p className="text-5xl font-display font-bold text-white mb-3 uppercase tracking-tighter leading-none">2</p>
          <p className="text-white/20 text-[10px] font-bold uppercase tracking-[0.2em]">Need attention</p>
        </motion.div>
      </div>

      <motion.div 
        variants={itemVariants}
        className="brutalist-card overflow-hidden bg-surface border-2 border-white/10"
      >
        <div className="p-10 border-b-2 border-white/10 bg-black/40 flex justify-between items-center">
          <h2 className="text-2xl font-display font-bold uppercase tracking-tight">Current Medications</h2>
          <div className="relative w-64 group">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 group-focus-within:text-primary transition-colors" size={16} />
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search meds..."
              className="w-full pl-10 pr-4 py-3 bg-black border-2 border-white/10 outline-none focus:border-primary transition-all text-[10px] font-bold uppercase tracking-widest text-white placeholder:text-white/20"
            />
          </div>
        </div>
        <div className="divide-y-2 divide-white/10">
          {isLoading ? (
            <div className="p-20 text-center text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">Loading Medications...</div>
          ) : filteredMedications.length === 0 ? (
            <div className="p-20 text-center text-white/20 text-[10px] font-bold uppercase tracking-[0.5em]">No medications found</div>
          ) : (
            filteredMedications.map((med) => (
              <motion.div 
                key={med.id} 
                whileHover={{ backgroundColor: 'rgba(255, 255, 255, 0.02)' }}
                className="p-10 flex items-center justify-between group cursor-pointer"
              >
                <div className="flex items-center gap-8">
                  <div className={cn("w-20 h-20 border-2 border-white/10 flex items-center justify-center text-primary group-hover:border-primary group-hover:bg-primary/10 transition-all")}>
                    <Pill size={40} className="group-hover:rotate-12 transition-transform" />
                  </div>
                  <div>
                    <h3 className="text-2xl font-display font-bold uppercase tracking-tight mb-2 group-hover:text-primary transition-all">{med.drug_name}</h3>
                    <p className="text-[10px] text-white/20 font-bold uppercase tracking-[0.3em]">{med.dosage} • {med.frequency}</p>
                  </div>
                </div>
                <div className="text-right flex items-center gap-16">
                  <div className="hidden md:block">
                    <p className="text-[10px] text-white/10 font-bold uppercase tracking-[0.4em] mb-3">Schedule</p>
                    <p className="text-sm font-bold text-white uppercase tracking-[0.2em]">{med.start_date ? new Date(med.start_date).toLocaleDateString() : 'N/A'}</p>
                  </div>
                  <motion.button 
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteMedication(med.id);
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
            ))
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};

export default Medications;
