# Two-Factor Authentication (2FA)

## Overview

This project implements Time-based One-Time Password (TOTP) Two-Factor Authentication to add an extra security layer on top of the standard username/password login. The 2FA system is based on RFC 6238 (TOTP) and is compatible with common authenticator apps such as Google Authenticator, Microsoft Authenticator, Authy, etc.

The implementation covers:
- 2FA setup and activation
- 2FA challenge during login
- Recovery codes for account recovery
- Rate limiting and security controls

## Technologies Used

- **pyotp**: TOTP generation and verification
- **qrcode**: QR code generation for authenticator setup
- **Flask-Login**: Session and authentication handling
- **SQLAlchemy**: Persistence of secrets and recovery codes

## Data Model

### User (2FA-related fields)

The User model stores the information required for 2FA:
- **two_factor_secret**: Base32-encoded secret used for TOTP generation
- **two_factor_enabled**: Boolean flag indicating whether 2FA is active

### Recovery Codes

Recovery codes are stored in a dedicated model:
- **UserTwoFactorRecoveryCode**
  - One-time use
  - Stored hashed
  - Used when the authenticator device is unavailable

## 2FA Setup Flow

1. User requests 2FA activation
2. System generates a random TOTP secret
3. A QR code is generated using the secret
4. User scans the QR code with an authenticator app
5. User enters a valid TOTP code to confirm setup
6. 2FA is marked as enabled
7. A set of recovery codes is generated and shown once

This flow ensures the authenticator app is correctly synchronized before activation.

## Login Flow with 2FA

### Step 1 – Credentials Validation
- User submits username/email and password
- Credentials are verified

### Step 2 – 2FA Challenge (if enabled)
- If two_factor_enabled = true, login is paused
- User is redirected to the 2FA challenge page
- User must provide:
  - A valid TOTP code, or
  - A valid unused recovery code

### Step 3 – Session Creation
- On successful verification, the user session is finalized
- User is logged in normally

## Disable 2FA Flow

The system allows users to explicitly disable Two-Factor Authentication from their account settings.

### Disable Process
1. User requests to disable 2FA from the security settings
2. System requires password re-authentication
3. User must provide a valid current TOTP code or a recovery code
4. Upon successful verification:
   - two_factor_enabled is set to false
   - two_factor_secret is deleted
   - All unused recovery codes are invalidated

This ensures that only the legitimate account owner can disable 2FA.

## Recovery Codes Flow

- Recovery codes are generated during 2FA setup
- Each code can be used only once
- When a recovery code is used:
  - It is invalidated immediately
  - The login process continues successfully

Recovery codes allow account access if the user loses access to their authenticator app.

## Security Measures

- Rate limiting on login and 2FA attempts
- Short TOTP validity window (30 seconds)
- Hashed storage of recovery codes
- Single-use recovery codes
- Explicit confirmation required to enable 2FA

## Error Handling

Common failure scenarios handled by the system:
- Invalid or expired TOTP code
- Invalid or already-used recovery code
- Too many failed attempts (rate limited)

Clear error messages are shown without leaking sensitive information.

## Backend API Endpoints

### Enable 2FA
- **POST /api/2fa/setup**
  - Generates a TOTP secret
  - Returns a QR code and manual setup key
- **POST /api/2fa/verify**
  - Verifies initial TOTP code
  - Enables 2FA
  - Generates recovery codes

### 2FA Login Challenge
- **POST /api/2fa/challenge**
  - Verifies TOTP or recovery code
  - Completes login session

### Disable 2FA
- **POST /api/2fa/disable**
  - Requires password + TOTP or recovery code
  - Disables 2FA and removes secrets

### Recovery Codes
- **POST /api/2fa/recovery/regenerate**
  - Invalidates old recovery codes
  - Generates a new set

All endpoints return standard HTTP status codes (200, 400, 401, 429).

## User Interface

Relevant templates:
- **two_factor_setup.html** – 2FA activation and QR display
- **two_factor_challenge.html** – Login challenge form

The UI clearly guides the user through setup and login steps.

## Summary

The 2FA implementation significantly improves account security by:
- Protecting against credential theft
- Adding a second authentication factor
- Providing secure recovery mechanisms

This solution follows industry best practices and is fully compatible with standard authenticator applications.
