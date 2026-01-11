# Track Spec: Payment Fixes & FreeKassa Integration

## Overview
Fix issues with Marzban protocol configurations and integrate FreeKassa as a secondary payment provider.

## Objectives
- Resolve '400 Bad Request' when VMess is disabled on the Marzban server.
- Ensure payment processing is robust and handles failures in Marzban user creation without losing track of user funds.
- Implement FreeKassa API for balance top-ups.

## Acceptance Criteria
- Subscription creation succeeds even if some protocols (like VMess) are disabled on the server.
- Users are clearly notified if their payment was successful but the subscription auto-activation failed (funds should remain on balance).
- FreeKassa invoices can be generated and verified.
