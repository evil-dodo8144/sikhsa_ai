"""
Sync Manager for Offline-First Operation
Location: backend/src/offline/sync_manager.py
"""

import asyncio
from typing import Dict, Any, List
from datetime import datetime, timedelta
import json
from pathlib import Path
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class SyncManager:
    """
    Manages synchronization between local and cloud
    Enables offline-first operation
    """
    
    def __init__(self):
        self.sync_queue = []
        self.last_sync = None
        self.sync_in_progress = False
        self.sync_path = Path(config.DATA_DIR) / "sync"
        self.sync_path.mkdir(parents=True, exist_ok=True)
        
    async def queue_for_sync(self, item: Dict[str, Any]) -> None:
        """
        Queue item for later sync
        """
        item["queued_at"] = datetime.utcnow().isoformat()
        item["sync_attempts"] = 0
        self.sync_queue.append(item)
        
        # Save to disk for persistence
        await self._save_queue()
        
        logger.debug(f"Queued item for sync: {item.get('type')}")
    
    async def sync(self) -> Dict[str, Any]:
        """
        Perform sync with cloud
        """
        if self.sync_in_progress:
            return {"status": "sync_already_in_progress"}
        
        self.sync_in_progress = True
        results = {
            "synced": 0,
            "failed": 0,
            "errors": []
        }
        
        try:
            # Check connectivity first
            if not await self._check_connectivity():
                return {"status": "offline", "message": "No internet connection"}
            
            # Process queue
            for item in self.sync_queue[:]:
                try:
                    success = await self._sync_item(item)
                    if success:
                        self.sync_queue.remove(item)
                        results["synced"] += 1
                    else:
                        item["sync_attempts"] += 1
                        results["failed"] += 1
                        
                        # Remove if too many attempts
                        if item["sync_attempts"] > 5:
                            self.sync_queue.remove(item)
                            results["errors"].append({
                                "item": item,
                                "error": "Max attempts exceeded"
                            })
                except Exception as e:
                    logger.error(f"Sync error: {str(e)}")
                    results["failed"] += 1
                    results["errors"].append({"item": item, "error": str(e)})
            
            # Update last sync time
            self.last_sync = datetime.utcnow()
            
            # Save updated queue
            await self._save_queue()
            
            results["status"] = "success"
            results["queue_remaining"] = len(self.sync_queue)
            
        finally:
            self.sync_in_progress = False
        
        return results
    
    async def _sync_item(self, item: Dict[str, Any]) -> bool:
        """
        Sync single item with cloud
        """
        # Implementation depends on cloud API
        # This is a placeholder
        logger.info(f"Syncing item: {item.get('type')}")
        return True
    
    async def _check_connectivity(self) -> bool:
        """
        Check internet connectivity
        """
        try:
            import requests
            requests.get("https://api.scaledown.ai/health", timeout=2)
            return True
        except:
            return False
    
    async def _save_queue(self) -> None:
        """Save sync queue to disk"""
        queue_file = self.sync_path / "sync_queue.json"
        with open(queue_file, 'w') as f:
            json.dump({
                "queue": self.sync_queue,
                "last_sync": self.last_sync.isoformat() if self.last_sync else None
            }, f, indent=2)
    
    async def _load_queue(self) -> None:
        """Load sync queue from disk"""
        queue_file = self.sync_path / "sync_queue.json"
        if queue_file.exists():
            with open(queue_file, 'r') as f:
                data = json.load(f)
                self.sync_queue = data.get("queue", [])
                last_sync = data.get("last_sync")
                if last_sync:
                    self.last_sync = datetime.fromisoformat(last_sync)
    
    def get_status(self) -> Dict[str, Any]:
        """Get sync status"""
        return {
            "queue_size": len(self.sync_queue),
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "sync_in_progress": self.sync_in_progress,
            "items_queued": [item.get("type") for item in self.sync_queue[:5]]
        }