# System Architecture

## Overview
The ScaleDown AI Tutor uses a microservices architecture with offline-first capabilities.

## Components
1. **Frontend**: React PWA for mobile/web access
2. **Backend API**: FastAPI with async support
3. **ScaleDown Integration**: Prompt optimization service
4. **LLM Router**: Routes to appropriate models
5. **Indexing Service**: Multi-level textbook indexing
6. **Cache Layer**: Redis + local LRU cache

## Data Flow
1. Student submits query
2. Query parsed and intent classified
3. Context retrieved from index
4. Prompt optimized with ScaleDown
5. Routed to appropriate LLM
6. Response cached and returned