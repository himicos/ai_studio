**Technical Prompt for UX/UI Design: AI Studio System Web Interface**

**Objective:** Design a modern, intuitive, and powerful web interface for an AI Studio system that simplifies complex operations and enhances user experience through thoughtful UX/UI decisions.

---

### Core Components & Design Decisions:

#### 1. Navigation & Layout:
- **Floating Sidebar:** Implement a collapsible sidebar that provides seamless access to core features. Ensure it supports both text labels and icons for quick recognition.
- **Theme Toggle:** Integrate a prominently placed dark/light theme toggle, enabling users to switch themes effortlessly.
- **System Status Indicators:** Display real-time system status indicators using color codes and icons to communicate system health at a glance.
- **Breadcrumb Navigation:** Design a breadcrumb trail for users to easily track and navigate deep analysis paths, enhancing user orientation.

#### 2. Proxy Management Dashboard:
- **Proxy Visualization:** Develop a world map visualization for live proxy rotation. Use animated markers to represent active proxies.
- **Health Metrics:** Display latency and success rate through intuitive graphs and color-coded indicators for each proxy.
- **Quick Switching Interface:** Implement a dropdown or toggle switch for fast proxy changes, ensuring minimal disruption.
- **Proxy Pool Management:** Provide an interface for adding/removing proxies, with immediate updates to the map.
- **Connection Status:** Use real-time indicators to show proxy connection status, reinforcing system reliability.

#### 3. Prompt Laboratory:
- **Multi-Tab Workspace:** Design a tabbed interface for simultaneous prompt editing, allowing users to switch contexts easily.
- **Split View:** Create a split view layout showing the original prompt, generated variations, and the selected final version for easy comparison.
- **Prompt History:** Visualize prompt history with branching paths, enabling users to trace development and iteration.
- **Scoring & Testing:** Integrate a scoring system for prompt effectiveness and an A/B testing interface for evaluating variations.

#### 4. Analytics Center:
- **Real-Time Tracking:** Implement dynamic graphs for whale movement and transaction volumes with updates via WebSockets.
- **Sentiment Analysis:** Design a dashboard with sentiment trends and insights, using visual cues like heatmaps.
- **Pattern Recognition:** Provide visualizations for pattern recognition, making complex data more digestible.
- **Alert Configuration:** Allow users to configure custom alerts with an intuitive interface, including threshold settings.

#### 5. Memory Management:
- **Knowledge Graph:** Develop a visual knowledge graph of stored insights with interactive nodes that expand on click.
- **Filtering & Search:** Implement category-based filtering and natural language search capabilities for efficient data retrieval.
- **Relationship Visualization:** Show relationships between insights with connecting lines and expandable detail panels.
- **Data Management:** Include export/import functionality to facilitate data handling across systems.

#### 6. Interactive Features:
- **Drag-and-Drop Builder:** Enable users to construct prompts using drag-and-drop building blocks, promoting creativity and efficiency.
- **Collaboration Tools:** Incorporate real-time collaboration features for teamwork, with version control and user annotations.
- **Webhook & API Configuration:** Design interfaces for custom webhook setups and API key management, emphasizing security and ease of use.
- **System Monitoring:** Provide a dashboard for system health monitoring, with expandable details for in-depth analysis.

---

### Design Notes:
- **Card-Based Layout:** Use modular card designs for content organization, allowing for flexible layout adjustments and responsive design.
- **Smooth Transitions:** Implement CSS transitions for smooth view changes, enhancing the overall user experience.
- **Keyboard Shortcuts:** Develop a set of keyboard shortcuts for power users to navigate and perform actions quickly.
- **Mobile Responsiveness:** Ensure the interface is fully responsive, adapting to various screen sizes and orientations.

### Technical Requirements:
- **Real-Time Updates:** Utilize WebSocket integration for live data updates and interactions.
- **User Preferences:** Store user preferences in local storage for a personalized experience.
- **REST API Endpoints:** Develop REST API endpoints for all major functions, ensuring platform interoperability.
- **Authentication & Access:** Implement a robust authentication system with role-based access controls for security.
- **Rate Limiting:** Implement rate limiting and quota management to ensure system stability and performance.

**Focus:** Create an intuitive interface that simplifies complex operations, making them feel natural and accessible to users of all skill levels.
