import localforage from 'localforage';

// Configure localforage
localforage.config({
  name: 'ScaleDownTutor',
  storeName: 'offline_queue',
  description: 'Offline query queue'
});

class OfflineQueue {
  constructor() {
    this.queue = [];
    this.init();
  }
  
  async init() {
    // Load queue from storage
    try {
      const saved = await localforage.getItem('query_queue');
      if (saved) {
        this.queue = saved;
      }
    } catch (error) {
      console.error('Failed to load queue:', error);
    }
  }
  
  async add(query) {
    const item = {
      id: Date.now().toString(),
      ...query,
      timestamp: new Date().toISOString(),
      attempts: 0
    };
    
    this.queue.push(item);
    await this.save();
    return item;
  }
  
  async remove(id) {
    this.queue = this.queue.filter(item => item.id !== id);
    await this.save();
  }
  
  async getAll() {
    return this.queue;
  }
  
  async getPending() {
    return this.queue.filter(item => !item.synced);
  }
  
  async markSynced(ids) {
    const idSet = new Set(ids);
    this.queue = this.queue.filter(item => !idSet.has(item.id));
    await this.save();
  }
  
  async incrementAttempt(id) {
    const item = this.queue.find(i => i.id === id);
    if (item) {
      item.attempts++;
      await this.save();
    }
  }
  
  async save() {
    try {
      await localforage.setItem('query_queue', this.queue);
    } catch (error) {
      console.error('Failed to save queue:', error);
    }
  }
  
  getCount() {
    return this.queue.length;
  }
  
  clear() {
    this.queue = [];
    this.save();
  }
}

export const offlineQueue = new OfflineQueue();