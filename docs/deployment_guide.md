# Complete Deployment Guide

## 📋 Prerequisites

### System Requirements
- **CPU**: 2+ cores (4+ recommended for production)
- **RAM**: 4GB minimum (8GB+ recommended)
- **Disk**: 20GB free space
- **OS**: Ubuntu 20.04+ / Debian 11+ (or any Linux distribution)

### Software Requirements
- **Docker** 24.0+ and Docker Compose 2.20+
- **Python** 3.10+
- **Node.js** 18+ and npm 9+
- **PostgreSQL** 15+
- **Redis** 7+
- **Nginx** 1.24+ (for production)

### API Keys Required
- **ScaleDown API Key** (Sign up at https://scaledown.ai)
- **OpenAI API Key** (Optional, for fallback)
- **Anthropic API Key** (Optional, for fallback)

---

## 🚀 Local Development Setup

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/scaledown-tutor.git
cd scaledown-tutor