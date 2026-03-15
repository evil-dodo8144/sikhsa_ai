"""
Intent Classifier - Classify query type
Location: backend/src/query/intent_classifier.py
"""

from typing import Dict, Any, List
import re
from ..utils.logger import get_logger

logger = get_logger(__name__)

class IntentClassifier:
    """Classify the intent of student queries"""
    
    def __init__(self):
        self.intent_patterns = {
            'factual': [
                r'\b(what is|who is|when did|where is)\b',
                r'\b(define|definition|meaning)\b',
                r'\b(fact|facts about)\b'
            ],
            'conceptual': [
                r'\b(how does|how do|why does|why is)\b',
                r'\b(explain|describe|understand)\b',
                r'\b(concept|principle|theory)\b'
            ],
            'problem_solving': [
                r'\b(how to|how can I|solve|calculate|find)\b',
                r'\b(problem|equation|formula|method)\b',
                r'\b(step by step|solution|approach)\b'
            ],
            'comparison': [
                r'\b(compare|contrast|difference between|similarities)\b',
                r'\b(versus|vs|better than|worse than)\b'
            ],
            'example': [
                r'\b(example|instance|sample|illustrate)\b',
                r'\b(show me|give me an example)\b'
            ],
            'verification': [
                r'\b(is it true|correct|right|wrong|verify|check)\b',
                r'\b(am I correct|did I understand)\b'
            ]
        }
        
        self.subject_hints = {
            'mathematics': ['math', 'algebra', 'geometry', 'calculus', 'equation', 'formula'],
            'science': ['science', 'physics', 'chemistry', 'biology', 'experiment', 'lab'],
            'history': ['history', 'historical', 'century', 'war', 'revolution', 'empire'],
            'geography': ['geography', 'map', 'country', 'capital', 'river', 'mountain'],
            'literature': ['literature', 'poem', 'novel', 'author', 'character', 'plot'],
            'computer_science': ['computer', 'programming', 'code', 'algorithm', 'data']
        }
        
    def classify(self, parsed_query: Dict[str, Any], grade: int) -> Dict[str, Any]:
        """
        Classify query intent
        """
        query_text = parsed_query['normalized'].lower()
        
        # Score each intent
        intent_scores = {}
        for intent, patterns in self.intent_patterns.items():
            score = 0
            for pattern in patterns:
                matches = re.findall(pattern, query_text, re.IGNORECASE)
                score += len(matches) * 2  # Weight for pattern matches
            
            # Boost for question type
            if intent in parsed_query.get('question_type', ''):
                score += 3
                
            intent_scores[intent] = score
        
        # Get primary intent
        primary_intent = max(intent_scores, key=intent_scores.get)
        
        # If no clear intent, default to factual
        if intent_scores[primary_intent] == 0:
            primary_intent = 'factual'
        
        # Detect subject
        subject = self._detect_subject(query_text)
        
        # Determine recommended model based on complexity
        recommended_model = self._recommend_model(
            primary_intent, 
            parsed_query['complexity'],
            grade
        )
        
        result = {
            'type': primary_intent,
            'scores': intent_scores,
            'subject': subject,
            'complexity': parsed_query['complexity'],
            'recommended_model': recommended_model,
            'needs_examples': primary_intent == 'example',
            'needs_step_by_step': primary_intent == 'problem_solving',
            'grade_level': grade
        }
        
        logger.info(f"Classified intent: {primary_intent} (subject: {subject})")
        return result
    
    def _detect_subject(self, text: str) -> str:
        """Detect subject area from query"""
        scores = {}
        
        for subject, keywords in self.subject_hints.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            if score > 0:
                scores[subject] = score
        
        if scores:
            return max(scores, key=scores.get)
        return 'general'
    
    def _recommend_model(self, intent: str, complexity: str, grade: int) -> str:
        """Recommend which LLM model to use"""
        # Complex tasks need better models
        if complexity == 'complex' or intent in ['problem_solving', 'conceptual']:
            return 'gpt-4'
        elif complexity == 'medium' or grade > 10:
            return 'gpt-3.5-turbo'
        else:
            return 'local'  # Use local model for simple queries