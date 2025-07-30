# Blood Bank Antibody Identification System - Postman Collection

## 📋 Overview

This Postman collection provides comprehensive testing for the Blood Bank Antibody Identification System API. The collection includes all CRUD operations for Templates, Antigens, Antibody Rules, Antigrams, Patient Reactions, and Cell Finding functionality.

## 🚀 Quick Start

### 1. Import the Collection
1. Open Postman
2. Click "Import" button
3. Select the `Blood_Bank_API_Collection.json` file
4. The collection will be imported with all requests organized by functionality

### 2. Set Up Environment Variables
The collection uses the following environment variables:
- `base_url`: The base URL of your API (default: `http://localhost:5000`)
- `template_id`: Template ID for testing (default: `1752694582796`)
- `antigram_id`: Antigram ID for testing (default: `1752694582796`)
- `rule_id`: Antibody rule ID for testing (default: `1`)
- `antigen_name`: Antigen name for testing (default: `D`)

### 3. Start the Flask Application
```bash
# Set environment variable for local database
$env:USE_LOCAL_DB="true"

# Start the Flask application
python main.py
```

## 📚 Collection Structure

### 1. Template Management
**Purpose**: CRUD operations for antigram templates that define the structure for creating antigrams.

**Endpoints**:
- `GET /api/templates` - Get all templates
- `GET /api/templates/{id}` - Get template by ID
- `POST /api/templates` - Create new template
- `PUT /api/templates/{id}` - Update template
- `DELETE /api/templates/{id}` - Delete template

**Key Features**:
- Template validation for antigen orders
- Cell range validation
- Integration with valid antigens only

### 2. Antigen Management
**Purpose**: Manage blood group antigens and their systems.

**Endpoints**:
- `GET /api/antigens` - Get all antigens
- `GET /api/antigens/valid` - Get only valid antigens (with antibody rules)
- `GET /api/antigens/default-order` - Get default antigen order
- `GET /api/antigens/pairs` - Get antigen pairs for homozygous rules
- `POST /api/antigens` - Create new antigen
- `DELETE /api/antigens/{name}` - Delete antigen
- `POST /api/antigens/initialize` - Initialize base antigens

**Key Features**:
- Separate endpoints for all vs valid antigens
- Default antigen order (Panocell order)
- Antigen pairs for homozygous rule creation

### 3. Antibody Rules
**Purpose**: Manage antibody identification rules with different rule types.

**Endpoints**:
- `GET /api/antibody-rules` - Get all rules
- `GET /api/antibody-rules/{id}` - Get rule by ID
- `POST /api/antibody-rules` - Create new rule
- `PUT /api/antibody-rules/{id}` - Update rule
- `DELETE /api/antibody-rules/{id}` - Delete rule
- `DELETE /api/antibody-rules/delete-all` - Delete all rules
- `POST /api/antibody-rules/initialize` - Initialize default rules

**Rule Types**:
- **SingleAG**: Simple antigen ruling out
- **Homo**: Homozygous rule with antigen pairs
- **Hetero**: Heterozygous rule with required counts
- **ABSpecificRO**: Antibody-specific ruling out
- **LowF**: Low frequency antigen automatic ruling out

### 4. Antigram Management
**Purpose**: Manage blood cell panels with antigen reactions.

**Endpoints**:
- `GET /api/antigrams` - Get all antigrams (with optional search)
- `GET /api/antigrams/{id}` - Get antigram by ID with cell reactions
- `POST /api/antigrams` - Create new antigram using template
- `PUT /api/antigrams/{id}` - Update antigram
- `DELETE /api/antigrams/{id}` - Delete antigram
- `DELETE /api/antigrams/delete-all-antigrams` - Delete all antigrams

**Key Features**:
- Template-based antigram creation
- Cell reaction data storage
- Lot number and expiration date tracking

### 5. Patient Reactions
**Purpose**: Manage patient test results against antigram cells.

**Endpoints**:
- `GET /api/patient-reactions` - Get all patient reactions
- `POST /api/patient-reactions` - Add single reaction
- `POST /api/patient-reactions/batch` - Add batch reactions
- `DELETE /api/delete-patient-reaction` - Delete specific reaction
- `DELETE /api/clear-patient-reactions` - Clear all reactions

**Key Features**:
- Individual and batch reaction management
- MultiIndex storage for efficient lookup
- Integration with antibody identification

### 6. Antibody Identification
**Purpose**: Perform antibody identification using patient reactions and rules.

**Endpoints**:
- `GET /api/antibody-identification` - Get identification results
- `GET /api/abid` - Alternative identification endpoint

**Key Features**:
- Rule-based antigen ruling out
- Detailed ruling out explanations
- Possible antibody suggestions

### 7. Cell Finding
**Purpose**: Search for cells with specific antigen patterns.

**Endpoints**:
- `POST /cell_finder` - Find cells by antigen pattern

**Key Features**:
- Pattern matching across all antigrams
- Detailed cell reaction information
- Lot number and antigram identification

### 8. Validation & Debug
**Purpose**: Validate system integrity and debug issues.

**Endpoints**:
- `GET /api/validate-rules` - Validate all antibody rules
- `GET /api/validate-rules/summary` - Get validation summary
- `GET /api/validate-rules/missing` - Get antigens without rules
- `GET /api/debug/patient-reactions` - Debug patient reactions

**Key Features**:
- Rule conflict detection
- Missing antigen identification
- System health monitoring

## 🧪 Testing Workflow

### 1. Initial Setup
```bash
# 1. Initialize base antigens
POST /api/antigens/initialize

# 2. Initialize default antibody rules
POST /api/antibody-rules/initialize
```

### 2. Template Creation
```bash
# 1. Get valid antigens for template
GET /api/antigens/valid

# 2. Create template with valid antigens
POST /api/templates
{
  "name": "Standard Panel",
  "antigen_order": ["D", "C", "c", "E", "e", "K", "k", "Fya", "Fyb"],
  "cell_count": 10,
  "cell_range": [1, 10]
}
```

### 3. Antigram Creation
```bash
# 1. Get available templates
GET /api/templates

# 2. Create antigram using template
POST /api/antigrams
{
  "template_id": 1752694582796,
  "lot_number": "ABC123",
  "expiration_date": "2024-12-31",
  "cells": [
    {
      "cell_number": "1",
      "reactions": {
        "D": "+",
        "C": "+",
        "c": "0",
        "E": "0",
        "e": "+"
      }
    }
  ]
}
```

### 4. Patient Reactions
```bash
# 1. Add patient reactions
POST /api/patient-reactions/batch
{
  "reactions": {
    "1752694582796": {
      "1": "+",
      "2": "0",
      "3": "+",
      "4": "0",
      "5": "+"
    }
  }
}
```

### 5. Antibody Identification
```bash
# 1. Get identification results
GET /api/antibody-identification
```

### 6. Cell Finding
```bash
# 1. Find cells with specific pattern
POST /cell_finder
{
  "search_pattern": {
    "D": "+",
    "C": "+",
    "c": "0",
    "E": "0",
    "e": "+"
  }
}
```

## 🔧 Common Test Scenarios

### Scenario 1: Complete Antibody Identification Workflow
1. Initialize system (antigens + rules)
2. Create template with valid antigens
3. Create antigram using template
4. Add patient reactions
5. Perform antibody identification
6. Validate results

### Scenario 2: Template Management
1. Create multiple templates
2. Update template antigen order
3. Delete template
4. Validate template integrity

### Scenario 3: Rule Management
1. Create different rule types
2. Update rule parameters
3. Enable/disable rules
4. Validate rule conflicts

### Scenario 4: Cell Finding
1. Create antigrams with known patterns
2. Search for specific antigen combinations
3. Verify search results
4. Test edge cases

## 🚨 Error Handling

The collection includes examples of common error responses:

### Validation Errors
- Missing required fields
- Invalid antigen names
- Invalid rule types
- Cell range validation errors

### Not Found Errors
- Template not found
- Antigram not found
- Rule not found
- Antigen not found

### Conflict Errors
- Antigen already exists
- Template already exists

## 📊 Response Validation

Each request includes:
- **Status Code Validation**: Ensures proper HTTP status codes
- **Content-Type Validation**: Verifies JSON responses
- **Response Time Validation**: Checks performance (under 2000ms)
- **Schema Validation**: Validates response structure

## 🔍 Debugging Tips

### 1. Check System Health
```bash
GET /api/validate-rules
GET /api/debug/patient-reactions
```

### 2. Verify Data Integrity
```bash
GET /api/antigens/valid
GET /api/antibody-rules
GET /api/templates
```

### 3. Monitor Performance
- Check response times in Postman
- Use validation endpoints to identify issues
- Review debug information for data consistency

## 📝 Notes

### Environment Setup
- Ensure Flask application is running on `http://localhost:5000`
- Set `USE_LOCAL_DB=true` for local development
- Database will be automatically initialized on first run

### Data Persistence
- All data is automatically saved to database
- Templates, antigrams, and reactions persist between sessions
- Use delete endpoints to clean up test data

### API Consistency
- All endpoints return consistent JSON responses
- Error messages include detailed information
- Status codes follow REST conventions

## 🎯 Best Practices

1. **Test Setup**: Always initialize antigens and rules first
2. **Data Cleanup**: Use delete endpoints to clean up test data
3. **Validation**: Use validation endpoints to check system health
4. **Error Handling**: Test both success and error scenarios
5. **Performance**: Monitor response times for performance issues

## 🔗 Related Documentation

- [API Documentation](README.md)
- [Rule Creation Guide](RULE_CREATION_GUIDE.md)
- [Database Schema](models.py)
- [Core Business Logic](core/)

---

**Happy Testing! 🧪🩸** 