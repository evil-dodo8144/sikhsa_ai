"""
Quantized Models for Edge Deployment
Location: backend/src/offline/quantized_models.py
"""

import numpy as np
from typing import Dict, Any, Optional
import json
from pathlib import Path
from ..utils.logger import get_logger
from ..config.settings import config

logger = get_logger(__name__)

class QuantizedModels:
    """
    Manage 2-bit quantized models for edge devices
    """
    
    def __init__(self):
        self.models_path = Path(config.MODEL_DIR) / "quantized"
        self.models_path.mkdir(parents=True, exist_ok=True)
        self.loaded_models = {}
        
    def quantize_weights(self, weights: np.ndarray, bits: int = 2) -> Dict[str, Any]:
        """
        Quantize model weights to lower precision
        """
        # Find min/max
        min_val = weights.min()
        max_val = weights.max()
        
        # Quantize to 2-bit (4 levels)
        if bits == 2:
            levels = 4
            # Scale to 0-3 range
            scaled = ((weights - min_val) / (max_val - min_val) * (levels - 1)).round()
            quantized = scaled.astype(np.uint8)
            
        elif bits == 4:
            levels = 16
            scaled = ((weights - min_val) / (max_val - min_val) * (levels - 1)).round()
            quantized = scaled.astype(np.uint8)
            
        elif bits == 8:
            # 8-bit quantization
            scaled = (weights * 127).round()
            quantized = scaled.astype(np.int8)
            
        else:
            raise ValueError(f"Unsupported bits: {bits}")
        
        return {
            "quantized": quantized,
            "min_val": float(min_val),
            "max_val": float(max_val),
            "bits": bits,
            "shape": weights.shape
        }
    
    def dequantize(self, quantized_data: Dict[str, Any]) -> np.ndarray:
        """
        Dequantize weights back to float32
        """
        quantized = quantized_data["quantized"]
        min_val = quantized_data["min_val"]
        max_val = quantized_data["max_val"]
        bits = quantized_data["bits"]
        shape = quantized_data["shape"]
        
        if bits == 2:
            levels = 4
            # Convert back to float
            dequantized = (quantized / (levels - 1)) * (max_val - min_val) + min_val
            
        elif bits == 4:
            levels = 16
            dequantized = (quantized / (levels - 1)) * (max_val - min_val) + min_val
            
        elif bits == 8:
            dequantized = quantized / 127.0
            
        else:
            raise ValueError(f"Unsupported bits: {bits}")
        
        return dequantized.reshape(shape)
    
    def save_quantized_model(self, model_name: str, model_data: Dict[str, Any]) -> None:
        """
        Save quantized model to disk
        """
        model_path = self.models_path / f"{model_name}.qmodel"
        
        # Convert numpy arrays to lists for JSON
        serializable = {}
        for key, value in model_data.items():
            if isinstance(value, np.ndarray):
                serializable[key] = value.tolist()
            elif isinstance(value, dict) and "quantized" in value:
                serializable[key] = {
                    "quantized": value["quantized"].tolist(),
                    "min_val": value["min_val"],
                    "max_val": value["max_val"],
                    "bits": value["bits"],
                    "shape": value["shape"]
                }
            else:
                serializable[key] = value
        
        with open(model_path, 'w') as f:
            json.dump(serializable, f)
        
        logger.info(f"Saved quantized model: {model_name}")
    
    def load_quantized_model(self, model_name: str) -> Optional[Dict[str, Any]]:
        """
        Load quantized model from disk
        """
        if model_name in self.loaded_models:
            return self.loaded_models[model_name]
        
        model_path = self.models_path / f"{model_name}.qmodel"
        if not model_path.exists():
            logger.warning(f"Model not found: {model_name}")
            return None
        
        with open(model_path, 'r') as f:
            data = json.load(f)
        
        # Convert lists back to numpy arrays
        for key, value in data.items():
            if isinstance(value, dict) and "quantized" in value:
                value["quantized"] = np.array(value["quantized"], dtype=np.uint8)
        
        self.loaded_models[model_name] = data
        logger.info(f"Loaded quantized model: {model_name}")
        
        return data
    
    def get_size_reduction(self, original_size: int, quantized_size: int) -> float:
        """
        Calculate size reduction percentage
        """
        return (1 - quantized_size / original_size) * 100