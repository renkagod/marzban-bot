# Track Plan: User Subscription & Payments

## Phase 1: Access Control & Dashboard
- [x] Task: Mandatory Channel Subscription (4012f2b)
    - [ ] Sub-task: Implement 'Registration' middleware/logic to check channel membership
    - [ ] Sub-task: Create a 'Join Channel' block with verification button
- [x] Task: User Dashboard implementation (a08c3ca)
    - [ ] Sub-task: Create main menu handler showing balance and group status
    - [ ] Sub-task: Implement 'My Subscription' view fetching real data from Marzban API
    - [ ] Sub-task: Add QR code generation for connection links
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Access Control & Dashboard' (Protocol in workflow.md)

## Phase 2: CryptoBot Integration
- [ ] Task: CryptoBot API Client
    - [ ] Sub-task: Implement a generic CryptoBot client supporting Mainnet and Testnet modes
    - [ ] Sub-task: Create logic for creating invoices based on selected top-up amount
- [ ] Task: Payment Processing & Webhooks
    - [ ] Sub-task: Implement a polling task or webhook handler for payment verification
    - [ ] Sub-task: Update user balance and log payment in the database upon success
    - [ ] Sub-task: Send confirmation notifications to user and admin channel topic
- [ ] Task: Conductor - User Manual Verification 'Phase 2: CryptoBot Integration' (Protocol in workflow.md)
