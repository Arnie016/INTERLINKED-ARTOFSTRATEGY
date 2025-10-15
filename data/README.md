# Generated Organizational Data

This directory contains generated mock organizational data files created by the data generation system.

## File Types

### 1. Entity Files
**Format:** `{CompanyName}_Entities_{YYYY-MM-DD_HHMMSS}.json`

Contains all organizational entities:
- Employees (Person nodes)
- Departments
- Projects
- Systems/Applications
- Business Processes

**Example:** `Acme_Corporation_Entities_2024-10-15_143000.json`

### 2. Relationship Files
**Format:** `{CompanyName}_Relationships_{YYYY-MM-DD_HHMMSS}.json`

Contains all relationships between entities:
- Reporting lines (REPORTS_TO)
- Department membership (BELONGS_TO)
- Project assignments (WORKS_ON)
- System usage (USES)
- Process ownership (OWNS)
- Process participation (PERFORMS)

**Example:** `Acme_Corporation_Relationships_2024-10-15_143000.json`

### 3. Communication Files
**Format:** `{CompanyName}_Communications_{YYYY-MM-DD_HHMMSS}.json`

Contains communication and interaction data:
- Slack message metadata
- Email metadata
- Calendar event data

**Example:** `Acme_Corporation_Communications_2024-10-15_143000.json`

### 4. Summary Files
**Format:** `{CompanyName}_Summary_{YYYY-MM-DD_HHMMSS}.json`

Contains generation statistics and metadata:
- Total counts for each entity type
- Generation timestamp
- Company size
- File paths

**Example:** `Acme_Corporation_Summary_2024-10-15_143000.json`

## Data Usage

These files can be used for:
- **Analysis:** Import into analytics tools for organizational analysis
- **Backup:** Store organizational snapshots
- **Testing:** Use as test data for agent development
- **Auditing:** Track what data was generated and when
- **Export:** Share data with external tools

## File Retention

Files are automatically generated with timestamps to prevent overwrites. You may want to:
- Periodically clean up old files
- Archive files you want to keep
- Delete files that are no longer needed

## Privacy Notice

All data in this directory is **synthetic/mock data**. No real organizational or personal information is contained in these files.

## Integration

These files are automatically generated when using the "Generate Data" feature in the frontend UI. The data is simultaneously:
1. Saved to these JSON files
2. Inserted into the Neo4j graph database

## Example File Structure

### Entities File
```json
{
  "company_name": "Acme Corporation",
  "company_size": "medium",
  "generated_at": "2024-10-15T14:30:00",
  "employees": [...],
  "departments": [...],
  "projects": [...],
  "systems": [...],
  "processes": [...]
}
```

### Relationships File
```json
{
  "reporting": [...],
  "collaboration": [...],
  "project_assignments": [...],
  "system_usage": [...],
  "process_ownership": [...],
  "department_membership": [...]
}
```

### Communications File
```json
{
  "company_name": "Acme Corporation",
  "generated_at": "2024-10-15T14:30:00",
  "slack_messages": [...],
  "emails": [...],
  "calendar_events": [...]
}
```

## Need Help?

See `MOCK_DATA_GENERATION_IMPLEMENTATION.md` in the project root for comprehensive documentation.

