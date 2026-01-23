# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-24

### Initial Release

Crebit Studio v0.1.0 - AI-powered creative content generation platform.

### Added

#### Core Platform
- **13 Dimension Apps**: Complete suite of AI creative tools
  - 1D (Prompt Generator) - AI prompt engineering
  - 2D (Story Architect) - Narrative structure design
  - 3D (Visual Realizer) - Image generation
  - 4D (Reference Decoder) - Video reference analysis with style library
  - Abyss Mirror - Creative reflection and analysis
  - Aesthetic Director - Visual style guidance
  - Character Consistency - Character design coherence
  - Prompt Alchemy - Advanced prompt transformation
  - Quality Director - Output quality assessment
  - Sound Crafter - Audio design
  - Storyboard Sketcher - Visual storyboard creation
  - Video Maker (Veo) - AI video generation
  - Suno/Kling Integration - External AI service connectors

#### Multi-RAG System
- **Tier0 (NotebookLM CDP)**: Master knowledge base integration
- **Tier1 (Qdrant + BM25)**: Hybrid vector search with sparse embeddings
- Auteur-style RAG presets (Bong Joon-ho, Kubrick, Fincher, etc.)
- Evidence-based attribution system with `evidence_refs`

#### Security & Reliability
- P0 Security Hardening: Input sanitization, attribution-gated prompting
- Sealed Capsule principle: All LLM calls server-side
- Run-Token credit management (issue → execute → deduct/refund)

#### Infrastructure
- OpenTelemetry integration for observability
- GraphQL gateway with DataLoaders
- SSE streaming for real-time updates
- Redis caching layer

### Technical Stack
- **Frontend**: Next.js 16, React 19, TypeScript, Tailwind CSS
- **Backend**: FastAPI, Python 3.11, SQLAlchemy 2.0 async
- **Database**: PostgreSQL 16, Qdrant, Redis
- **AI**: Google Gemini API, Veo, Suno, Kling

### Tests
- 3,783 backend tests passing
- 60%+ code coverage
- E2E tests with Playwright

### Documentation
- Comprehensive API documentation
- Dimension App Developer Guide
- Architecture Evolution Codex

---

[0.1.0]: https://github.com/crebit/vivid/releases/tag/v0.1.0
