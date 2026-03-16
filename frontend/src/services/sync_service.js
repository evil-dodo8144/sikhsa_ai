import { api } from './api';
import { offlineQueue } from './offline_queue';
import { cacheManager } from './cache_manager';

class SyncService {
  constructor() {
    this.syncing = false;
    this.syncInterval = null;
  }
  
  startAutoSync(interval = 5 * 60 * 1000) { // Every 5 minutes
    this.syncInterval = setInterval(() => {
      if (navigator.onLine && !this.syncing) {
        this.sync();
      }
    }, interval);
  }
  
  stopAutoSync() {
    if (this.syncInterval) {
      clearInterval(this.syncInterval);
      this.syncInterval = null;
    }
  }
  
  async sync() {
    if (this.syncing || !navigator.onLine) {
      return { success: false, reason: 'Already syncing or offline' };
    }
    
    this.syncing = true;
    const results = {
      synced: 0,
      failed: 0,
      errors: []
    };
    
    try {
      // Get pending queries
      const pending = await offlineQueue.getPending();
      
      for (const item of pending) {
        try {
          // Attempt to sync
          const response = await api.sendQuery(
            item.query,
            item.grade,
            item.subject,
            item.studentId
          );
          
          // Cache the response
          await cacheManager.set(
            `query:${item.id}`,
            response,
            'responses'
          );
          
          // Mark as synced
          await offlineQueue.markSynced([item.id]);
          results.synced++;
          
        } catch (error) {
          console.error('Sync failed for item:', item.id, error);
          results.failed++;
          results.errors.push({
            id: item.id,
            error: error.message
          });
          
          // Increment attempt count
          await offlineQueue.incrementAttempt(item.id);
        }
      }
      
      return results;
      
    } finally {
      this.syncing = false;
    }
  }
  
  getQueuedCount() {
    return offlineQueue.getCount();
  }
  
  isSyncing() {
    return this.syncing;
  }
}

export const syncService = new SyncService();