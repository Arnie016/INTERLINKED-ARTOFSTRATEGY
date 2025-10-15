# Quick Start: Mock Data Generation

This guide will help you get started with the mock data generation feature in under 5 minutes.

## Prerequisites

1. **Backend Dependencies Installed**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Neo4j Running** (Optional - for graph visualization)
   - If Neo4j is not running, data will still be generated to files
   - See main README for Neo4j setup

3. **Backend API Running**
   ```bash
   cd backend/api
   python main.py
   # API should be running on http://localhost:8000
   ```

4. **Frontend Running**
   ```bash
   cd frontend
   npm install  # if first time
   npm run dev
   # Frontend should be running on http://localhost:3000
   ```

## Using the UI (Recommended)

### Step 1: Open the Application
Navigate to http://localhost:3000 in your browser

### Step 2: Generate Mock Data
1. **Enter a company name** (e.g., "Acme Corporation")
2. **Select company size:**
   - **Small** (10-50 employees) - Best for quick testing
   - **Medium** (50-200 employees) - Good balance
   - **Large** (200-1000 employees) - Comprehensive testing
3. **Click "Generate Data"**

### Step 3: Wait for Generation
- Progress indicator will show while generating
- Small: ~2-5 seconds
- Medium: ~5-10 seconds
- Large: ~15-30 seconds

### Step 4: View Results
- Graph will automatically refresh
- Click nodes and edges to see details
- View generated files in `data/` directory

## Using the API Directly

```bash
curl -X POST http://localhost:8000/api/generate-sample-data \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Company",
    "company_size": "small",
    "generate_files": true
  }'
```

## Using Python Module Directly

```python
from backend.tools.mock_generation import generate_mock_data

# Generate data
result = generate_mock_data(
    company_name="My Company",
    company_size="medium"
)

print(f"Generated {result['statistics']['total_employees']} employees")
print(f"Files: {result['files']}")
```

## What Gets Generated

### Entities (Nodes)
- ✅ **Employees** - Realistic names, roles, departments, skills
- ✅ **Departments** - Engineering, Sales, Marketing, etc.
- ✅ **Projects** - With budgets, timelines, teams
- ✅ **Systems** - Slack, GitHub, Salesforce, etc.
- ✅ **Processes** - Business processes by department

### Relationships (Edges)
- ✅ **REPORTS_TO** - Organizational hierarchy
- ✅ **BELONGS_TO** - Department membership
- ✅ **WORKS_ON** - Project assignments
- ✅ **USES** - System usage
- ✅ **OWNS** - Process ownership
- ✅ **PERFORMS** - Process participation

### Communication Data
- ✅ **Slack Messages** - Channel activity, threads, reactions
- ✅ **Emails** - Send/receive patterns, response times
- ✅ **Calendar Events** - Meetings, attendees, recurrence

## Output Files

Generated files are saved to `data/` directory:

```
data/
├── company_name_entities_20241015_143000.json
├── company_name_relationships_20241015_143000.json
├── company_name_communications_20241015_143000.json
└── company_name_summary_20241015_143000.json
```

## Testing the Installation

Run the test script to verify everything works:

```bash
cd backend
python test_mock_generation.py
```

Expected output:
```
============================================================
MOCK DATA GENERATION TEST SUITE
============================================================

Testing Small Company Generation
============================================================
Generating organizational data for Small Tech Startup (small)...
✓ Generated 6 departments
✓ Generated 35 employees
...

ALL TESTS PASSED! ✓
```

## Common Issues

### Issue: "Faker library not available"
**Solution:** Install Faker
```bash
pip install Faker
```

### Issue: "No space left on device"
**Solution:** Clean up old files in `data/` directory
```bash
cd data
rm *.json  # Remove old generated files
```

### Issue: "Neo4j connection failed"
**Solution:** Data generation will still work, files will be saved. To fix Neo4j:
1. Check `.env` file in backend directory
2. Verify Neo4j is running
3. Check credentials

### Issue: Backend not responding
**Solution:** Restart the backend
```bash
cd backend/api
python main.py
```

## Example Use Cases

### 1. Testing Agent Queries
Generate a small company, then ask agents questions:
```
"Who reports to the Engineering Director?"
"What projects is Alice working on?"
"Which systems are used by the Sales team?"
```

### 2. Performance Testing
Generate a large company to test graph performance:
- 200-1000 employees
- 40-100 projects
- Hundreds of relationships

### 3. Demo Scenarios
Generate medium company with realistic data:
- Present organizational structure
- Show collaboration patterns
- Demonstrate insights

## Next Steps

After generating data:

1. **Explore the Graph** - Click nodes to see details
2. **Ask Agent Questions** - Use the chat interface
3. **Analyze Files** - Open JSON files in `data/` directory
4. **Customize Generation** - Modify `mock_generation.py` for your needs

## Advanced Usage

See `MOCK_DATA_GENERATION_IMPLEMENTATION.md` for:
- Detailed architecture
- Data schema reference
- Extending the generator
- Adding new entity types
- Custom data sources

## Need Help?

- Check `MOCK_DATA_GENERATION_IMPLEMENTATION.md` for comprehensive docs
- Run `python backend/test_mock_generation.py` to verify installation
- Check backend logs in terminal for error messages
- Ensure all dependencies are installed

---

**Happy Testing!** 🎉

Now you have realistic organizational data to work with. Start exploring the graph and testing agent capabilities!

