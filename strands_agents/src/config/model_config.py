"""
Bedrock Model Configuration Utilities

Provides utilities for configuring and managing Bedrock models:
- Model parameter presets
- Agent-specific model configurations
- Token management
- Model selection helpers
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from .constants import AgentName, DEFAULT_MODEL_ID, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE


@dataclass
class ModelConfig:
    """
    Configuration for a Bedrock model.
    
    Attributes:
        model_id: Bedrock model identifier
        max_tokens: Maximum tokens for generation
        temperature: Sampling temperature (0.0-1.0)
        top_p: Nucleus sampling parameter
        top_k: Top-k sampling parameter
        stop_sequences: List of stop sequences
    """
    
    model_id: str
    max_tokens: int = DEFAULT_MAX_TOKENS
    temperature: float = DEFAULT_TEMPERATURE
    top_p: float = 0.9
    top_k: int = 250
    stop_sequences: Optional[list] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Strands Agent."""
        config = {
            "model_id": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
        }
        
        # Only include top_k for models that support it
        if "anthropic" in self.model_id:
            config["top_k"] = self.top_k
        
        if self.stop_sequences:
            config["stop_sequences"] = self.stop_sequences
        
        return config


# ============================================================================
# Model Presets
# ============================================================================

# High-quality reasoning for complex tasks
REASONING_MODEL = ModelConfig(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tokens=4096,
    temperature=0.7,
    top_p=0.9,
    top_k=250
)

# Fast responses for simple queries
FAST_MODEL = ModelConfig(
    model_id="anthropic.claude-3-haiku-20240307-v1:0",
    max_tokens=2048,
    temperature=0.5,
    top_p=0.9,
    top_k=250
)

# High-quality long-form content
CREATIVE_MODEL = ModelConfig(
    model_id="anthropic.claude-3-opus-20240229-v1:0",
    max_tokens=4096,
    temperature=0.8,
    top_p=0.95,
    top_k=200
)

# Precise, deterministic responses
PRECISE_MODEL = ModelConfig(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    max_tokens=4096,
    temperature=0.1,
    top_p=0.9,
    top_k=250
)


# ============================================================================
# Agent-Specific Configurations
# ============================================================================

AGENT_MODEL_CONFIGS: Dict[AgentName, ModelConfig] = {
    AgentName.ORCHESTRATOR: ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=4096,
        temperature=0.5,  # More deterministic for routing
        top_p=0.9
    ),
    
    AgentName.GRAPH: ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=4096,
        temperature=0.3,  # Precise for query generation
        top_p=0.9
    ),
    
    AgentName.ANALYZER: ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=4096,
        temperature=0.7,  # Balanced for analysis
        top_p=0.9
    ),
    
    AgentName.EXTRACTOR: ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=4096,
        temperature=0.4,  # Precise for data extraction
        top_p=0.9
    ),
    
    AgentName.ADMIN: ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        max_tokens=2048,
        temperature=0.2,  # Very precise for admin operations
        top_p=0.9
    )
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_model_config(
    agent_name: AgentName,
    override_model_id: Optional[str] = None
) -> ModelConfig:
    """
    Get model configuration for an agent.
    
    Args:
        agent_name: Name of the agent
        override_model_id: Optional model ID to override default
    
    Returns:
        ModelConfig instance
    
    Example:
        >>> config = get_model_config(AgentName.GRAPH)
        >>> config.model_id
        'anthropic.claude-3-5-sonnet-20241022-v2:0'
    """
    # Get base config for agent
    config = AGENT_MODEL_CONFIGS.get(agent_name, REASONING_MODEL)
    
    # Apply model override if provided
    if override_model_id:
        config = ModelConfig(
            model_id=override_model_id,
            max_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            top_k=config.top_k,
            stop_sequences=config.stop_sequences
        )
    
    return config


def create_custom_model_config(
    model_id: str,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
    **kwargs
) -> ModelConfig:
    """
    Create a custom model configuration.
    
    Args:
        model_id: Bedrock model identifier
        max_tokens: Optional max tokens override
        temperature: Optional temperature override
        **kwargs: Additional model parameters
    
    Returns:
        ModelConfig instance
    
    Example:
        >>> config = create_custom_model_config(
        ...     "anthropic.claude-3-opus-20240229-v1:0",
        ...     max_tokens=8192,
        ...     temperature=0.9
        ... )
    """
    return ModelConfig(
        model_id=model_id,
        max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        temperature=temperature if temperature is not None else DEFAULT_TEMPERATURE,
        top_p=kwargs.get("top_p", 0.9),
        top_k=kwargs.get("top_k", 250),
        stop_sequences=kwargs.get("stop_sequences")
    )


def get_model_config_from_yaml(config_dict: Dict[str, Any]) -> ModelConfig:
    """
    Create model configuration from YAML config dictionary.
    
    Args:
        config_dict: Configuration dictionary from YAML
    
    Returns:
        ModelConfig instance
    
    Example:
        >>> yaml_config = {
        ...     "model": "anthropic.claude-3-5-sonnet-20241022-v2:0",
        ...     "max_tokens": 4096
        ... }
        >>> config = get_model_config_from_yaml(yaml_config)
    """
    return ModelConfig(
        model_id=config_dict.get("model", DEFAULT_MODEL_ID),
        max_tokens=config_dict.get("max_tokens", DEFAULT_MAX_TOKENS),
        temperature=config_dict.get("temperature", DEFAULT_TEMPERATURE),
        top_p=config_dict.get("top_p", 0.9),
        top_k=config_dict.get("top_k", 250),
        stop_sequences=config_dict.get("stop_sequences")
    )


def estimate_token_count(text: str) -> int:
    """
    Estimate token count for text.
    
    This is a rough estimation. For accurate counts, use the
    Bedrock tokenizer for the specific model.
    
    Args:
        text: Text to estimate tokens for
    
    Returns:
        Estimated token count
    
    Note:
        Uses rough estimate of ~4 characters per token for English text.
    """
    # Rough estimation: ~4 chars per token
    return len(text) // 4


def validate_token_budget(
    prompt_tokens: int,
    max_output_tokens: int,
    model_context_window: int = 200000
) -> bool:
    """
    Validate that token budget fits within model context window.
    
    Args:
        prompt_tokens: Number of tokens in prompt
        max_output_tokens: Maximum desired output tokens
        model_context_window: Model's total context window
    
    Returns:
        True if within budget, False otherwise
    
    Example:
        >>> validate_token_budget(150000, 4096, 200000)
        True
        >>> validate_token_budget(195000, 10000, 200000)
        False
    """
    total_tokens = prompt_tokens + max_output_tokens
    return total_tokens <= model_context_window


def get_recommended_model(
    task_complexity: str = "medium",
    response_speed: str = "balanced"
) -> ModelConfig:
    """
    Get recommended model based on task requirements.
    
    Args:
        task_complexity: Task complexity (simple, medium, complex)
        response_speed: Speed requirement (fast, balanced, quality)
    
    Returns:
        Recommended ModelConfig
    
    Example:
        >>> config = get_recommended_model("complex", "quality")
        >>> config.model_id
        'anthropic.claude-3-opus-20240229-v1:0'
    """
    if response_speed == "fast":
        return FAST_MODEL
    elif task_complexity == "complex" and response_speed == "quality":
        return CREATIVE_MODEL
    elif task_complexity == "simple":
        return FAST_MODEL
    else:
        # Default to reasoning model for balanced performance
        return REASONING_MODEL


# ============================================================================
# Model Families and Capabilities
# ============================================================================

MODEL_CAPABILITIES = {
    "anthropic.claude-3-opus": {
        "context_window": 200000,
        "strengths": ["complex reasoning", "long-form content", "nuanced analysis"],
        "best_for": ["research", "creative writing", "detailed analysis"]
    },
    "anthropic.claude-3-5-sonnet": {
        "context_window": 200000,
        "strengths": ["balanced performance", "code generation", "analysis"],
        "best_for": ["general tasks", "coding", "structured output"]
    },
    "anthropic.claude-3-haiku": {
        "context_window": 200000,
        "strengths": ["speed", "efficiency", "simple tasks"],
        "best_for": ["quick responses", "simple queries", "high throughput"]
    }
}


def get_model_capabilities(model_id: str) -> Dict[str, Any]:
    """
    Get capabilities for a model.
    
    Args:
        model_id: Bedrock model identifier
    
    Returns:
        Dictionary of model capabilities
    """
    # Extract model family from ID
    for family in MODEL_CAPABILITIES:
        if family in model_id:
            return MODEL_CAPABILITIES[family]
    
    # Default capabilities
    return {
        "context_window": 200000,
        "strengths": ["general purpose"],
        "best_for": ["general tasks"]
    }

