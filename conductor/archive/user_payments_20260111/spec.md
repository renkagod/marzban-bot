# Track Spec: User Subscription & Payments

## Overview
Implement the core user-facing functionality: verifying channel membership, topping up balance via CryptoBot, and viewing Marzban subscription details.

## Objectives
- Implement a one-time channel subscription check for new users.
- Integrate CryptoBot API for automated payments (supporting both Mainnet and Testnet).
- Build a User Dashboard showing data usage, expiry date, and connection link.
- Generate QR codes for subscription links.
- Implement group-aware pricing (150 for Inner Circle, 200 for Standard).

## Technical Details
- **Payments**: CryptoBot API (requires context7 documentation).
- **Verification**: ot.get_chat_member for channel check.
- **QR Codes**: qrcode library.
- **Resilience**: Handle payment timeouts and Marzban API unavailability during dashboard rendering.

## Acceptance Criteria
- New users cannot access the bot without subscribing to the specified channel.
- Users can create a CryptoBot invoice and pay it (verified via Testnet).
- Balance is automatically updated in the database upon successful payment.
- Subscription dashboard displays correct data from Marzban and correct pricing based on the user's group.
