# Track Plan: Referral System & Pricing Groups

## Phase 1: Referral Logic
- [ ] Task: Deep-linking & Tracking
    - [ ] Sub-task: Update /start handler to capture referrer ID from deep-links
    - [ ] Sub-task: Modify dd_user to store referral relationships
- [ ] Task: Referral Cabinet
    - [ ] Sub-task: Create a '👫 Рефералы' menu showing stats and the referral link
    - [ ] Sub-task: Implement a method to count successful invites
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Referral Logic' (Protocol in workflow.md)

## Phase 2: Dynamic Pricing & Groups
- [ ] Task: Group-based Pricing Implementation
    - [ ] Sub-task: Define pricing constants or env variables for each group
    - [ ] Sub-task: Update 	op_up menu to display dynamic buttons based on user['group_name']
- [ ] Task: Referral Rewards (Optional/Bonus)
    - [ ] Sub-task: Implement logic to award balance to referrer upon referee's first payment
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Dynamic Pricing & Groups' (Protocol in workflow.md)
