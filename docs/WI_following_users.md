# Following Users and Communities

## Overview

This feature allows users to follow specific authors and communities so that they can stay up to date with their activity. When a followed author publishes a new dataset, or when a new dataset is added to a community the user follows, they can track these updates from their profile.

The implementation covers:
- Following and unfollowing authors
- Following and unfollowing communities
- Integration with user profile dashboard

## Technologies Used

- **SQLAlchemy**: Follow relationships and cascade operations
- **Flask-Login**: Authentication for follow actions
- **Flask**: RESTful endpoints for follow operations

## Data Model

### UserFollowAuthor

Tracks user-to-author follows:
- **user_id**: The user who is following
- **author_id**: The author being followed
- **created_at**: Timestamp of when the follow was created

Unique constraint ensures a user cannot follow the same author twice.

### UserFollowCommunity

Tracks user-to-community follows:
- **user_id**: The user who is following
- **community_id**: The community identifier being followed
- **created_at**: Timestamp of when the follow was created

Unique constraint ensures a user cannot follow the same community twice.

### User Model Relationships

The User model includes relationships to followed entities:
- **followed_authors**: Dynamic relationship to UserFollowAuthor
- **followed_communities**: Dynamic relationship to UserFollowCommunity

Both relationships support cascade delete operations.

## Follow Flow

1. User views an author profile or community page
2. User clicks the "Follow" button
3. A follow record is created in the database
4. The button changes to "Following" state
5. Follow appears in user's profile summary

## Unfollow Flow

1. User clicks "Following" button (or "Unfollow")
2. The follow record is deleted from the database
3. The button reverts to "Follow" state
4. Follow is removed from user's profile summary

## Backend API Endpoints

### Follow/Unfollow Author
- **POST /follow/author/{author_id}**
  - Creates a follow relationship with the author
  - Returns success status
- **POST /unfollow/author/{author_id}**
  - Removes the follow relationship
  - Returns success status

### Follow/Unfollow Community
- **POST /follow/community/{community_id}**
  - Creates a follow relationship with the community
  - Returns success status
- **POST /unfollow/community/{community_id}**
  - Removes the follow relationship
  - Returns success status

All endpoints require authentication and return JSON responses. Attempting to follow a non-existent entity returns a 404 error.

## User Interface

The follow functionality is integrated into:
- Author profile pages (follow button)
- Community pages (follow button)
- User profile summary (lists of followed authors and communities)

## Summary

The following feature:
- Keeps users engaged with content they care about
- Builds community around authors and topics
- Promotes content discovery through social connections
- Provides a foundation for future notification features
