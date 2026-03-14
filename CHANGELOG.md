# Changelog

All notable changes to SBN ChatAgent will be documented in this file.

## [1.1.0] - 2026-03-15

### Added
- **Logging Configuration**: Rotating file handlers with structured logging
- **Conversation History**: Multi-turn conversation support with context awareness
- **Input Validation**: Comprehensive validation and sanitization for all user inputs
- **Rate Limiting**: Protection against abuse (10 requests per 60 seconds per IP)
- **Configuration Management**: Centralized settings using pydantic-settings
- **Unit Tests**: Test suite for validators and conversation manager
- **Health Checks**: Docker health checks and improved health endpoint
- **Frontend Improvements**: Real-time connection status, rate limit warnings, error handling

### Changed
- **RAG Prompt**: Enhanced with 8 specific instructions for better product queries
- **LLM Settings**: Lower temperature (0.3) for more factual responses
- **Docker Security**: Running as non-root user (appuser)
- **Documentation**: Comprehensive README and API examples

### Improved
- Error handling with detailed logging
- Input sanitization to prevent injection attacks
- Frontend UX with loading states and visual feedback
- Docker configuration with proper volume mounts

## [1.0.0] - 2026-03-14

### Added
- Initial release
- FastAPI backend with RAG integration
- Ollama LLM integration (Qwen2.5:0.5b)
- ChromaDB vector store for product knowledge
- Basic chat UI
- Docker support
- Internal API integration for product catalog
