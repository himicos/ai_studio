# SpyderWeb AI Studio: Visual Memory System Roadmap

This roadmap outlines our strategic plan for enhancing the visual memory system in SpyderWeb AI Studio, focusing on high-impact, low-effort improvements that will exponentially increase the platform's capabilities.

## Core Philosophy

**100x Impact with 1x Effort**: Leverage existing vector memory, semantic search, and agent infrastructure to create intelligent visualizations that transform how users interact with knowledge.

## Feature Roadmap

### Current Focus: System Foundation

#### 1. Live Semantic Query Highlighting [✅ IMPLEMENTED]
- **Priority**: High
- **Effort**: Low (1x)
- **Impact**: 30x UX, 10x search capability
- **Description**: Highlight relevant nodes and paths based on cosine similarity when users enter a question or term
- **Implementation**:
  - ✅ Add query input field to graph container
  - ✅ Use existing `searchMemoryNodes()` function with similarity threshold
  - ✅ Apply color gradient to nodes based on similarity score
  - ✅ Highlight connecting paths between highly similar nodes
  - ✅ Add visual legend for similarity scale
- **Status**: 
  - ✅ Basic implementation completed with node highlighting
  - ✅ Enhanced zooming to focus on relevant nodes
  - ✅ Color-coding based on similarity scores
  - ⚠️ Minor linter errors being addressed

#### 2. Memory Weight / Attention Encoding [Frontend Remaining]
- **Priority**: High
- **Effort**: Low (0.5x Frontend/Logic Remaining)
- **Impact**: 25x visibility into system focus
- **Description**: Vary node/edge size or opacity based on importance, recent activation, or frequency of use. Backend endpoint `/nodes/weights` implemented.
- **Implementation**:
  - ✅ Backend endpoint is implemented and functional
  - Connect frontend to backend endpoint
  - Create node sizing function based on metadata
  - Implement tracking logic in `/nodes/track-access` endpoint
  - Add toggle for different sizing metrics (frequency, recency, importance)

### Phase 1: Foundation Enhancements

#### 3. Self-Improvement Loop [✅ IMPLEMENTED]
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 50x system evolution
- **Description**: System that continuously improves itself by monitoring execution logs, generating critiques, and implementing safe refactors
- **Implementation**:
  - ✅ Create execution logging infrastructure with database table
  - ✅ Implement function decorator for easy tracking integration
  - ✅ Build Critic Agent for analyzing logs and generating insights
  - ✅ Create Refactor Agent to implement safe improvements
  - ✅ Add scheduler to run analysis at regular intervals
- **Status**:
  - ✅ Basic implementation complete
  - ✅ All agents operational with database integration
  - ⚠️ Gathering execution data for first round of improvements

#### 4. Actionable Nodes
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 40x operational speed
- **Description**: Add context menu to nodes with actions like "Summarize," "Generate post," "Find similar," "Execute agent". Transforms the graph into an active workspace.
- **Implementation**:
  - Create right-click context menu component
  - Define standard action set for all node types
  - Implement node-type-specific actions
  - Connect actions to existing API endpoints (summarization, search, agents)
  - Add visual feedback for action execution
  - Create action history panel (optional V2)

### Phase 2: Interaction & Debugging

#### 5. Agent Trace Mode (Replay Reasoning)
- **Priority**: Medium
- **Effort**: Low (1x)
- **Impact**: 20x debugging/understanding
- **Description**: Visually replay the path of nodes an agent followed or created during a task
- **Implementation**:
  - Create trace logger middleware for memory access
  - Store sequence of node accesses with timestamps
  - Add timeline slider component to replay traces
  - Implement animation of highlighted paths with sequenced timing
  - Add export option for trace data

#### 6. Prompt-Context Linking
- **Priority**: Medium
- **Effort**: Low (1x)
- **Impact**: 15x prompt quality improvement
- **Description**: Visualize which memory nodes are injected into which prompts as context
- **Implementation**:
  - Store prompt metadata with references to memory nodes used
  - Create bidirectional links in graph between prompts and context nodes
  - Add special visual treatment for prompt nodes
  - Implement filter to show only context used in specific prompts
  - Create hover state showing prompt text using the node

### Phase 3: Organization & Navigation

#### 7. Modular Tag Clustering
- **Priority**: Medium
- **Effort**: Low (1x)
- **Impact**: 25x clarity and organization
- **Description**: Group nodes by user-defined or auto-tagged topics for better organization
- **Implementation**:
  - Use existing keyword extraction to generate cluster tags
  - Implement force-directed clustering algorithm based on tags
  - Add UI controls for manual tag creation and assignment
  - Create collapsible/expandable tag groups
  - Add tag-based filtering options

#### 8. Memory Mode Toggle
- **Priority**: Medium
- **Effort**: Low (1x)
- **Impact**: 15x insight through multiple perspectives
- **Description**: Toggle between different visualization modes (time-based, importance, project-specific)
- **Implementation**:
  - Create mode selector in graph controls
  - Implement chronological layout algorithm
  - Add importance-weighted layout option
  - Create project/workspace filter with saved configurations
  - Ensure smooth transitions between modes

### Phase 4: Advanced Interactions

#### 9. Graph AI Copilot
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 100x interface power
- **Description**: Integrated AI assistant that works directly within the graph visualization
- **Implementation**:
  - Add chat input component to graph panel
  - Connect to existing LLM integration
  - Implement response visualization that highlights relevant nodes
  - Create ability for copilot to generate new nodes and connections
  - Add option to accept/reject proposed changes
  - Implement specialized graph-based prompts

## Implementation Strategy

### Current Focus
- **Nitter Self-Hosting & Configuration:** Set up local Nitter, update code to use configurable URL.
- **Memory Weight Frontend Integration**: Finish connecting frontend to the backend implementation.
- **Actionable Nodes**: Begin implementation of context menu functionality.

### Quick Wins (Next 2 Weeks)
- Knowledge Graph UI Fixes
- Self-Improvement Loop Enhancement (based on initial data)

### Short-Term (1 Month)
- Agent Trace Mode
- Prompt-Context Linking

### Mid-Term (2-3 Months)
- Modular Tag Clustering
- Memory Mode Toggle

### Long-Term (3-6 Months)
- Graph AI Copilot
- Model Routing System
- Token Cost Tracking
- Memory Pruning Logic
- Document Ingestion Pipeline

## Technical Dependencies

1. ✅ Ensure vector embedding consistency across all node types (Addressed by FAISS migration)
2. ✅ Create unified database configuration (Addressed by database unification)
3. ⚠️ Create unified node access tracking system (Partially done with `/track-access` endpoint)
4. ⚠️ Standardize metadata schema for all memory objects (Ongoing)
5. ⚠️ Implement efficient graph rendering optimizations for larger datasets (Ongoing)
6. ⚠️ Develop consistent interaction patterns for graph elements (Key for Actionable Nodes)
7. ⚠️ **Configure Twitter Data Source:** Implement configurable URL for self-hosted Nitter, allowing flexibility for future API integration.

## Success Metrics

- **Graph Engagement**: Time spent interacting with visual memory
- **Action Efficiency**: Reduction in clicks/time to perform tasks via Actionable Nodes
- **Agent Effectiveness**: Reduction in steps needed to complete tasks
- **User Comprehension**: Ability to explain agent reasoning and connections
- **Development Velocity**: Speed of implementing new features using the enhanced system
- **Knowledge Quality**: Measured improvement in content generation using graph-derived context
- **Self-Improvement**: Rate of successful auto-refactors and system optimizations

## System Efficiency Enhancements

### 0. Nitter Self-Hosting Configuration [✅ Completed]
- **Priority**: Critical (for Twitter Agent reliability)
- **Effort**: Low (0.5x) + Troubleshooting (1.5x)
- **Impact**: Ensures reliable Twitter data ingestion, prerequisite for Twitter-related features.
- **Description**: Set up a local Nitter instance and modify `ai_studio_package/data/browser_manager.py` to use a configurable base URL (e.g., via environment variable) instead of the hardcoded `nitter.net`. This provides stability and allows for future integration of the official Twitter API if desired.
- **Status**: Completed. Nitter service running via Docker Compose, app connects successfully. (Requires session tokens for live data).

### 1. Vector Database Migration (SQLite → FAISS) [✅ Completed]
- **Priority**: High
- **Effort**: Medium (2x) 
- **Impact**: 50x query speed, 25x scalability
- **Description**: Replace SQLite-based vector storage with dedicated vector database (FAISS). Includes adapter layer (`vector_adapter.py`), store manager (`VectorStoreManager`), and migration script (`migrate_to_faiss.py`).
- **Status**: 
  - ✅ FAISS integration as primary vector storage
  - ✅ Migration script created and tested
  - ✅ Semantic search interface updated to leverage FAISS
  - ✅ Database unification completed 
  - ✅ Embedding pipeline fixed for all content types

### 2. Self-Improvement Loop [✅ Implemented]
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 50x system evolution
- **Description**: System that monitors its own performance and makes targeted improvements over time
- **Status**:
  - ✅ Execution logging infrastructure implemented
  - ✅ Critic Agent implemented to analyze logs
  - ✅ Refactor Agent created to implement safe improvements
  - ✅ Scheduled analysis of system performance
  - ⚠️ Gathering initial execution data

### 3. Model Routing System
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 30x cost efficiency, 15x processing speed
- **Description**: Intelligent routing between local GPU models and cloud API models based on task complexity and requirements
- **Implementation**:
  - Classify task complexity via metadata analysis
  - Define routing rules based on model cost/performance ratio
  - Add token usage predictor to estimate costs before execution
  - Create model scoring layer to track quality-to-token ratio
  - Implement UI override for testing and development

### 4. Token Cost Tracking
- **Priority**: Medium
- **Effort**: Low (1x)
- **Impact**: 20x cost visibility, 10x optimization opportunity
- **Description**: Comprehensive tracking of token usage and associated costs across all LLM operations
- **Implementation**:
  - Add token logger module to all OpenAI API calls
  - Create storage schema for token/cost usage per task
  - Implement API endpoints for token statistics retrieval
  - Develop alerting system for high-cost behaviors
  - Add dashboard visualizations for cost trends

### 5. Memory Pruning Logic
- **Priority**: Medium
- **Effort**: Medium (1.5x)
- **Impact**: 20x memory efficiency, 10x reducing noise
- **Description**: Automatically identify and archive or remove low-value memory nodes based on usage patterns and importance
- **Implementation**:
  - Create value scoring algorithm based on node metrics (age, usage, connectedness)
  - Add pruning threshold configuration options
  - Implement 3-tier storage strategy (active, archive, delete)
  - Create archive browsing interface in UI
  - Add manual override for node value scores

### 6. Document Ingestion Pipeline
- **Priority**: Medium
- **Effort**: Medium (2x)
- **Impact**: 30x knowledge diversity, 15x setup efficiency
- **Description**: Add support for ingesting and processing PDFs, web pages, and other document formats
- **Implementation**:
  - Create document parsing modules for common formats
  - Implement chunking logic for large documents
  - Design custom embedding strategy for document sections
  - Add document-specific metadata schema
  - Create document upload/URL input UI
  - Implement progress tracking for large ingestion jobs 