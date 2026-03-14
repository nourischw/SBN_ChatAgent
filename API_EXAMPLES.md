# SBN ChatAgent - API Examples

This file contains example API requests for testing and integration.

## Health Check

```bash
# Check system health
curl http://localhost:3030/health | jq

# Expected response:
# {
#   "status": "healthy",
#   "api_available": true,
#   "ollama_status": "connected",
#   "ollama_model": "qwen2.5:0.5b"
# }
```

## Chat API

```bash
# Basic chat request
curl -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Hello, what products do you have?",
    "conversation_id": "test-session-1"
  }' | jq

# Chat with history
curl -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What about the second product you mentioned?",
    "conversation_id": "test-session-1",
    "include_history": true,
    "history_limit": 5
  }' | jq
```

## Product Management

```bash
# Load products from internal API
curl http://localhost:3030/api/products | jq

# Expected response:
# {
#   "success": true,
#   "data": [...],
#   "message": "Retrieved X products..."
# }

# Manually ingest product data
curl -X POST "http://localhost:3030/api/ingest?data_type=product" \
  -H "Content-Type: application/json" \
  -d '[
    {
      "ProdId": 1,
      "ProdName": "Sample Product",
      "ProdNum": "SP-001",
      "ProdBrandName": "Brand A",
      "ProdCatgName": "Electronics",
      "Qty": 100,
      "SellingPrice": 99.99,
      "Currency": "HKD"
    }
  ]' | jq

# Clear vector store
curl -X DELETE http://localhost:3030/api/vector-store/clear | jq
```

## Conversation Management

```bash
# Get conversation stats
curl http://localhost:3030/api/conversations/stats | jq

# Expected response:
# {
#   "total_conversations": 2,
#   "conversation_ids": ["session-1", "session-2"],
#   "messages_per_conversation": {...}
# }

# Clear specific conversation
curl -X DELETE http://localhost:3030/api/conversations/test-session-1 | jq
```

## Ollama Test

```bash
# Test Ollama connection
curl http://localhost:3030/api/ollama/test | jq

# Expected response:
# {
#   "success": true,
#   "ollama_host": "http://localhost:11434",
#   "model": "qwen2.5:0.5b",
#   "response": "Hello! This is a test...",
#   "message": "Ollama LLM is working correctly!"
# }
```

## Rate Limiting Test

```bash
# Send multiple requests to trigger rate limiting
for i in {1..15}; do
  echo "Request $i:"
  curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" \
    -X POST http://localhost:3030/api/chat \
    -H "Content-Type: application/json" \
    -d "{\"message\": \"Test message $i\"}"
done

# After 10 requests, you should see HTTP 429 (Too Many Requests)
```

## WebSocket-style Continuous Chat (Bash)

```bash
# Simulate a conversation
CONV_ID="demo-$(date +%s)"

echo "Starting conversation: $CONV_ID"

# First message
curl -s -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What products are available?\", \"conversation_id\": \"$CONV_ID\"}" | jq '.response'

# Follow-up message (with history)
curl -s -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"Tell me more about the first one\", \"conversation_id\": \"$CONV_ID\", \"include_history\": true}" | jq '.response'

# Another follow-up
curl -s -X POST http://localhost:3030/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is the price?\", \"conversation_id\": \"$CONV_ID\", \"include_history\": true}" | jq '.response'
```

## Python Example

```python
import requests

BASE_URL = "http://localhost:3030"

# Check health
health = requests.get(f"{BASE_URL}/health")
print(f"Health: {health.json()}")

# Load products
products = requests.get(f"{BASE_URL}/api/products")
print(f"Products loaded: {products.json()}")

# Start conversation
conversation_id = "python-test-1"

# First message
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "What products do you have?",
        "conversation_id": conversation_id
    }
)
print(f"Response: {response.json()['response']}")

# Follow-up with history
response = requests.post(
    f"{BASE_URL}/api/chat",
    json={
        "message": "Tell me more about them",
        "conversation_id": conversation_id,
        "include_history": True,
        "history_limit": 5
    }
)
print(f"Follow-up: {response.json()['response']}")
```

## Node.js Example

```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:3030';

async function testChatAgent() {
  // Check health
  const health = await axios.get(`${BASE_URL}/health`);
  console.log('Health:', health.data);

  // Load products
  const products = await axios.get(`${BASE_URL}/api/products`);
  console.log('Products:', products.data);

  // Start conversation
  const conversationId = 'nodejs-test-1';

  // First message
  const response1 = await axios.post(`${BASE_URL}/api/chat`, {
    message: 'What products do you have?',
    conversation_id: conversationId
  });
  console.log('Response:', response1.data.response);

  // Follow-up with history
  const response2 = await axios.post(`${BASE_URL}/api/chat`, {
    message: 'Tell me more about them',
    conversation_id: conversationId,
    include_history: true,
    history_limit: 5
  });
  console.log('Follow-up:', response2.data.response);
}

testChatAgent().catch(console.error);
```
