// Simple local model for offline inference
class LocalModel {
  constructor() {
    this.model = null;
    this.vocab = null;
    this.loaded = false;
  }
  
  async load() {
    if (this.loaded) return;
    
    try {
      // Load vocabulary
      const vocabResponse = await fetch('/models/vocab.json');
      this.vocab = await vocabResponse.json();
      
      // Load model weights (simplified)
      // In production, use TensorFlow.js or ONNX Runtime
      this.model = {
        predict: (input) => {
          // Very simple pattern matching
          return this.generateResponse(input);
        }
      };
      
      this.loaded = true;
      console.log('Local model loaded');
      
    } catch (error) {
      console.error('Failed to load local model:', error);
    }
  }
  
  generateResponse(input) {
    const text = input.toLowerCase();
    
    // Simple pattern matching
    if (text.includes('hello') || text.includes('hi')) {
      return {
        text: "Hello! I'm your offline tutor. For detailed answers, please connect to the internet.",
        confidence: 0.7
      };
    }
    
    if (text.includes('what is')) {
      const topic = text.replace('what is', '').trim();
      return {
        text: `I can explain "${topic}" when you're online. For now, check your textbook.`,
        confidence: 0.5
      };
    }
    
    return {
      text: "I understand your question. Please connect to the internet for a complete answer.",
      confidence: 0.6
    };
  }
  
  async predict(input) {
    if (!this.loaded) {
      await this.load();
    }
    
    return this.model.predict(input);
  }
  
  isLoaded() {
    return this.loaded;
  }
}

export const localModel = new LocalModel();