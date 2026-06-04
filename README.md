# RASA + OpenAI Hybrid Chatbot

> Structured intent handling with RASA NLU + GPT-4o-mini fallback for open-ended conversations. Deployable on Kubernetes via Helm.

[![CI](https://github.com/aleksandar-rakic/rasa-openai-hybrid/actions/workflows/ci.yml/badge.svg)](https://github.com/aleksandar-rakic/rasa-openai-hybrid/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.10-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![RASA](https://img.shields.io/badge/RASA-3.6-5A17EE?style=flat-square)](https://rasa.com)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](LICENSE)

## Architecture

```
User message
     │
     ▼
RASA NLU (intent classification)
     │
     ├── confidence ≥ 0.70 → Structured RASA response
     │                        (pricing, features, bug report, handoff)
     │
     └── confidence < 0.70 → action_openai_fallback
                               │
                               ├── Build conversation history (last 5 turns)
                               ├── Query GPT-4o-mini with system prompt
                               └── Return contextual response
```

**Best of both worlds:**
- RASA handles structured business logic (forms, slots, deterministic flows)
- OpenAI handles open-ended questions, edge cases, and out-of-scope intents

## Stack

| Component | Technology |
|-----------|-----------|
| NLU / Core | RASA 3.6 (DIET classifier, TEDPolicy) |
| Fallback LLM | OpenAI GPT-4o-mini (async) |
| Actions server | Python 3.10 + rasa-sdk |
| Containerization | Docker + Docker Compose |
| Orchestration | Kubernetes + Helm |
| CI/CD | GitHub Actions |
| Linting | Ruff + Mypy |

## Getting Started

```bash
# Clone
git clone https://github.com/aleksandar-rakic/rasa-openai-hybrid.git
cd rasa-openai-hybrid

# Configure
cp .env.example .env
# Add your OPENAI_API_KEY to .env

# Train the model
docker compose --profile train up trainer

# Start
docker compose up -d

# Test
curl -X POST http://localhost:5005/webhooks/rest/webhook \
  -H "Content-Type: application/json" \
  -d '{"sender": "user1", "message": "What are your pricing plans?"}'
```

## Project Structure

```
.
├── config.yml              # NLU pipeline + policies
├── domain.yml              # Intents, entities, slots, responses
├── requirements.txt        # Python dependencies
├── Dockerfile.actions      # Actions server container
├── docker-compose.yml      # Local development stack
│
├── data/
│   ├── nlu.yml             # Training examples
│   └── rules.yml           # Conversation rules
│
├── actions/
│   ├── openai_fallback.py  # GPT-4o-mini fallback action
│   └── transfer_to_human.py# Human handoff action
│
└── helm/rasa/              # Kubernetes Helm chart
    ├── Chart.yaml
    └── values.yaml         # HPA, PDB, ingress, resource limits
```

## Kubernetes Deployment

```bash
# Add secrets
kubectl create secret generic rasa-openai \
  --from-literal=OPENAI_API_KEY=sk-...

# Deploy
helm upgrade --install rasa-chatbot ./helm/rasa \
  --set actions.secret.OPENAI_API_KEY=$(kubectl get secret rasa-openai -o jsonpath='{.data.OPENAI_API_KEY}' | base64 -d) \
  --set ingress.hosts[0].host=chatbot.yourdomain.com \
  --namespace chatbot --create-namespace
```

The Helm chart includes:
- Horizontal Pod Autoscaler (2–10 replicas based on CPU)
- Pod Disruption Budget (min 1 available)
- Ingress with TLS via cert-manager
- Resource requests/limits for both RASA and actions containers

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_API_KEY` | required | OpenAI API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model to use |
| `RASA_TELEMETRY_ENABLED` | `false` | Disable RASA telemetry |

## License

MIT © [Aleksandar Rakić](https://github.com/aleksandar-rakic)
