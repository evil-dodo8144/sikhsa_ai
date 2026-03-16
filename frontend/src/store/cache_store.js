import { create } from 'zustand';
import { cacheManager } from '../services/cache_manager';

export const useCache = create((set, get) => ({
  stats: null,
  loading: false,
  
  refreshStats: async () => {
    set({ loading: true });
    try {
      const stats = await cacheManager.getStats();
      set({ stats, loading: false });
    } catch (error) {
      console.error('Failed to get cache stats:', error);
      set({ loading: false });
    }
  },
  
  clearCache: async (store = null) => {
    set({ loading: true });
    try {
      await cacheManager.clear(store);
      await get().refreshStats();
    } catch (error) {
      console.error('Failed to clear cache:', error);
      set({ loading: false });
    }
  },
  
  getItem: async (key, store) => {
    return cacheManager.get(key, store);
  },
  
  setItem: async (key, value, store) => {
    return cacheManager.set(key, value, store);
  }
}));