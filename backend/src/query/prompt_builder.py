"""
Prompt Builder for LLM Queries
Location: backend/src/query/prompt_builder.py
"""

from typing import Dict, Any, Optional
from datetime import datetime
from ..utils.logger import get_logger

logger = get_logger(__name__)

class PromptBuilder:
    """
    Builds minimal prompts for LLM queries
    Optimized for ScaleDown API compression
    """
    
    def __init__(self):
        self.templates = {
            "factual": """
Context: {context}

Question: {query}

Answer the question using ONLY the context above. Keep answer concise (1-2 sentences).
""",
            "conceptual": """
Context: {context}

Question: {query}

Explain the concept in simple terms suitable for grade {grade}. Use examples if helpful.
""",
            "problem_solving": """
Context: {context}

Problem: {query}

Solve step by step. Show your work. Final answer should be clear.
""",
            "definition": """
Context: {context}

Define: {query}

Give a clear definition suitable for grade {grade}. Include a simple example.
""",
            "comparison": """
Context: {context}

Compare: {query}

Highlight key similarities and differences. Be concise.
""",
            "example": """
Context: {context}

Give an example of: {query}

Provide a simple, clear example suitable for grade {grade}.
""",
            "verification": """
Context: {context}

Verify: {query}

Check if this is correct based on the context. Explain why.
"""
        }
        
    def build(self,
             query: str,
             context: Dict[str, Any],
             intent: Dict[str, Any],
             grade: int) -> str:
        """
        Build minimal prompt for LLM
        
        Args:
            query: Student's question
            context: Pruned context dictionary
            intent: Classified intent
            grade: Student's grade level
            
        Returns:
            Formatted prompt string
        """
        intent_type = intent.get("type", "factual")
        template = self.templates.get(intent_type, self.templates["factual"])
        
        # Extract context text
        context_text = context.get("text", "")
        
        # Build prompt
        prompt = template.format(
            context=context_text,
            query=query,
            grade=grade
        )
        
        # Clean up whitespace
        prompt = "\n".join(line.strip() for line in prompt.split("\n") if line.strip())
        
        logger.debug(f"Built {intent_type} prompt: {len(prompt)} chars")
        
        return prompt
    
    def build_with_instructions(self,
                               query: str,
                               context: Dict[str, Any],
                               intent: Dict[str, Any],
                               grade: int,
                               additional_instructions: Optional[str] = None) -> str:
        """
        Build prompt with additional instructions
        """
        base_prompt = self.build(query, context, intent, grade)
        
        if additional_instructions:
            base_prompt += f"\n\nAdditional instructions: {additional_instructions}"
        
        return base_prompt
    
    def build_minimal(self, query: str, context: str) -> str:
        """
        Build ultra-minimal prompt for maximum compression
        """
        return f"Q: {query}\nContext: {context[:500]}\nA:"