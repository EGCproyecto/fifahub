---
name: "Unplanned Task"
about: "Unplanned work (not a bug or standard Work Item)"
title: "[TASK] Enforce Description column in CSV uploads"
labels: enhancement
---

### Description
This unplanned task is necessary to improve the quality of dataset metadata at the source level. We need to enforce a stricter schema for uploaded CSV files to ensure they contain descriptive information.

### Details
Modify the `TabularDatasetForm` validation logic in `app/modules/tabular/forms.py`.
- Add `"Description"` to the `FIFA_REQUIRED_COLUMNS` list.
- This will reject any CSV upload that does not contain a column header named "Description".

### Impact
- **Backend**: `forms.py` validation logic.
- **Frontend**: Error messages if the user uploads an invalid CSV.
- **Tests**: Existing tests in `app/modules/tabular/tests` will fail if their sample CSVs are not updated to include this new column.

### Acceptance Criteria
- [ ] The system rejects CSV files missing the "Description" column.
- [ ] Existing valid CSVs (with the column added) can still be uploaded.
- [ ] Manual verification shows correct error messages for invalid files.
- [ ] Changes are correctly integrated into `trunk` (or main branch).

### Assignee
@sergio

### Branch
`featuretask/TASK-CSV-enforce-description`
