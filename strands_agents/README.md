# Interactive Chat Interface for Organizational Graph Analysis

A powerful chat interface that allows you to interact with AI agents to analyze your organizational graph data stored in Neo4j. Ask questions about your organization's structure, people, projects, and relationships in natural language.

## 🚀 Quick Start - Chat Interface

The easiest way to interact with your organizational data is through the interactive chat interface:

```bash
# Navigate to the project directory
cd strands_agents

# Start the chat interface
python chat.py
```

That's it! You'll see a chat interface where you can ask questions about your organizational data.

## 💬 What You Can Do

Once the chat interface is running, you can:

### Ask Questions About Your Organization
- **"What departments exist in our organization?"**
- **"Who are the key people in Sales?"**
- **"What projects are currently active?"**
- **"How is our organizational structure organized?"**
- **"What systems do we use?"**

### Switch Between Different AI Agents
- **Neo4j Agent** (default) - Intelligent analysis of your organizational data
- **Query Agent** - General purpose AI assistant
- **Neo4j Tool** - Direct database queries

### Use Built-in Commands
- `help` - Show all available commands
- `stats` - Display database statistics
- `schema` - Show your data structure
- `clear` - Clear the screen
- `quit` - Exit the chat

## 🔑 Prerequisites

Before you can use the chat interface, you need to set up your credentials:

### 1. Neo4j Database Access
You need access to a Neo4j database with your organizational data. This can be:
- **Neo4j AuraDB** (cloud) - Recommended for easy setup
- **Neo4j Desktop** (local) - For local development
- **Self-hosted Neo4j** - For enterprise deployments

### 2. Required Credentials

#### Neo4j Credentials
Create a `.env` file in the `src/` directory with your Neo4j connection details:

```bash
# Neo4j Connection (Required)
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_neo4j_password
NEO4J_DATABASE=neo4j

# Optional: Instance information
AURA_INSTANCEID=your-instance-id
AURA_INSTANCENAME=your-instance-name
```

#### AWS Credentials
The system uses AWS Bedrock for AI capabilities. Set up your AWS credentials:

```bash
# Option 1: AWS CLI (Recommended)
aws configure

# Option 2: Environment Variables
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_REGION=your_region
```

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd strands_agents
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up your credentials** (see Prerequisites above)

4. **Start chatting:**
   ```bash
   python chat.py
   ```

## 🎯 Why Use This Chat Interface?

### For Business Users
- **Natural Language Queries** - Ask questions in plain English
- **No Technical Knowledge Required** - No need to learn Cypher or database queries
- **Instant Insights** - Get immediate answers about your organization
- **Interactive Exploration** - Discover patterns and relationships through conversation

### For Data Analysts
- **Rapid Prototyping** - Quickly explore organizational data
- **Pattern Discovery** - Find unexpected relationships and insights
- **Data Validation** - Verify data quality through natural language queries
- **Report Generation** - Get structured answers for reports and presentations

### For IT Administrators
- **System Monitoring** - Check database health and statistics
- **Schema Exploration** - Understand your data structure
- **Troubleshooting** - Diagnose data issues through conversation
- **Documentation** - Generate documentation from your actual data

## 🔧 Advanced Usage

### Direct File Execution
```bash
# Run the chat interface directly
python src/llm_interface/chat.py
```

### Programmatic Usage
```python
from src.agents.neo4j_agent import Neo4jAgent

# Create an agent instance
agent = Neo4jAgent()

# Ask questions programmatically
response = agent.query("What departments exist?")
print(response)
```

## 📊 Example Conversations

### Exploring Organizational Structure
```
🤖 Neo4j Agent > What types of entities exist in our database?
🤖 Neo4j Agent > What are the main organizational units?
🤖 Neo4j Agent > How are departments structured?
```

### Analyzing People and Roles
```
🤖 Neo4j Agent > Who are the key individuals in our organization?
🤖 Neo4j Agent > What roles exist in the Sales department?
🤖 Neo4j Agent > Who reports to whom?
```

### Project and Process Analysis
```
🤖 Neo4j Agent > What projects are currently active?
🤖 Neo4j Agent > What processes do we have?
🤖 Neo4j Agent > Which systems support our operations?
```

## 🚨 Troubleshooting

### Common Issues

**"Failed to connect to Neo4j"**
- Check your Neo4j credentials in the `.env` file
- Verify your Neo4j instance is running
- Ensure your IP is whitelisted (for AuraDB)

**"AWS credentials not found"**
- Run `aws configure` to set up AWS credentials
- Or set AWS environment variables
- Ensure you have Bedrock access in your AWS account

**"No data found"**
- Verify your Neo4j database contains organizational data
- Check that your data has proper node labels and relationships
- Try the `stats` command to see what's in your database

### Getting Help
- Use the `help` command in the chat interface
- Check the `stats` and `schema` commands to understand your data
- Ensure your credentials are properly configured

## 🔒 Security Notes

- Keep your `.env` file secure and never commit it to version control
- Use environment variables for production deployments
- Ensure your Neo4j database has proper access controls
- AWS credentials should follow least-privilege principles

## 📈 What's Next?

Once you're comfortable with the chat interface, you can:
- Explore the underlying agent architecture
- Customize the AI prompts for your specific needs
- Integrate the agents into your own applications
- Build custom tools for your organizational data

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Verify your credentials and database connection
3. Try the built-in help commands
4. Contact the development team for advanced support

---

**Ready to explore your organizational data? Run `python chat.py` and start asking questions!** 🚀