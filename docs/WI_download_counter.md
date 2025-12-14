# Download Counter for Datasets

## Overview

This feature allows tracking how many times a dataset has been downloaded by incrementing a counter each time a download is requested. This gives authors and users a simple way to measure dataset popularity.

The implementation covers:
- Automatic download tracking
- Display of download counts across the platform
- API exposure of download statistics

## Technologies Used

- **SQLAlchemy**: Database field and increment operations
- **Flask**: Route handling for download tracking

## Data Model

### BaseDataset (download-related field)

The BaseDataset model stores the download counter:
- **download_count**: Integer field tracking total downloads (default = 0, indexed for performance)

## Download Tracking Flow

1. User requests to download a dataset file (or ZIP)
2. The download request is intercepted by the service layer
3. download_count is incremented in the database
4. The file is served to the user

This ensures every download is accurately tracked.

## Display Locations

The download count is displayed in multiple locations:
- Dataset detail page next to the download button
- Dataset cards on the explore page
- Trending datasets section on the home page
- API responses for datasets

## Backend API Endpoints

### Get Dataset Stats
- **GET /datasets/{id}/stats**
  - Returns download count along with other metrics
  - Response includes: dataset_id, download_count, view_count

### Dataset API Response
- **GET /api/datasets**
  - Each dataset object includes download_count field

## Summary

The download counter provides valuable metrics for:
- Authors to measure their dataset's impact
- Users to discover popular datasets
- Platform analytics and trending features
- Building the trending datasets functionality
