# Track Spec: Core Infrastructure and Admin Management

## Overview
This track focuses on building the foundational layers of the Marzban Telegram Bot, including the bot engine, Marzban API integration, and essential administrative controls.

## Objectives
- Initialize the Aiogram 3.x bot engine with asynchronous support.
- Establish a reliable connection to the Marzban API using the 'marzban' library.
- Implement the SQLite database schema for users, groups, and logs.
- Create an Admin interface for managing the 'Inner Circle' group.
- Develop a health monitor that alerts a Telegram channel topic if Marzban is down.

## Technical Details
- **Framework**: Aiogram 3.x
- **API**: Marzban Python Client (context7 documentation required)
- **Database**: SQLite with aiosqlite
- **Logging**: Dedicated admin topic for system alerts.

## Acceptance Criteria
- Bot successfully starts and connects to the Marzban API.
- Admins can manually add/remove users from the 'Inner Circle' group via Telegram.
- Server health check runs periodically and sends an alert to the channel if the API is unreachable.
- Database correctly stores user and group information.
