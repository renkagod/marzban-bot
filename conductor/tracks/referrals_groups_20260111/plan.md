# Track Plan: Referral System & Pricing Groups

## Phase 1: Referral Logic
- [x] Task: Deep-linking & Tracking (d0d7a85)
    - [ ] Sub-task: Update /start handler to capture referrer ID from deep-links
    - [ ] Sub-task: Modify add_user to store referral relationships
- [x] Task: Referral Cabinet (5514482)
    - [ ] Sub-task: Create a '👫 Рефералы' menu showing stats and the referral link
    - [ ] Sub-task: Implement a method to count successful invites
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Referral Logic' (Protocol in workflow.md)

## Phase 2: Dynamic Pricing & Groups
- [ ] Task: Group-based Pricing Implementation
    - [ ] Sub-task: Define pricing constants or env variables for each group
    - [ ] Sub-task: Update top_up menu to display dynamic buttons based on user['group_name']
- [ ] Task: Referral Rewards (Optional/Bonus)
    - [ ] Sub-task: Implement logic to award balance to referrer upon referee's first payment
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Dynamic Pricing & Groups' (Protocol in workflow.md)