# FIFAHub Documentation

This folder contains technical documentation for FIFAHub features and Work Items (WIs).

## General Documentation

| Document | Description |
|----------|-------------|
| [CI/CD Workflows](CICD_WORKFLOWS.md) | GitHub Actions pipelines and deployment process |
| [Contributing Guide](CONTRIBUTING.md) | How to contribute to FIFAHub |

## Work Items Documentation

| WI | Description | Difficulty | Issue |
|----|-------------|------------|-------|
| [Download Counter](WI_download_counter.md) | Track dataset download counts | Easy | [#105](https://github.com/EGCETSII/uvlhub/issues/105) |
| [View User Profile](WI_user_profile.md) | View user's uploaded datasets | Easy | [#69](https://github.com/EGCETSII/uvlhub/issues/69) |
| [Trending Datasets](WI_trending_datasets.md) | Ranking of popular datasets | Medium | [#100](https://github.com/EGCETSII/uvlhub/issues/100) |
| [Following Users](WI_following_users.md) | Follow authors and communities | Medium | [#92](https://github.com/EGCETSII/uvlhub/issues/92) |
| [Two-Factor Auth](WI_two_factor_auth.md) | TOTP-based 2FA security | Hard | [#89](https://github.com/EGCETSII/uvlhub/issues/89) |
| [Dataset Recommendations](WI_dataset_recommendations.md) | Related datasets suggestions | Hard | [#98](https://github.com/EGCETSII/uvlhub/issues/98) |
| [New Dataset Types](WI_new_dataset_types.md) | FIFA CSV support (FIFAHub) | Hard | [#104](https://github.com/EGCETSII/uvlhub/issues/104) |
| [Fakenodo](WI_fakenodo.md) | Zenodo simulation for testing | Hard | [#103](https://github.com/EGCETSII/uvlhub/issues/103) |

## WI Categories

### Easy
- Download Counter - Simple field increment on download
- View User Profile - Basic profile page with user datasets

### Medium  
- Trending Datasets - Ranking algorithm based on downloads/views
- Following Users - Social features with email notifications

### Hard
- Two-Factor Authentication - Security feature with TOTP and recovery codes
- Dataset Recommendations - Content-based recommendation engine
- New Dataset Types - Polymorphic dataset architecture (Mandatory)
- Fakenodo - Zenodo API simulation service (Mandatory)

## Quick Links

- [Main README](../README.md) - Project overview and setup
- [GitHub Issues](https://github.com/EGCETSII/uvlhub/issues) - Original issue tracker
