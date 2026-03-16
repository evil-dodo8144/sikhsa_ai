import localforage from 'localforage';

// Configure IndexedDB
localforage.config({
  name: 'ScaleDownTutor',
  version: 1.0,
  storeName: 'app_data',
  description: 'Offline storage for ScaleDown Tutor'
});

export const storage = {
  async get(key) {
    try {
      return await localforage.getItem(key);
    } catch (error) {
      console.error('Storage get error:', error);
      return null;
    }
  },
  
  async set(key, value) {
    try {
      await localforage.setItem(key, value);
      return true;
    } catch (error) {
      console.error('Storage set error:', error);
      return false;
    }
  },
  
  async remove(key) {
    try {
      await localforage.removeItem(key);
      return true;
    } catch (error) {
      console.error('Storage remove error:', error);
      return false;
    }
  },
  
  async clear() {
    try {
      await localforage.clear();
      return true;
    } catch (error) {
      console.error('Storage clear error:', error);
      return false;
    }
  },
  
  async keys() {
    try {
      return await localforage.keys();
    } catch (error) {
      console.error('Storage keys error:', error);
      return [];
    }
  },
  
  async getUsage() {
    try {
      const keys = await localforage.keys();
      let totalSize = 0;
      
      for (const key of keys) {
        const value = await localforage.getItem(key);
        const size = new Blob([JSON.stringify(value)]).size;
        totalSize += size;
      }
      
      return {
        itemCount: keys.length,
        totalSizeBytes: totalSize,
        totalSizeMB: (totalSize / (1024 * 1024)).toFixed(2)
      };
    } catch (error) {
      console.error('Storage usage error:', error);
      return null;
    }
  }
};