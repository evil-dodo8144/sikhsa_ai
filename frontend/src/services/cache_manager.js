import localforage from 'localforage';

// Configure different stores
const stores = {
  responses: localforage.createInstance({
    name: 'ScaleDownTutor',
    storeName: 'responses'
  }),
  embeddings: localforage.createInstance({
    name: 'ScaleDownTutor',
    storeName: 'embeddings'
  }),
  textbooks: localforage.createInstance({
    name: 'ScaleDownTutor',
    storeName: 'textbooks'
  })
};

class CacheManager {
  constructor() {
    this.maxSize = 100;
    this.ttl = 7 * 24 * 60 * 60 * 1000; // 7 days
  }
  
  async get(key, store = 'responses') {
    try {
      const item = await stores[store].getItem(key);
      
      if (!item) return null;
      
      // Check TTL
      if (Date.now() - item.timestamp > this.ttl) {
        await this.remove(key, store);
        return null;
      }
      
      return item.value;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }
  
  async set(key, value, store = 'responses') {
    try {
      const item = {
        value,
        timestamp: Date.now()
      };
      
      await stores[store].setItem(key, item);
      
      // Manage size
      await this.manageSize(store);
      
    } catch (error) {
      console.error('Cache set error:', error);
    }
  }
  
  async remove(key, store = 'responses') {
    try {
      await stores[store].removeItem(key);
    } catch (error) {
      console.error('Cache remove error:', error);
    }
  }
  
  async clear(store = null) {
    try {
      if (store) {
        await stores[store].clear();
      } else {
        for (const s of Object.values(stores)) {
          await s.clear();
        }
      }
    } catch (error) {
      console.error('Cache clear error:', error);
    }
  }
  
  async manageSize(store) {
    try {
      const keys = await stores[store].keys();
      
      if (keys.length > this.maxSize) {
        // Get all items with timestamps
        const items = await Promise.all(
          keys.map(async (key) => ({
            key,
            ...(await stores[store].getItem(key))
          }))
        );
        
        // Sort by timestamp (oldest first)
        items.sort((a, b) => a.timestamp - b.timestamp);
        
        // Remove oldest
        const toRemove = items.slice(0, items.length - this.maxSize);
        for (const item of toRemove) {
          await this.remove(item.key, store);
        }
      }
    } catch (error) {
      console.error('Cache management error:', error);
    }
  }
  
  async getStats() {
    const stats = {};
    
    for (const [name, store] of Object.entries(stores)) {
      const keys = await store.keys();
      stats[name] = {
        size: keys.length,
        keys: keys.slice(0, 10) // First 10 keys
      };
    }
    
    return stats;
  }
}

export const cacheManager = new CacheManager();