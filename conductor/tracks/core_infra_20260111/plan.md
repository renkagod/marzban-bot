# Track Plan: Core Infrastructure and Admin Management

## Phase 1: Foundation & API [checkpoint: 945446d]
- [x] Task: Project Initialization (55177b0)
    - [ ] Sub-task: Create directory structure and pyproject.toml/requirements.txt
    - [ ] Sub-task: Configure environment variables (.env) for Bot Token and Marzban credentials
- [x] Task: Database Setup (ce12afd)
    - [ ] Sub-task: Design and implement SQLite schema using aiosqlite
    - [ ] Sub-task: Create database manager for CRUD operations on users and groups
- [x] Task: Marzban API Integration (ea825b5)
    - [ ] Sub-task: Initialize Marzban client and implement a connectivity check
    - [ ] Sub-task: Create a wrapper for core Marzban operations (get status, list users)
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Foundation & API' (Protocol in workflow.md)

## Phase 2: Bot Core & Admin Tools
- [x] Task: Bot Engine Implementation (2fdb2ae)
    - [ ] Sub-task: Set up Aiogram dispatcher and basic handlers
    - [ ] Sub-task: Implement 'Failure Isolation' middleware to catch API errors
- [ ] Task: Admin Group Management
    - [ ] Sub-task: Create admin-only command to manage 'Inner Circle' members
    - [ ] Sub-task: Implement interactive menus for selecting and tagging users
- [ ] Task: Health Monitoring Service
    - [ ] Sub-task: Implement background task for periodic server status checks
    - [ ] Sub-task: Configure alert forwarding to the designated admin channel topic
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Bot Core & Admin Tools' (Protocol in workflow.md)
