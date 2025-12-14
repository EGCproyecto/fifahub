# View User Profile

## Overview

This feature allows users to click on a user's profile to see their uploaded datasets. Users can view their own profile dashboard as well as browse other users' public datasets.

The implementation covers:
- Personal profile summary page
- Public profile viewing for other users
- Paginated dataset listings
- Integration with following functionality

## Technologies Used

- **Flask-Login**: Authentication and session handling
- **SQLAlchemy**: User and dataset queries with pagination
- **Jinja2**: Template rendering for profile pages

## Data Model

### UserProfile

The UserProfile model stores user information:
- **name**: User's first name
- **surname**: User's last name
- **orcid**: ORCID identifier (optional)
- **affiliation**: User's institution or organization (optional)

Each User has a one-to-one relationship with UserProfile.

## Profile Summary Features

The personal profile summary page displays:
- User profile information (name, surname, affiliation, ORCID)
- User's uploaded datasets (paginated)
- List of followed authors
- List of followed communities

## Public Profile Flow

1. User clicks on an author name anywhere on the platform
2. User is redirected to the public profile page
3. That user's datasets are displayed in a paginated list
4. Each dataset links to its detail page

This allows discovery of datasets by specific authors.

## Backend API Endpoints

### View Own Profile
- **GET /profile/summary**
  - Returns the logged-in user's profile dashboard
  - Includes datasets, followed authors, followed communities

### Edit Profile
- **GET/POST /profile/edit**
  - Form to update profile information

### View Other User's Datasets
- **GET /users/{userId}/datasets**
  - Renders public profile page with that user's datasets

### API: Get User Datasets
- **GET /api/users/{userId}/datasets**
  - Returns paginated JSON of user's datasets
  - Pagination includes: total_items, total_pages, current_page

## User Interface

Relevant templates:
- **profile/summary.html** – Personal profile dashboard
- **profile/edit.html** – Edit profile form
- **profile/user_dataset_list.html** – Public profile view

The UI provides clear navigation between profile sections.

## Summary

The user profile feature:
- Enables discovery of datasets by author
- Builds community around content creators
- Provides transparency about dataset authorship
- Encourages quality contributions through visibility
