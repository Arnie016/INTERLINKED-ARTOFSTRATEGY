'use client'

import React, { useState, useEffect } from 'react'
import AgentChat from '../components/AgentChat'
import GraphVisualization from '../components/GraphVisualization'
import { Brain, Network, Database, Settings, RefreshCw } from 'lucide-react'

interface GraphData {
  nodes: Array<{
    id: string
    label: string
    type: string
    properties: Record<string, any>
  }>
  edges: Array<{
    id: string
    source: string
    target: string
    type: string
    properties: Record<string, any>
  }>
}

export default function HomePage() {
  const [graphData, setGraphData] = useState<GraphData | undefined>()
  const [selectedNode, setSelectedNode] = useState<any>(null)
  const [selectedEdge, setSelectedEdge] = useState<any>(null)
  const [isConnected, setIsConnected] = useState(false)
  const [neo4jStatus, setNeo4jStatus] = useState<string>("unknown")
  const [companyName, setCompanyName] = useState<string>("")
  const [companySize, setCompanySize] = useState<string>("medium")
  const [isGeneratingData, setIsGeneratingData] = useState(false)

  // Check API connection on mount
  useEffect(() => {
    checkConnection()
    // Retry connection check every 5 seconds if not connected
    const interval = setInterval(() => {
      if (!isConnected) {
        checkConnection()
      }
    }, 5000)
    
    return () => clearInterval(interval)
  }, [isConnected])

  // Auto-load graph data when connected
  useEffect(() => {
    if (isConnected && !graphData) {
      loadInitialGraphData()
    }
  }, [isConnected, graphData])

  const checkConnection = async () => {
    try {
      console.log('Attempting to connect to backend...')
      const response = await fetch('/api/health', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        mode: 'cors',
      })
      console.log('Health check response:', response.status, response.ok)
      const data = await response.json()
      console.log('Health check data:', data)
      setIsConnected(response.ok)
      setNeo4jStatus(data.neo4j_status || "unknown")
    } catch (error) {
      console.error('Health check failed:', error)
      setIsConnected(false)
    }
  }

  const loadInitialGraphData = async () => {
    try {
      console.log('Loading initial graph data from Neo4j...')
      const response = await fetch('/api/graph-context', {
        method: 'GET',
        headers: {
          'Accept': 'application/json',
        },
        mode: 'cors',
      })
      
      if (response.ok) {
        const data = await response.json()
        console.log('Graph data loaded:', data)
        console.log(`Received ${data.nodes?.length || 0} nodes and ${data.edges?.length || 0} edges`)
        
        // Log edge types for debugging
        if (data.edges) {
          const edgeTypes: Record<string, number> = {}
          data.edges.forEach((edge: any) => {
            const type = edge.type || 'Unknown'
            edgeTypes[type] = (edgeTypes[type] || 0) + 1
          })
          console.log('Edge types received:', edgeTypes)
        }
        
        setGraphData(data)
      } else {
        console.error('Failed to load graph data:', response.status, response.statusText)
      }
    } catch (error) {
      console.error('Error loading graph data:', error)
    }
  }

  const handleGraphUpdate = (data: GraphData) => {
    setGraphData(data)
  }

  const handleNodeClick = (node: any) => {
    setSelectedNode(node)
    setSelectedEdge(null)
  }

  const handleEdgeClick = (edge: any) => {
    setSelectedEdge(edge)
    setSelectedNode(null)
  }

  const generateSampleData = async () => {
    if (!companyName.trim()) {
      alert('Please enter a company name first')
      return
    }

    setIsGeneratingData(true)
    try {
      console.log('Generating sample data for company:', companyName)
      
      // Call the backend to generate comprehensive sample data
      const response = await fetch('/api/generate-sample-data', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          company_name: companyName,
          company_size: companySize,
          generate_files: true
        })
      })

      if (response.ok) {
        const result = await response.json()
        console.log('Sample data generated:', result)
        
        // Reload the graph data to show the new sample data
        await loadInitialGraphData()
        
        alert(`Successfully generated sample data for ${companyName}!`)
      } else {
        throw new Error('Failed to generate sample data')
      }
    } catch (error) {
      console.error('Error generating sample data:', error)
      alert('Failed to generate sample data. Please try again.')
    } finally {
      setIsGeneratingData(false)
    }
  }

  return (
    <div className="h-screen flex flex-col bg-gray-100 dark:bg-gray-900 overflow-hidden">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 shadow-sm border-b border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center space-x-3">
              <Brain className="h-7 w-7 text-blue-600 dark:text-blue-400" />
              <div>
                <h1 className="text-xl font-bold text-gray-900 dark:text-gray-100">OrgMind AI</h1>
                <p className="text-xs text-gray-500 dark:text-gray-400">Strategy Copilot</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  {isConnected ? 'API Connected' : 'API Disconnected'}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${
                  neo4jStatus === 'connected' ? 'bg-green-500' : 
                  neo4jStatus === 'disconnected' ? 'bg-yellow-500' : 
                  'bg-red-500'
                }`}></div>
                <span className="text-sm text-gray-600 dark:text-gray-300">
                  Neo4j: {neo4jStatus}
                </span>
              </div>
              <button
                onClick={checkConnection}
                className="p-2 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                title="Check Connection"
              >
                <Settings className="h-4 w-4" />
              </button>
              <button
                onClick={() => {
                  console.log('Manual connection test...')
                  checkConnection()
                }}
                className="px-3 py-1 text-sm bg-blue-600 dark:bg-blue-500 text-white rounded-md hover:bg-blue-700 dark:hover:bg-blue-600 transition-colors"
                title="Test Connection"
              >
                Test
              </button>
              <button
                onClick={loadInitialGraphData}
                className="px-3 py-1 text-sm bg-green-600 dark:bg-green-500 text-white rounded-md hover:bg-green-700 dark:hover:bg-green-600 transition-colors"
                title="Load Graph Data"
              >
                Load Graph
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 overflow-hidden">
        {!isConnected ? (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6 text-center">
            <Database className="h-12 w-12 mx-auto mb-4 text-red-500" />
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200 mb-2">Backend Not Connected</h2>
            <p className="text-red-600 dark:text-red-300 mb-4">
              Please start the FastAPI backend server to use the application.
            </p>
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg p-4 text-left max-w-md mx-auto">
              <p className="text-sm font-mono text-gray-800 dark:text-gray-200">
                cd backend/api<br />
                python main.py
              </p>
            </div>
          </div>
        ) : (
          <div className="h-full flex flex-col space-y-3">
            {/* Company Setup and Graph Controls */}
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm p-3 flex-shrink-0">
              <div className="flex items-center justify-between">
                {/* Left side - Title and stats */}
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Network className="h-4 w-4 text-green-600 dark:text-green-400" />
                    <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {graphData ? `${graphData.nodes.length} nodes, ${graphData.edges.length} relationships` : 'Strategy Copilot'}
                    </h2>
                  </div>
                  {graphData && (
                    <div className="text-xs text-gray-500 dark:text-gray-400">
                      {graphData.nodes.filter(n => n.type === 'Person').length} People,{' '}
                      {graphData.nodes.filter(n => n.type === 'Department').length} Departments,{' '}
                      {graphData.nodes.filter(n => n.type === 'Project').length} Projects,{' '}
                      {graphData.nodes.filter(n => n.type === 'System').length} Systems,{' '}
                      {graphData.nodes.filter(n => n.type === 'Process').length} Processes
                    </div>
                  )}
                </div>
                
                {/* Center - Company Setup */}
                <div className="flex items-center space-x-3">
                  <input
                    type="text"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    placeholder="Company name..."
                    className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  />
                  <select
                    value={companySize}
                    onChange={(e) => setCompanySize(e.target.value)}
                    className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
                  >
                    <option value="small">Small (5 employees)</option>
                    <option value="medium">Medium (15 employees)</option>
                    <option value="large">Large (30 employees)</option>
                  </select>
                  <button
                    onClick={generateSampleData}
                    disabled={!companyName.trim() || isGeneratingData}
                    className="px-3 py-1 bg-green-600 dark:bg-green-500 text-white rounded-md hover:bg-green-700 dark:hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center space-x-1"
                  >
                    {isGeneratingData ? (
                      <>
                        <div className="animate-spin rounded-full h-3 w-3 border-b border-white"></div>
                        <span>Generating...</span>
                      </>
                    ) : (
                      <span>Generate Data</span>
                    )}
                  </button>
                </div>
                
                {/* Right side - Graph Controls */}
                <div className="flex items-center space-x-1">
                  <button
                    onClick={loadInitialGraphData}
                    className="p-1.5 text-gray-600 dark:text-gray-300 hover:text-gray-800 dark:hover:text-gray-100 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                    title="Refresh Graph"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </button>
                </div>
              </div>
            </div>

            {/* Side-by-side layout: Chat (left) and Graph (right) */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-3 overflow-hidden">
              {/* Chat Panel */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden">
                <AgentChat onGraphUpdate={handleGraphUpdate} />
              </div>

              {/* Graph Panel */}
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm overflow-hidden">
                <GraphVisualization
                  data={graphData}
                  onNodeClick={handleNodeClick}
                  onEdgeClick={handleEdgeClick}
                />
              </div>
            </div>
          </div>
        )}

        {/* Details Panel */}
        {(selectedNode || selectedEdge) && (
          <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {selectedNode ? 'Node Details' : 'Edge Details'}
              </h3>
            </div>
            <div className="p-4">
              {selectedNode && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">ID</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100 font-mono">{selectedNode.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Label</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100">{selectedNode.label}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Type</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100">{selectedNode.type}</p>
                  </div>
                  {Object.keys(selectedNode.properties || {}).length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Properties</label>
                      <div className="mt-1 bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                        <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-auto">
                          {JSON.stringify(selectedNode.properties, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
              
              {selectedEdge && (
                <div className="space-y-3">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">ID</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100 font-mono">{selectedEdge.id}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Type</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100">{selectedEdge.type}</p>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Source → Target</label>
                    <p className="text-sm text-gray-900 dark:text-gray-100 font-mono">
                      {selectedEdge.source} → {selectedEdge.target}
                    </p>
                  </div>
                  {Object.keys(selectedEdge.properties || {}).length > 0 && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">Properties</label>
                      <div className="mt-1 bg-gray-50 dark:bg-gray-700 rounded-md p-3">
                        <pre className="text-xs text-gray-800 dark:text-gray-200 overflow-auto">
                          {JSON.stringify(selectedEdge.properties, null, 2)}
                        </pre>
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 flex-shrink-0">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <Network className="h-4 w-4 text-gray-400 dark:text-gray-500" />
              <span className="text-xs text-gray-500 dark:text-gray-400">
                Agent Tool Architecture v1.0.0
              </span>
            </div>
            <div className="text-xs text-gray-500 dark:text-gray-400">
              Powered by Neo4j, SageMaker RL, Exa.ai, and Cytoscape.js
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
