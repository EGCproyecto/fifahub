# Fakenodo – Zenodo Simulation Service

## Overview

Fakenodo is a test service that simulates the basic responses of a Zenodo-like API, without attempting to replicate it fully. Its purpose is to enable development and testing of the Zenodo integration in FIFAHub without relying on the actual Zenodo API.

The implementation covers:
- Simulated deposition creation and management
- File upload simulation
- DOI generation and versioning logic
- Publishing workflow

## Technologies Used

- **Flask**: HTTP service endpoints
- **SQLAlchemy**: Persistent storage of depositions
- **JSON**: Metadata storage format

## Core Functionality

Fakenodo respects the basic Zenodo logic:
- **Edit metadata only** → No new DOI is generated
- **Change/add files and publish** → Generates a new DOI and version

This mirrors how Zenodo handles versioning of research outputs.

## Data Model

### Fakenodo

The Fakenodo model represents a simulated deposition:
- **id**: Primary key (used as deposition ID)
- **meta_data**: JSON field storing title, description, creators
- **doi**: Generated DOI string

## DOI Generation

Fakenodo generates predictable DOIs for testing:
- **Initial DOI**: 10.5281/fakenodo.{deposition_id}
- **Versioned DOI**: 10.5281/fakenodo.{deposition_id}.v{version}

This allows consistent testing of DOI-related features.

## Configuration

Fakenodo is enabled via environment variable:
- **FAKENODO_URL**: When set, the application uses Fakenodo instead of real Zenodo

In the application, FakenodoService replaces ZenodoService when this variable is configured.

## Deposition Workflow

### Create Deposition
1. Client sends POST request with metadata
2. Fakenodo creates a new deposition record
3. A temporary DOI is assigned
4. Response includes deposition ID and links

### Upload File
1. Client sends file to the deposition
2. Fakenodo simulates file storage
3. File is associated with the deposition

### Publish Deposition
1. Client requests publication
2. Fakenodo generates a versioned DOI
3. Deposition is marked as published
4. Response includes final DOI

### Delete Deposition
1. Client requests deletion
2. Deposition is removed from the database
3. Associated files are cleaned up

## Backend API Endpoints

### Deposition Management
- **POST /fakenodo/depositions**
  - Creates a new deposition
  - Returns deposition ID and links
- **POST /fakenodo/depositions/{id}/upload**
  - Uploads a file to the deposition
  - Returns file metadata
- **POST /fakenodo/depositions/{id}/publish**
  - Publishes the deposition
  - Returns final DOI
- **DELETE /fakenodo/depositions/{id}**
  - Deletes the deposition

## Integration with FIFAHub

When FAKENODO_URL is set:
1. All Zenodo operations route to Fakenodo
2. DOIs are generated locally
3. No external API calls are made
4. Tests can run without Zenodo credentials

## Summary

Fakenodo enables:
- Local development without Zenodo API access
- Reliable automated testing of DOI features
- Simulation of Zenodo versioning logic
- Predictable responses for CI/CD pipelines
- Isolation from external service dependencies
