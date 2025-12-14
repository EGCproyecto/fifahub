# Trending Datasets

## Overview

This feature displays a ranking of the most viewed or recently downloaded datasets to help visitors discover what is popular on the platform. The trending section appears prominently on the home page.

The implementation covers:
- Ranking algorithm based on download counts
- Dynamic loading of trending data
- Responsive display on the home page

## Technologies Used

- **SQLAlchemy**: Aggregation queries for ranking
- **Flask**: API endpoint for trending data
- **JavaScript**: Asynchronous loading of trending section

## Ranking Algorithm

Datasets are ranked based on:
- Download count (primary sorting factor)
- Recent activity prioritized
- Only published datasets are included

## Display Information

For each trending dataset, the following is shown:
- Dataset title (clickable link to detail page)
- Main author name
- Number of downloads with icon
- Community (if applicable)

## Trending Section Flow

1. Home page loads with a "Trending Datasets" placeholder
2. JavaScript fetches trending data asynchronously
3. Top datasets are rendered in a list format
4. Each item links to the dataset detail page

This async loading ensures fast initial page loads.

## Backend API Endpoints

### Get Trending Datasets
- **GET /datasets/trending**
  - Returns top datasets ordered by download_count
  - Default limit: 5 datasets
  - Response includes: id, title, author, download_count

## User Interface

The trending section displays on the home page:
- Card with "Trending Datasets" header
- List of top datasets with download counts
- Loading state while fetching data
- Empty state message if no datasets exist

## Summary

The trending datasets feature:
- Helps users discover popular content
- Encourages quality dataset uploads
- Provides social proof for valuable datasets
- Improves user engagement with the platform
