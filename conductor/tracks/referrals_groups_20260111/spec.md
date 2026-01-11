# Track Spec: Referral System & Pricing Groups

## Overview
Implement a referral system to encourage user growth and a flexible pricing system that distinguishes between 'Standard' users and the 'Inner Circle'.

## Objectives
- Generate unique referral links for every user.
- Track who invited whom and store this in the database.
- Implement a 'Referral Cabinet' showing invite stats and potential rewards.
- Apply dynamic pricing in the 'Top-up' menu based on the user's group.
- Implement basic reward logic (e.g., balance bonus for successful invites).

## Technical Details
- **Referrals**: Handled via /start? Birds=referrer_id deep-linking.
- **Pricing**: 	op_up menu will fetch pricing from a configuration or env variables, filtered by user's group_name.
- **Database**: Use existing eferred_by column and eferral_rewards table.

## Acceptance Criteria
- Users can see their referral link in the bot.
- New users joining via a link are correctly linked to their referrer.
- The 'Top-up' menu shows prices based on user group (e.g., 150 for Inner Circle, 200 for Standard).
- Admins can still manually switch users between groups.
