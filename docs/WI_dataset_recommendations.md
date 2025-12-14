# Automatic Dataset Recommendations

## Overview

This feature provides users with suggestions for related datasets when viewing a dataset, making it easier to discover similar content that may be of interest. The recommendations appear in a "Related Datasets" section on dataset detail pages.

The implementation covers:
- Similarity scoring based on shared metadata
- Weighted algorithm considering multiple factors
- Fallback behavior for datasets with limited metadata
- Integration with both dataset types (UVL and Tabular)

## Technologies Used

- **SQLAlchemy**: Query and matching logic
- **Jaccard Index**: Set similarity calculations
- **Flask**: Integration with dataset routes

## Recommendation Algorithm

The system suggests datasets based on multiple weighted factors:

### Weight Distribution
- **Tags**: 40% – Shared tags between datasets
- **Communities**: 30% – Datasets in the same community
- **Authors**: 20% – Datasets by the same author(s)
- **Downloads**: 5% – Popularity bonus for high-download datasets
- **Recency**: 5% – Freshness bonus for recently uploaded datasets

### Scoring Methods

**Jaccard Similarity**: Calculates the intersection over union for sets of tags, authors, and communities. Returns a value between 0.0 and 1.0.

**Download Score**: Uses Log10 normalization to smooth high download counts, preventing extremely popular datasets from dominating recommendations.

**Recency Score**: Freshness score that starts at 1.0 for datasets uploaded today and decays to 0.0 over 365 days.

## Recommendation Flow

1. User views a dataset detail page
2. System collects the dataset's metadata profile (tags, authors, communities)
3. Candidate datasets sharing at least one attribute are fetched
4. Each candidate is scored using the weighted algorithm
5. Top 5 candidates are returned as recommendations
6. Related datasets are displayed in the detail page

## Fallback Behavior

When no metadata matches are found (e.g., dataset has no tags or authors):
- System returns top datasets by download count
- Excludes the current dataset from results
- Ensures users always see some recommendations

## User Interface

Related datasets appear on:
- Dataset detail page (view_dataset.html)
- Tabular dataset detail page (view_tabular.html)

Each recommendation shows:
- Dataset title (clickable link)
- Download count
- Author information

## Summary

The automatic recommendations feature:
- Improves content discovery
- Increases user engagement
- Helps users find relevant datasets quickly
- Promotes lesser-known quality datasets through similarity matching
