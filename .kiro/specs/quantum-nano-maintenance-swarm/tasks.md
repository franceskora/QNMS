# Implementation Plan: Quantum-Nano Maintenance Swarm (QNMS)

## Overview

This implementation plan breaks down the QNMS system into incremental, manageable steps. We start with infrastructure setup and a basic FastAPI application, then progressively add Gemini integration, Isaac Sim communication, safety validation, and swarm coordination. Each step builds on the previous one, ensuring continuous integration and validation.

## Tasks

- [ ] 1. Set up Vultr infrastructure and project foundation
  - Create Vultr compute instance with Python 3.11+
  - Set up SSH access and firewall rules (ports 80, 443, 8000 for FastAPI)
  - Install system dependencies (Python, pip, git)
  - Create project directory structure: `qnms/` with subdirectories `api/`, `core/`, `integrations/`, `tests/`
  - Initialize git repository and create `.gitignore` for Python
  - Create `requirements.txt` with initial dependencies: fastapi, uvicorn, pydantic, python-dotenv
  - Set up virtual environment and install dependencies
  - _Requirements: 1.1, 1.2_

- [ ] 2. Create FastAPI "Hello World" with health check endpoint
  - [ ] 2.1 Implement basic FastAPI application structure
    - Create `api/main.py` with FastAPI app instance
    - Implement `/health` endpoint that returns `{"status": "healthy", "timestamp": "..."}`
    - Configure Uvicorn server with WebSocket support
    - Add CORS middleware for cross-origin requests
    - _Requirements: 1.1, 1.3_
  
  - [ ]* 2.2 Write unit tests for health check endpoint
    - Test health endpoint returns 200 status
    - Test response contains required fields
    - _Requirements: 1.1, 1.3_

- [ ] 3. Integrate Gemini 1.5 Pro API
  - [ ] 3.1 Create Gemini client module
    - Create `integrations/gemini_client.py`
    - Implement `GeminiClient` class with async API calls
    - Add API key configuration via environment variables
    - Implement prompt formatting for defect data
    - Implement JSON response parsing and error handling
    - Add retry logic with exponential backoff for API failures
    - _Requirements: 3.1, 3.2, 3.6_
  
  - [ ] 3.2 Create test endpoint for Gemini integration
    - Add `/test/gemini` endpoint that sends sample defect data to Gemini
    - Return the generated repair path as JSON response
    - Log all Gemini API calls with correlation IDs
    - _Requirements: 3.1, 3.2_
  
  - [ ]* 3.3 Write unit tests for Gemini client
    - Test prompt formatting with sample defect data
    - Test JSON parsing with valid and malformed responses
    - Test error handling for API failures
    - _Requirements: 3.1, 3.2, 3.6_

- [ ] 4. Checkpoint - Verify Gemini integration works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 5. Implement core data models with Pydantic
  - [ ] 5.1 Create data model definitions
    - Create `core/models.py`
    - Implement `SensorCoordinate` model with validation (0.1nm precision, bounds checking)
    - Implement `CoordinateCommand` model with grid alignment validation
    - Implement `RepairPath` model
    - Implement `DefectRecord` model
    - Implement `SwarmAgentState` model
    - Implement `SystemMetrics` model
    - Add custom validators for precision and bounds
    - _Requirements: 2.1, 2.2, 6.3_
  
  - [ ]* 5.2 Write property test for coordinate precision validation
    - **Property 1: Coordinate Precision Validation**
    - **Validates: Requirements 2.1, 2.2**
  
  - [ ]* 5.3 Write property test for invalid input rejection
    - **Property 2: Invalid Input Rejection**
    - **Validates: Requirements 2.3**
  
  - [ ]* 5.4 Write property test for atomic grid alignment
    - **Property 14: Atomic Grid Alignment**
    - **Validates: Requirements 6.3**

- [ ] 6. Implement data validation and safety checks
  - [ ] 6.1 Create validation module
    - Create `core/validator.py`
    - Implement `ThermalSafetyValidator` class (120°C limit check)
    - Implement `StructuralSafetyValidator` class (no-go zone checking)
    - Implement `AtomicPrecisionValidator` class (0.1nm grid alignment)
    - Implement `CollisionDetector` class (0.5nm minimum separation)
    - Implement `YieldProtectionLogic` class (mark unrepairable defects)
    - Add configuration for no-go zones (loaded from config file)
    - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ]* 6.2 Write property test for thermal safety constraint
    - **Property 12: Thermal Safety Constraint**
    - **Validates: Requirements 6.1**
  
  - [ ]* 6.3 Write property test for no-go zone avoidance
    - **Property 13: No-Go Zone Avoidance**
    - **Validates: Requirements 6.2**
  
  - [ ]* 6.4 Write property test for collision prevention
    - **Property 15: Collision Prevention**
    - **Validates: Requirements 6.4**
  
  - [ ]* 6.5 Write property test for unrepairable defect marking
    - **Property 16: Unrepairable Defect Marking**
    - **Validates: Requirements 6.5**

- [ ] 7. Implement logging and monitoring infrastructure
  - [ ] 7.1 Set up structured logging
    - Create `core/logging_config.py`
    - Configure Python logging with JSON formatter
    - Add correlation ID middleware for FastAPI
    - Implement log entry creation for all operations
    - _Requirements: 1.4, 7.2_
  
  - [ ] 7.2 Implement monitoring service
    - Create `core/monitoring.py`
    - Implement `SystemMetrics` tracking class
    - Add Prometheus metrics endpoint at `/metrics`
    - Track counters: defects detected, repaired, failed, unrepairable
    - Track gauges: active agents, connection status
    - Track histograms: repair latency, API latency
    - _Requirements: 7.1, 7.3, 7.4, 7.5_
  
  - [ ]* 7.3 Write property test for comprehensive operation logging
    - **Property 3: Comprehensive Operation Logging**
    - **Validates: Requirements 1.4, 7.2**
  
  - [ ]* 7.4 Write property test for metrics tracking
    - **Property 17: Metrics Tracking**
    - **Validates: Requirements 7.3, 7.4**

- [ ] 8. Checkpoint - Verify validation and monitoring work
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 9. Implement command queue system
  - [ ] 9.1 Create command queue module
    - Create `core/queue.py`
    - Implement thread-safe `CommandQueue` class using `asyncio.Queue`
    - Add priority queue support (severity-based ordering)
    - Implement command status tracking (pending, in-progress, completed, failed)
    - Add command deduplication logic
    - Implement queue statistics (size, throughput)
    - _Requirements: 2.4, 4.4, 8.3_
  
  - [ ]* 9.2 Write property test for command status tracking
    - **Property 9: Command Status Tracking**
    - **Validates: Requirements 4.4, 4.5**
  
  - [ ]* 9.3 Write property test for command queue assignment
    - **Property 20: Command Queue Assignment**
    - **Validates: Requirements 8.3**

- [ ] 10. Implement Isaac Sim WebSocket integration
  - [ ] 10.1 Create Isaac Sim client module
    - Create `integrations/isaac_client.py`
    - Implement `IsaacSimClient` class with WebSocket connection management
    - Implement connection handshake protocol
    - Implement message serialization/deserialization (JSON format)
    - Add heartbeat/ping-pong mechanism (10s interval)
    - Implement message acknowledgment protocol
    - Add command buffering during connection interruptions
    - Implement exponential backoff reconnection logic
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 1.5_
  
  - [ ] 10.2 Create WebSocket endpoint in FastAPI
    - Add `/ws/isaac` WebSocket endpoint in `api/main.py`
    - Handle incoming sensor data messages
    - Handle outgoing command messages
    - Handle acknowledgment messages
    - Add connection state tracking
    - _Requirements: 5.1, 5.2, 5.3_
  
  - [ ]* 10.3 Write property test for exponential backoff reconnection
    - **Property 4: Exponential Backoff Reconnection**
    - **Validates: Requirements 1.5**
  
  - [ ]* 10.4 Write property test for connection buffering and retry
    - **Property 10: Connection Buffering and Retry**
    - **Validates: Requirements 5.4**
  
  - [ ]* 10.5 Write property test for message acknowledgment
    - **Property 11: Message Acknowledgment**
    - **Validates: Requirements 5.5**
  
  - [ ]* 10.6 Write unit tests for WebSocket communication
    - Test handshake protocol
    - Test bidirectional message flow
    - Test connection interruption handling
    - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 11. Implement end-to-end data flow pipeline
  - [ ] 11.1 Create connection manager
    - Create `core/connections.py`
    - Implement `ConnectionManager` class
    - Manage WebSocket connection to Isaac Sim
    - Manage HTTP client for Gemini API
    - Track connection health and status
    - Implement circuit breaker pattern for external services
    - _Requirements: 1.2, 1.5_
  
  - [ ] 11.2 Implement sensor data ingestion endpoint
    - Add `/api/sensor-data` POST endpoint
    - Validate incoming sensor coordinates
    - Queue valid coordinates for processing
    - Return acknowledgment within 50ms
    - Log all received data with correlation IDs
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_
  
  - [ ] 11.3 Implement repair path processing pipeline
    - Create background task to process queued sensor coordinates
    - Send coordinates to Gemini for path planning
    - Validate generated repair paths against safety constraints
    - Convert repair paths to coordinate commands
    - Queue commands for distribution to swarm agents
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 4.1_
  
  - [ ]* 11.4 Write property test for data flow pipeline integrity
    - **Property 5: Data Flow Pipeline Integrity**
    - **Validates: Requirements 2.4, 3.1, 4.1, 4.2**
  
  - [ ]* 11.5 Write property test for repair path structure validity
    - **Property 6: Repair Path Structure Validity**
    - **Validates: Requirements 3.2, 4.3**
  
  - [ ]* 11.6 Write property test for severity-based prioritization
    - **Property 7: Severity-Based Prioritization**
    - **Validates: Requirements 3.4**
  
  - [ ]* 11.7 Write property test for path optimization
    - **Property 8: Path Optimization**
    - **Validates: Requirements 3.3**

- [ ] 12. Checkpoint - Verify end-to-end flow works
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 13. Implement swarm agent coordination
  - [ ] 13.1 Create swarm coordinator module
    - Create `core/swarm_coordinator.py`
    - Implement `SwarmCoordinator` class
    - Track all active swarm agents and their states
    - Implement command distribution logic (round-robin)
    - Implement coordinate conflict prevention
    - Implement agent failure detection and command reassignment
    - Add agent position tracking
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_
  
  - [ ] 13.2 Create command distribution endpoint
    - Add `/api/commands/distribute` POST endpoint
    - Distribute commands to available swarm agents via Isaac Sim
    - Track command execution status
    - Update agent states based on acknowledgments
    - _Requirements: 4.2, 4.3, 4.5_
  
  - [ ]* 13.3 Write property test for command distribution across agents
    - **Property 18: Command Distribution Across Agents**
    - **Validates: Requirements 8.1**
  
  - [ ]* 13.4 Write property test for coordinate conflict prevention
    - **Property 19: Coordinate Conflict Prevention**
    - **Validates: Requirements 8.2**
  
  - [ ]* 13.5 Write property test for agent state tracking
    - **Property 21: Agent State Tracking**
    - **Validates: Requirements 8.4**
  
  - [ ]* 13.6 Write property test for failed agent command reassignment
    - **Property 22: Failed Agent Command Reassignment**
    - **Validates: Requirements 8.5**

- [ ] 14. Implement error handling and recovery
  - [ ] 14.1 Create error handling module
    - Create `core/error_handler.py`
    - Implement structured error response format
    - Add error categorization (connection, validation, planning, execution)
    - Implement circuit breaker for Gemini API (5 failures, 30s half-open)
    - Implement circuit breaker for Isaac Sim (3 failures, 10s half-open)
    - Add error logging with correlation IDs
    - _Requirements: 3.6, 6.1, 6.2, 6.3, 6.4, 6.5_
  
  - [ ] 14.2 Add error handling middleware to FastAPI
    - Create global exception handler
    - Return structured error responses for all exceptions
    - Log all errors with stack traces
    - _Requirements: 2.3, 3.6_
  
  - [ ]* 14.3 Write unit tests for error scenarios
    - Test connection errors and recovery
    - Test validation errors and rejection
    - Test AI planning errors and human intervention
    - Test execution errors and command reassignment
    - _Requirements: 2.3, 3.6, 6.5_

- [ ] 15. Add configuration management
  - [ ] 15.1 Create configuration module
    - Create `core/config.py`
    - Load configuration from environment variables and config files
    - Define no-go zones configuration
    - Define thermal limits, collision radius, grid precision
    - Define API endpoints for Gemini and Isaac Sim
    - Define timeout values and retry limits
    - Add configuration validation on startup
    - _Requirements: 6.1, 6.2, 6.3, 6.4_
  
  - [ ] 15.2 Create example configuration files
    - Create `.env.example` with all required environment variables
    - Create `config.yaml` with system parameters
    - Document all configuration options in README
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [ ] 16. Implement database persistence (optional)
  - [ ] 16.1 Set up SQLite database
    - Create `core/database.py`
    - Define database schema (defects, commands, agent_states tables)
    - Implement SQLAlchemy models
    - Add database initialization and migration support
    - _Requirements: 4.4, 7.3, 8.4_
  
  - [ ] 16.2 Add database operations
    - Implement CRUD operations for defects
    - Implement CRUD operations for commands
    - Implement CRUD operations for agent states
    - Add database queries for metrics and reporting
    - _Requirements: 4.4, 7.3, 7.4, 8.4_

- [ ] 17. Create integration tests
  - [ ]* 17.1 Write end-to-end integration tests
    - Test full flow: sensor data → Gemini → commands → Isaac Sim
    - Test WebSocket bidirectional communication
    - Test error recovery scenarios
    - Test swarm coordination with multiple agents
    - _Requirements: All requirements_

- [ ] 18. Final checkpoint - Complete system validation
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 19. Create deployment artifacts
  - [ ] 19.1 Create deployment scripts
    - Create `deploy.sh` script for Vultr deployment
    - Create `systemd` service file for auto-start
    - Create `nginx` configuration for reverse proxy (optional)
    - Add SSL/TLS certificate setup instructions
    - _Requirements: 1.1_
  
  - [ ] 19.2 Create documentation
    - Create `README.md` with setup instructions
    - Create `API.md` with endpoint documentation
    - Create `ARCHITECTURE.md` with system overview
    - Create `DEPLOYMENT.md` with deployment guide
    - _Requirements: All requirements_

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation throughout development
- Property tests validate universal correctness properties (minimum 100 iterations each)
- Unit tests validate specific examples and edge cases
- The implementation follows a bottom-up approach: infrastructure → core components → integration → coordination
- All code should follow PEP 8 style guidelines and include type hints
- Use async/await patterns throughout for optimal performance with FastAPI
