
import neo4j, { Driver, Session } from 'neo4j-driver';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

// Configuration from environment variables
const NEO4J_URI = process.env.NEO4J_URI || 'neo4j+s://73c9bec5.databases.neo4j.io';
const NEO4J_USERNAME = process.env.NEO4J_USERNAME || 'neo4j';
const NEO4J_PASSWORD = process.env.NEO4J_PASSWORD;
const NEO4J_DATABASE = process.env.NEO4J_DATABASE || 'neo4j';
const INSTANCE_NAME = process.env.AURA_INSTANCENAME || 'Unknown';
const INSTANCE_ID = process.env.AURA_INSTANCEID || 'Unknown';

interface DatabaseInfo {
  name: string;
  version: string;
  nodeCount: number;
  relationshipCount: number;
  labels: string[];
}

class Neo4jConnection {
  private driver: Driver | null = null;

  /**
   * Validate that all required environment variables are set
   */
  public validateEnvironment(): boolean {
    const requiredVars = {
      'NEO4J_PASSWORD': NEO4J_PASSWORD
    };

    const missingVars: string[] = [];
    for (const [varName, varValue] of Object.entries(requiredVars)) {
      if (!varValue) {
        missingVars.push(varName);
      }
    }

    if (missingVars.length > 0) {
      console.log('❌ Missing required environment variables:');
      missingVars.forEach(varName => {
        console.log(`   - ${varName}`);
      });
      console.log();
      console.log('💡 Make sure you have a .env file with:');
      console.log('   NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io');
      console.log('   NEO4J_PASSWORD=your_password');
      console.log('   NEO4J_USERNAME=neo4j');
      console.log('   NEO4J_DATABASE=neo4j');
      return false;
    }

    return true;
  }

  /**
   * Connect to Neo4j Aura instance
   */
  async connect(): Promise<boolean> {
    try {
      console.log('🔌 Connecting to Neo4j Aura Instance');
      console.log(`   Instance Name: ${INSTANCE_NAME}`);
      console.log(`   Instance ID: ${INSTANCE_ID}`);
      console.log(`   URI: ${NEO4J_URI}`);
      console.log(`   Database: ${NEO4J_DATABASE}`);
      console.log(`   Username: ${NEO4J_USERNAME}`);
      console.log();

      this.driver = neo4j.driver(
        NEO4J_URI,
        neo4j.auth.basic(NEO4J_USERNAME, NEO4J_PASSWORD!)
      );

      // Verify connectivity
      const serverInfo = await this.driver.getServerInfo();
      console.log('✅ Successfully connected to Neo4j!');
      console.log(`   Server: ${serverInfo.address}`);
      console.log();

      return true;

    } catch (error: any) {
      if (error.code === 'Neo.ClientError.Security.Unauthorized') {
        console.log('❌ Authentication failed!');
        console.log('   - Check your username and password in .env file');
        console.log('   - Verify credentials are correct');
      } else if (error.code === 'ServiceUnavailable') {
        console.log('❌ Service unavailable!');
        console.log('   - Check if the instance is running (login to console.neo4j.io)');
        console.log('   - Wait 60 seconds after instance creation');
        console.log('   - Verify the URI is correct in .env file');
      } else {
        console.log(`❌ Connection error: ${error.message}`);
      }
      return false;
    }
  }

  /**
   * Get basic database statistics
   */
  async getDatabaseInfo(): Promise<DatabaseInfo | null> {
    if (!this.driver) {
      console.log('❌ No active connection');
      return null;
    }

    try {
      const session = this.driver.session({ database: NEO4J_DATABASE });

      // Get version
      const versionResult = await session.run(
        'CALL dbms.components() YIELD name, versions RETURN name, versions'
      );
      const versionRecord = versionResult.records[0];

      // Count nodes
      const nodeResult = await session.run('MATCH (n) RETURN count(n) as count');
      const nodeCount = nodeResult.records[0].get('count').toNumber();

      // Count relationships
      const relResult = await session.run('MATCH ()-[r]->() RETURN count(r) as count');
      const relCount = relResult.records[0].get('count').toNumber();

      // Get labels
      const labelResult = await session.run('CALL db.labels() YIELD label RETURN collect(label) as labels');
      const labels = labelResult.records[0].get('labels');

      await session.close();

      const info: DatabaseInfo = {
        name: versionRecord?.get('name') || 'Unknown',
        version: versionRecord?.get('versions')?.[0] || 'Unknown',
        nodeCount,
        relationshipCount: relCount,
        labels
      };

      console.log('📊 Database Information:');
      console.log(`   Name: ${info.name}`);
      console.log(`   Version: ${info.version}`);
      console.log();
      console.log('📈 Statistics:');
      console.log(`   Nodes: ${info.nodeCount}`);
      console.log(`   Relationships: ${info.relationshipCount}`);
      console.log(`   Labels: ${info.labels.length}`);
      if (info.labels.length > 0) {
        console.log(`   Label Types: ${info.labels.join(', ')}`);
      }
      console.log();

      return info;

    } catch (error: any) {
      console.log(`⚠️  Could not retrieve info: ${error.message}\n`);
      return null;
    }
  }

  /**
   * Run simple read-only test to verify connection works
   */
  async runTestOperations(): Promise<boolean> {
    if (!this.driver) {
      console.log('❌ No active connection');
      return false;
    }

    try {
      console.log('🧪 Running Connection Test...');

      const session = this.driver.session({ database: NEO4J_DATABASE });

      // Simple read-only query to test connection
      const result = await session.run('RETURN 1 as test');
      const testValue = result.records[0].get('test');
      console.log(`   ✅ Query executed successfully: ${testValue}`);

      await session.close();
      console.log('✅ Connection test successful!\n');
      return true;

    } catch (error: any) {
      console.log(`❌ Connection test failed: ${error.message}\n`);
      return false;
    }
  }


  /**
   * Close the connection
   */
  async close(): Promise<void> {
    if (this.driver) {
      await this.driver.close();
      this.driver = null;
    }
  }
}

/**
 * Main execution function
 */
async function main(): Promise<void> {
  console.log('='.repeat(80));
  console.log('Neo4j Aura Instance Connection (TypeScript)');
  console.log('='.repeat(80));
  console.log();

  const connection = new Neo4jConnection();

  // Validate environment
  if (!connection.validateEnvironment()) {
    process.exit(1);
  }

  // Connect
  const connected = await connection.connect();
  if (!connected) {
    console.log('💡 Troubleshooting Tips:');
    console.log('   1. Check your .env file exists and has correct values');
    console.log('   2. Wait 60-90 seconds after instance creation');
    console.log('   3. Check instance status at: https://console.neo4j.io');
    console.log('   4. Verify instance shows \'Running\' status (green indicator)');
    console.log('   5. Check your internet connection');
    process.exit(1);
  }

  // Get database info
  await connection.getDatabaseInfo();

  // Test operations
  await connection.runTestOperations();

  // Close connection
  await connection.close();

  console.log('='.repeat(80));
  console.log('✅ Connection test complete!');
  console.log('='.repeat(80));
  console.log();
  console.log('💡 Next Steps:');
  console.log('   - Your Neo4j instance is ready');
  console.log('   - Connection test successful');
  console.log('   - Ready for data operations');
  console.log();
}

// Run the main function
if (require.main === module) {
  main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
  });
}

export { Neo4jConnection };
