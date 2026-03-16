import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useQuery = create(
  persist(
    (set, get) => ({
      queries: [],
      recentQueries: [],
      
      addQuery: (query) => set((state) => {
        const newQueries = [query, ...state.queries].slice(0, 100);
        const newRecent = [query.query, ...state.recentQueries]
          .filter((v, i, a) => a.indexOf(v) === i)
          .slice(0, 10);
        
        return {
          queries: newQueries,
          recentQueries: newRecent
        };
      }),
      
      getRecentQueries: () => get().recentQueries,
      
      clearHistory: () => set({ queries: [], recentQueries: [] }),
      
      getStats: () => {
        const { queries } = get();
        return {
          total: queries.length,
          last24h: queries.filter(q => 
            new Date(q.timestamp) > new Date(Date.now() - 24*60*60*1000)
          ).length
        };
      }
    }),
    {
      name: 'query-history'
    }
  )
);