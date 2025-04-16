# SpyderWeb AI Studio: Visual Memory System Roadmap

This roadmap outlines our strategic plan for enhancing the visual memory system in SpyderWeb AI Studio, focusing on high-impact, low-effort improvements that will exponentially increase the platform's capabilities.

## Core Philosophy

**100x Impact with 1x Effort**: Leverage existing vector memory, semantic search, and agent infrastructure to create intelligent visualizations that transform how users interact with knowledge.

## Feature Roadmap

### Current Focus: Phase 4 Prerequisite

#### 7. Actionable Nodes [CURRENT FOCUS]
- **Priority**: Highest
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

### Phase 1: Foundation Enhancements

#### 1. Live Semantic Query Highlighting
- **Priority**: High
- **Effort**: Low (1x)
- **Impact**: 30x UX, 10x search capability
- **Description**: Highlight relevant nodes and paths based on cosine similarity when users enter a question or term
- **Implementation**:
  - Add query input field to graph container
  - Use existing `searchMemoryNodes()` function with similarity threshold
  - Apply color gradient to nodes based on similarity score
  - Highlight connecting paths between highly similar nodes
  - Add visual legend for similarity scale

#### 2. Memory Weight / Attention Encoding [Backend Complete]
- **Priority**: High
- **Effort**: Low (1x) -> Low (0.5x Frontend/Logic Remaining)
- **Impact**: 25x visibility into system focus
- **Description**: Vary node/edge size or opacity based on importance, recent activation, or frequency of use. Backend endpoint `/nodes/weights` implemented.
- **Implementation**:
  - Extend memory node schema with `activation_score` and `last_accessed` fields (Done via metadata)
  - Create node sizing function based on these metrics (`calculateNodeSize` in frontend - Needs Connection)
  - Implement tracking logic in `/nodes/track-access` endpoint
  - Implement decay function for activation over time (Optional V2)
  - Add toggle for different sizing metrics (frequency, recency, importance)

### Phase 2: Interaction & Debugging

#### 3. Agent Trace Mode (Replay Reasoning)
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

#### 4. Prompt-Context Linking
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

#### 5. Modular Tag Clustering
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

#### 6. Memory Mode Toggle
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

#### 8. Graph AI Copilot
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
- **Actionable Nodes**: Target completion in the next 1-2 weeks.

### Quick Wins (Next 2 Weeks - Post Actionable Nodes)
- Finish Memory Weight / Attention Encoding (Frontend/Logic)
- Live Semantic Query Highlighting

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

1. Ensure vector embedding consistency across all node types (Addressed by FAISS migration)
2. Create unified node access tracking system (Partially done with `/track-access` endpoint)
3. Standardize metadata schema for all memory objects (Ongoing)
4. Implement efficient graph rendering optimizations for larger datasets (Ongoing)
5. Develop consistent interaction patterns for graph elements (Key for Actionable Nodes)

## Success Metrics

- **Graph Engagement**: Time spent interacting with visual memory
- **Action Efficiency**: Reduction in clicks/time to perform tasks via Actionable Nodes
- **Agent Effectiveness**: Reduction in steps needed to complete tasks
- **User Comprehension**: Ability to explain agent reasoning and connections
- **Development Velocity**: Speed of implementing new features using the enhanced system
- **Knowledge Quality**: Measured improvement in content generation using graph-derived context

## System Efficiency Enhancements

### 1. Vector Database Migration (SQLite → FAISS) [Largely Complete]
- **Priority**: High -> Completed
- **Effort**: Medium (2x) -> Done
- **Impact**: 50x query speed, 25x scalability
- **Description**: Replace SQLite-based vector storage with dedicated vector database (FAISS). Includes adapter layer (`vector_adapter.py`), store manager (`VectorStoreManager`), and migration script (`migrate_to_faiss.py`). Enhanced `db_enhanced.py`.
- **Implementation**:
  - Integrate FAISS as primary vector storage (Done)
  - Migrate existing embeddings from SQLite to vector DB (Script created, needs final run/validation)
  - Update semantic search interface to leverage vector DB capabilities (Done via adapter)
  - Replace memory node access logic for faster retrieval (Done via adapter)
  - Add index optimization for different query patterns (Future refinement)

### 2. Model Routing System
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

### 3. Token Cost Tracking
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

### 4. Memory Pruning Logic
- **Priority**: Medium
- **Effort**: Medium (1.5x)
- **Impact**: 35x memory efficiency, 20x relevance improvement
- **Description**: Automated management of vector database size and quality through relevance-based pruning
- **Implementation**:
  - Implement timestamp-based decay scoring
  - Add relevance thresholds for retention decisions
  - Create pruning scheduler to run at predefined intervals
  - Develop manual pruning interface in UI
  - Add backup mechanism for pruned but potentially useful nodes

### 5. Document Ingestion Pipeline
- **Priority**: High
- **Effort**: Medium (2x)
- **Impact**: 40x knowledge depth, 25x research capability
- **Description**: Expand ingestion capabilities beyond social media to include documents, web pages, and video transcripts
- **Implementation**:
  - Develop PDF parsing and chunking utilities
  - Create HTML scraping and cleaning pipeline
  - Add YouTube transcript extraction module
  - Implement content-type detection for appropriate processing
  - Build UI components for direct document upload

### 6. Self-Learning Feedback Loop (Bonus)
- **Priority**: Medium
- **Effort**: High (3x)
- **Impact**: 70x system intelligence, 45x autonomous improvement
- **Description**: Enable the system to evaluate and improve its own operations through continuous feedback
- **Implementation**:
  - Implement batch summarization of related content
  - Create embedding quality comparison framework
  - Add metrics collection for summary effectiveness
  - Develop automated agent improvement based on performance data
  - Build visualization tools to track system evolution

## Next Asymmetrical Execution Opportunity [Updated Focus]

### Actionable Nodes: The Interactive Workspace
With the FAISS vector database migration largely complete and providing a high-performance foundation, the next highest leverage opportunity is **Actionable Nodes**. This feature transforms the graph from a passive view into an active control surface.

#### Why This Is Asymmetrical Now (High Impact / Manageable Effort):
- **Foundation Ready**: Leverages the stable FAISS backend, reliable agents (Twitter/Reddit), and existing API endpoints (summarization, search).
- **Direct User Value**: Immediately makes the graph more useful and reduces context switching.
- **Synergy**: Combines visualization with operational capabilities, embodying the "AI Studio" concept.
- **Enables Next Steps**: Provides a natural interface for triggering more complex workflows like the Graph AI Copilot later.

#### Expected Outcomes:
- **Performance**: Faster task execution by initiating actions directly from graph context.
- **UX**: Significantly reduced clicks and navigation required for common operations.
- **Integration**: Tighter coupling between visual memory exploration and agent/tool execution.
- **Development**: Establishes UI patterns for direct graph interaction.

#### Getting Started (Next 1-2 Weeks):
1.  **Design Context Menu (Day 1)**
    - Define standard actions (Summarize, Find Similar, Delete?)
    - Define type-specific actions (e.g., "View Original Tweet/Post", "Generate Reply")
    - Sketch UI look and feel.
2.  **Implement Frontend Menu Component (Day 2-4)**
    - Use a library (e.g., react-contextmenu) or build custom.
    - Trigger menu on node right-click.
    - Pass node ID and type to menu actions.
3.  **Connect Actions to APIs (Day 5-8)**
    - Wire menu options to call relevant backend endpoints (`/api/summary/`, `/api/memory/semantic-search`, agent endpoints).
    - Handle API responses (e.g., display summary, highlight similar nodes).
4.  **Add Visual Feedback (Day 9-10)**
    - Show loading indicators during action execution.
    - Provide confirmation messages (e.g., "Summary generated").
5.  **Testing & Refinement (Day 11-14)**
    - Test across different node types.
    - Ensure smooth user experience.
    - Gather feedback.

This shifts our immediate focus to delivering a core interactive enhancement, building directly on the performance gains from the FAISS migration. 