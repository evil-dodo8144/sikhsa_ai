# ScaleDown AI Tutor for Rural India

## 📚 Overview
An intelligent tutoring system that ingests state-board textbooks and provides personalized, curriculum-aligned answers with minimal cost and data transfer using ScaleDown API for prompt optimization.

## 🎯 Key Features
- **ScaleDown API Integration**: 40-80% reduction in token usage
- **Multi-Level Indexing**: Chapter, concept, and page-level embeddings
- **Context Pruning**: 80-95% reduction in context size
- **Offline-First**: Works with spotty internet connectivity
- **Cost Optimization**: Tiered LLM routing for maximum savings

## 🏗️ Architecture
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ Frontend │────▶│ API Gateway │────▶│ ScaleDown API │
│ (React PWA) │ │ (FastAPI) │ │ (Optimization) │
└─────────────────┘ └─────────────────┘ └─────────────────┘
│
▼
┌─────────────────┐
│ LLM Providers │
│ (GPT-4, Claude)│
└─────────────────┘


## 🚀 Quick Start
```bash
# Clone repository
git clone https://github.com/yourusername/scaledown-tutor.git
cd scaledown-tutor

# Setup backend
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Setup frontend
cd ../frontend
npm install

# Configure environment
cp .env.example .env
# Edit .env with your ScaleDown API key

# Run the application
docker-compose up -d