"""
LLM Router with ScaleDown Integration
Location: backend/src/llm/router.py
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import asyncio

from .providers.local_tiny import LocalTinyModel
from .providers.gpt3_turbo import GPT3Turbo
from .providers.gpt4 import GPT4
from .providers.claude import ClaudeProvider
from .tier_manager import TierManager
from .cost_tracker import CostTracker
from ..scaledown.optimizer import PromptOptimizer
from ..utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class RoutingDecision:
    """Result of LLM routing decision"""
    model: str
    tier: str
    estimated_cost: float
    reason: str

class LLMRouter:
    """
    Routes queries to appropriate LLM based on:
    - Query complexity
    - Cost constraints
    - Student tier
    - Intent type
    """
    
    def __init__(self):
        self.tier_manager = TierManager()
        self.cost_tracker = CostTracker()
        self.optimizer = PromptOptimizer()
        
        # Initialize providers
        self.providers = {
            "local": LocalTinyModel(),
            "gpt-3.5-turbo": GPT3Turbo(),
            "gpt-4": GPT4(),
            "claude-instant": ClaudeProvider()
        }
        
        # Model costs per 1K tokens (approximate)
        self.model_costs = {
            "local": 0.0,
            "gpt-3.5-turbo": 0.0015,
            "gpt-4": 0.03,
            "claude-instant": 0.0016
        }
        
    async def route_and_generate(self,
                                prompt: str,
                                intent: Dict[str, Any],
                                student_tier: str = "free") -> Dict[str, Any]:
        """
        Route query to appropriate model and generate response
        """
        start_time = asyncio.get_event_loop().time()
        
        # Step 1: Determine which model to use
        routing = self._route(
            prompt=prompt,
            intent=intent,
            student_tier=student_tier
        )
        
        logger.info(f"Routing decision: {routing.model} (tier: {routing.tier})")
        
        # Step 2: Get provider
        provider = self.providers.get(routing.model)
        if not provider:
            logger.warning(f"Model {routing.model} not found, falling back to gpt-3.5-turbo")
            provider = self.providers["gpt-3.5-turbo"]
            routing.model = "gpt-3.5-turbo"
        
        # Step 3: Generate response
        try:
            response = await provider.generate(prompt)
            
            # Calculate cost
            tokens = len(prompt.split()) + len(response.get("text", "").split())
            cost = self._calculate_cost(routing.model, tokens)
            
            # Track cost
            self.cost_tracker.track(
                model=routing.model,
                tokens=tokens,
                cost=cost,
                student_tier=student_tier
            )
            
            processing_time = asyncio.get_event_loop().time() - start_time
            
            result = {
                "text": response.get("text", ""),
                "model": routing.model,
                "tokens_used": tokens,
                "cost": cost,
                "processing_time": processing_time,
                "success": True,
                "routing_reason": routing.reason
            }
            
            # Add sources if available
            if "sources" in response:
                result["sources"] = response["sources"]
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating response from {routing.model}: {str(e)}")
            
            # Fallback to local model
            logger.info("Falling back to local model")
            provider = self.providers["local"]
            response = await provider.generate(prompt)
            
            return {
                "text": response.get("text", "I'm having trouble answering right now. Please try again."),
                "model": "local_fallback",
                "tokens_used": len(prompt.split()),
                "cost": 0,
                "processing_time": asyncio.get_event_loop().time() - start_time,
                "success": True,
                "error": str(e)
            }
    
    def _route(self,
              prompt: str,
              intent: Dict[str, Any],
              student_tier: str) -> RoutingDecision:
        """
        Make routing decision
        """
        prompt_length = len(prompt.split())
        complexity = intent.get("complexity", "medium")
        subject = intent.get("subject", "general")
        
        # Tier-based budget
        tier_budget = self.tier_manager.get_budget(student_tier)
        
        # Check if we can use local model
        if (prompt_length < 100 and 
            complexity == "simple" and 
            tier_budget["max_daily_cost"] < 0.01):
            return RoutingDecision(
                model="local",
                tier=student_tier,
                estimated_cost=0,
                reason="Simple query, using free local model"
            )
        
        # Check for subjects that need better models
        if subject in ["mathematics", "science"] and complexity == "complex":
            if student_tier in ["premium", "enterprise"]:
                return RoutingDecision(
                    model="gpt-4",
                    tier=student_tier,
                    estimated_cost=self.model_costs["gpt-4"] * prompt_length / 1000,
                    reason=f"Complex {subject} query, using best model"
                )
        
        # Default to GPT-3.5
        return RoutingDecision(
            model="gpt-3.5-turbo",
            tier=student_tier,
            estimated_cost=self.model_costs["gpt-3.5-turbo"] * prompt_length / 1000,
            reason="Standard routing"
        )
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost for token usage"""
        cost_per_1k = self.model_costs.get(model, 0.0015)
        return (tokens / 1000) * cost_per_1k
    
    def get_cost_summary(self) -> Dict[str, Any]:
        """Get cost tracking summary"""
        return self.cost_tracker.get_summary()