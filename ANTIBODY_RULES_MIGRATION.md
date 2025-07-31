# Antibody Rules Migration Guide

## Overview

This document describes the migration from default rules to database-only antibody rules management. The system now stores all antibody rules in the database and provides tools for importing/exporting rule templates.

## Changes Made

### 1. Fixed Database Persistence Issue ✅

**Problem**: Custom antibody rules were being deleted and replaced with default rules on every server restart.

**Solution**: 
- Modified `main.py` to only initialize default rules if the database is empty
- Custom rules now persist across server restarts
- Added proper logging to track rule initialization

### 2. Enhanced Rule Management ✅

**New Features**:
- **Export Rules**: Download all rules as a JSON template
- **Import Rules**: Import rules from JSON files
- **Reset to Defaults**: Clear all rules and reset to defaults
- **Add Default Rules**: Add default rules without clearing existing ones

**API Endpoints**:
- `GET /api/antibody-rules/export` - Export all rules as template
- `POST /api/antibody-rules/import` - Import rules from template
- `POST /api/antibody-rules/reset` - Reset to default rules
- `POST /api/antibody-rules/initialize` - Add default rules (non-destructive)

### 3. Migration Tools ✅

**Migration Script**: `migrate_default_rules.py`
- Create templates from default rules
- Migrate rules to database
- Validate database rules against defaults

## Usage

### Web Interface

1. **Export Rules**:
   - Go to Antibody Rules Management page
   - Click "Export Rules" button
   - Download JSON file with all current rules

2. **Import Rules**:
   - Click "Import Rules" button
   - Select JSON file
   - Choose whether to clear existing rules or add to them

3. **Reset to Defaults**:
   - Click "Reset to Defaults" button
   - Confirms before clearing all rules

4. **Add Default Rules**:
   - Click "Add Default Rules" button
   - Adds missing default rules without clearing existing ones

### Command Line Migration

```bash
# Create template from default rules
python migrate_default_rules.py template

# Migrate default rules to database
python migrate_default_rules.py migrate

# Validate database rules
python migrate_default_rules.py validate

# Run all commands
python migrate_default_rules.py all
```

## File Structure

```
app/
├── main.py                          # Fixed auto-reinitialization
├── api/antigen.py                   # Enhanced rule management endpoints
├── templates/antibody_rules.html    # Updated UI with new buttons
├── static/js/antibody_rules.js      # Added export/import functionality
├── migrate_default_rules.py         # Migration script
└── ANTIBODY_RULES_MIGRATION.md      # This documentation
```

## Migration Process

### Phase 1: Database Persistence (Complete) ✅
- Fixed auto-reinitialization in `main.py`
- Custom rules now persist across restarts
- Added proper initialization logic

### Phase 2: Enhanced Management (Complete) ✅
- Added export/import functionality
- Enhanced UI with new management buttons
- Created migration tools

### Phase 3: Future Enhancements (Planned)
- Remove dependency on `default_rules.py`
- Create rule template library
- Add rule validation and testing tools
- Implement rule versioning

## Benefits

1. **Data Persistence**: Custom rules no longer lost on restart
2. **Flexibility**: Import/export rules for backup and sharing
3. **Safety**: Non-destructive operations by default
4. **Migration**: Tools to transition from default to custom rules
5. **Validation**: Verify rule integrity and completeness

## Troubleshooting

### Rules Not Persisting
- Check that `main.py` changes are applied
- Verify database file permissions
- Check server logs for initialization messages

### Import/Export Issues
- Ensure JSON file format is correct
- Check browser console for JavaScript errors
- Verify API endpoint responses

### Migration Script Issues
- Ensure database path is correct
- Check Python dependencies
- Verify file permissions for template creation

## Next Steps

1. **Test the new functionality** with existing rules
2. **Export current rules** as backup
3. **Import rules** to verify functionality
4. **Remove default_rules.py dependency** (future phase)
5. **Create rule template library** (future phase)

## API Reference

### Export Rules
```http
GET /api/antibody-rules/export
```

**Response**:
```json
{
  "template_name": "Exported Antibody Rules",
  "export_date": "2024-01-01T12:00:00",
  "rule_count": 25,
  "rules": [...]
}
```

### Import Rules
```http
POST /api/antibody-rules/import
Content-Type: application/json

{
  "rules": [...],
  "clear_existing": false
}
```

### Reset to Defaults
```http
POST /api/antibody-rules/reset
```

### Add Default Rules
```http
POST /api/antibody-rules/initialize
``` 