import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useUser = create(
  persist(
    (set, get) => ({
      studentId: null,
      name: '',
      grade: 7,
      subject: 'mathematics',
      tier: 'free',
      preferences: {
        theme: 'light',
        fontSize: 'medium',
        language: 'en'
      },
      
      setUser: (userData) => set({
        studentId: userData.studentId,
        name: userData.name,
        grade: userData.grade,
        subject: userData.subject,
        tier: userData.tier
      }),
      
      updatePreferences: (prefs) => set((state) => ({
        preferences: { ...state.preferences, ...prefs }
      })),
      
      getTier: () => get().tier,
      
      isPremium: () => get().tier === 'premium' || get().tier === 'enterprise'
    }),
    {
      name: 'user-storage'
    }
  )
);