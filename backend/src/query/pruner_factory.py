"""
Pruner Factory - Creates appropriate pruner combinations
Location: backend/src/query/pruner_factory.py
"""

from typing import List, Dict, Any
from .strategies import SemanticPruner, GradePruner, TokenPruner, RecencyPruner
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PrunerFactory:
    """Factory to create pruner combinations based on context"""
    
    @staticmethod
    def create_pruners(config: Dict[str, Any]) -> List:
        """
        Create list of pruners based on configuration
        """
        pruners = []
        
        # Always use semantic pruner
        if config.get('use_semantic', True):
            pruners.append(SemanticPruner(
                threshold=config.get('semantic_threshold', 0.3)
            ))
        
        # Use grade pruner if student grade is known
        if config.get('use_grade', True):
            pruners.append(GradePruner(
                tolerance=config.get('grade_tolerance', 1)
            ))
        
        # Always use token pruner for budget control
        if config.get('use_token', True):
            pruners.append(TokenPruner(
                max_tokens=config.get('max_tokens', 2000)
            ))
        
        # Use recency pruner for time-sensitive subjects
        if config.get('use_recency', False):
            pruners.append(RecencyPruner(
                decay_factor=config.get('recency_decay', 0.1)
            ))
        
        logger.info(f"Created {len(pruners)} pruners: {[p.__class__.__name__ for p in pruners]}")
        return pruners
    
    @staticmethod
    def create_for_subject(subject: str, grade: int) -> List:
        """
        Create pruners optimized for specific subject
        """
        config = {
            'use_semantic': True,
            'use_grade': True,
            'use_token': True,
            'semantic_threshold': 0.3,
            'grade_tolerance': 1,
            'max_tokens': 2000
        }
        
        # Subject-specific adjustments
        if subject == 'history':
            config['use_recency'] = False  # History needs older content
            config['semantic_threshold'] = 0.25  # Be more inclusive
            
        elif subject == 'science':
            config['use_recency'] = True  # Science needs recent info
            config['recency_decay'] = 0.05  # Gentle decay
            
        elif subject == 'mathematics':
            config['semantic_threshold'] = 0.4  # Math needs precise matches
            config['max_tokens'] = 1500  # Math queries are shorter
            
        elif grade <= 5:  # Elementary school
            config['max_tokens'] = 1000  # Simpler content
            config['semantic_threshold'] = 0.25  # More inclusive
            
        return PrunerFactory.create_pruners(config)