# New Dataset Types (FIFAHub Transformation)

## Overview

This feature restructures the platform so that it is no longer focused on UVL datasets, but on FIFA player CSV datasets. The goal is to transform uvlhub into FIFAHub, where FIFA-specific data can have its own validation logic and display requirements.

The implementation covers:
- Polymorphic dataset inheritance architecture
- FIFA CSV schema validation
- Tabular-specific metadata and metrics
- Custom upload and view workflows for CSV data

## Technologies Used

- **SQLAlchemy**: Polymorphic inheritance for dataset types
- **Pandas**: CSV processing and analysis
- **Flask-WTF**: Type-specific forms with validation
- **Jinja2**: Modular template blocks for different dataset types

## Data Model

### BaseDataset (Parent Class)

The BaseDataset model serves as the abstract parent for all dataset types:
- **id**: Primary key
- **type**: Discriminator column for polymorphism
- **user_id**: Owner of the dataset
- **download_count**: Number of downloads
- **view_count**: Number of page views
- **created_at**: Creation timestamp
- **ds_meta_data_id**: Reference to common metadata

### TabularDataset (FIFA CSV)

The TabularDataset model extends BaseDataset for CSV files:
- **rows_count**: Number of rows in the dataset
- **schema_json**: Column definitions and types
- **meta_data**: Relationship to TabularMetaData
- **metrics**: Relationship to TabularMetrics

### Tabular Metadata

The TabularMetaData model stores CSV-specific information:
- **delimiter**: CSV delimiter character
- **encoding**: File encoding (UTF-8, etc.)
- **has_header**: Whether the first row contains headers
- **n_rows**: Row count
- **n_cols**: Column count
- **sample_rows**: Preview of first rows

## FIFA Schema Validation

When uploading a CSV dataset, the system validates that the file contains the required FIFA columns:
- ID, Name, Age, Nationality
- Overall, Potential, Club
- Value, Wage
- Preferred Foot, Weak Foot, Skill Moves
- Position, Height, Weight

If any required columns are missing, the upload is rejected with a clear error message indicating which columns are absent.

## Upload Flow

1. User navigates to the tabular upload page
2. User fills in metadata (title, description, authors, tags)
3. User uploads a CSV file
4. System validates the FIFA schema
5. If validation passes, metadata is extracted (rows, columns, sample data)
6. Dataset is created and associated with the user
7. User is redirected to the dataset detail page

## View Flow

1. User opens a tabular dataset detail page
2. Common metadata is displayed (title, authors, description)
3. Tabular-specific information is shown:
   - Row and column counts
   - Data preview table
   - CSV encoding and delimiter information
4. Related datasets are suggested below

## Backend Routes

### Upload
- **GET /tabular/upload** – Display upload form
- **POST /tabular/upload** – Process upload with validation

### View
- **GET /tabular/{id}** – Display tabular dataset detail page

## User Interface

Relevant templates:
- **upload_tabular.html** – Upload form with metadata fields
- **view_tabular.html** – Dataset detail with data preview

The UI provides clear feedback during upload and displays data-specific information on detail pages.

## Summary

The new dataset types architecture:
- Enables domain-specific hubs (FIFAHub)
- Maintains clean separation of concerns
- Allows independent evolution of each dataset type
- Provides consistent user experience across types
- Enforces strict FIFA data validation
