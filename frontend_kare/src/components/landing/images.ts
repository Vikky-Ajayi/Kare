import voiceDoctorIllustration from '../../assets/voice-doctor-illustration.jpg';

/** One image per Kare feature, reused between SolutionsTabs and WhoItsFor so
 * the two sections read as the same visual system. Pregnancy/Symptom/Meds
 * are real stock photos (Unsplash / Pexels — both free-to-use, no
 * attribution required); Voice Doctor is a drawn illustration instead of a
 * photo — stock search kept surfacing photos that didn't match who Kare is
 * actually built for. */
export const FEATURE_IMAGES = {
  voice: voiceDoctorIllustration,
  pregnancy: 'https://images.pexels.com/photos/5853666/pexels-photo-5853666.jpeg?auto=compress&cs=tinysrgb&w=900',
  symptom: 'https://images.pexels.com/photos/5711457/pexels-photo-5711457.jpeg?auto=compress&cs=tinysrgb&w=900',
  meds: 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?auto=format&fit=crop&q=80&w=900',
} as const;
