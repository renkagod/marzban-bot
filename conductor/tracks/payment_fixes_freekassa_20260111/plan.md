# Track Plan: Payment Fixes & FreeKassa Integration

## Phase 1: Marzban Integration Fixes
- [x] Task: Robust Protocol Selection (5eff262)
    - [x] Sub-task: Modify `process_subscription_action` to try default protocols and fallback if one is disabled.
- [~] Task: Payment Processing Atomicity
    - [ ] Sub-task: Improve `check_payment_handler` to handle Marzban failures gracefully.

## Phase 2: FreeKassa Integration
- [ ] Task: FreeKassa API Client
- [ ] Task: Add FreeKassa to Top-up menu
- [ ] Task: Implement FreeKassa webhook/callback or polling check

## Phase 3: Verification
- [ ] Task: Conductor - User Manual Verification
