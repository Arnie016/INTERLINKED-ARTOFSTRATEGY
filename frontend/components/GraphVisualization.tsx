'use client'

import React, { useEffect, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import dagre from 'cytoscape-dagre'
import { Network, RefreshCw, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'

// Register the dagre layout
cytoscape.use(dagre)

interface GraphNode {
  id: string
  label: string
  type: string
  properties: Record<string, any>
}

interface GraphEdge {
  id: string
  source: string
  target: string
  type: string
  properties: Record<string, any>
}

interface GraphData {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

interface GraphVisualizationProps {
  data?: GraphData
  onNodeClick?: (node: GraphNode) => void
  onEdgeClick?: (edge: GraphEdge) => void
  companyName?: string
  setCompanyName?: (name: string) => void
  generateSampleData?: () => void
  isGeneratingData?: boolean
}

export default function GraphVisualization({ 
  data, 
  onNodeClick, 
  onEdgeClick,
  companyName,
  setCompanyName,
  generateSampleData,
  isGeneratingData
}: GraphVisualizationProps) {
  const containerRef = useRef<HTMLDivElement>(null)
  const cyRef = useRef<cytoscape.Core | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Initialize Cytoscape
  useEffect(() => {
    if (!containerRef.current) return

    const cy = cytoscape({
      container: containerRef.current,
      elements: [],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': '#3B82F6',
            'label': 'data(label)',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': 'white',
            'font-size': '12px',
            'font-weight': 'bold',
            'text-outline-width': 2,
            'text-outline-color': '#1E40AF',
            'width': '60px',
            'height': '60px',
            'border-width': 2,
            'border-color': '#1E40AF'
          }
        },
        {
          selector: 'node[type="Person"]',
          style: {
            'background-color': '#10B981',
            'border-color': '#059669'
          }
        },
        {
          selector: 'node[type="Process"]',
          style: {
            'background-color': '#F59E0B',
            'border-color': '#D97706'
          }
        },
        {
          selector: 'node[type="Department"]',
          style: {
            'background-color': '#8B5CF6',
            'border-color': '#7C3AED'
          }
        },
        {
          selector: 'node[type="Project"]',
          style: {
            'background-color': '#EF4444',
            'border-color': '#DC2626'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#6B7280',
            'target-arrow-color': '#6B7280',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '8px',
            'text-rotation': 'autorotate',
            'text-margin-y': -8,
            'text-background-color': 'white',
            'text-background-opacity': 0.8,
            'text-background-padding': '2px',
            'text-border-width': 1,
            'text-border-color': '#E5E7EB'
          }
        },
        {
          selector: 'edge[type="REPORTS_TO"]',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'width': 3
          }
        },
        {
          selector: 'edge[type="WORKS_WITH"]',
          style: {
            'line-color': '#10B981',
            'target-arrow-color': '#10B981',
            'width': 2
          }
        },
        {
          selector: 'edge[type="BELONGS_TO"]',
          style: {
            'line-color': '#8B5CF6',
            'target-arrow-color': '#8B5CF6',
            'width': 2
          }
        },
        {
          selector: 'edge[type="ASSIGNED_TO"]',
          style: {
            'line-color': '#F59E0B',
            'target-arrow-color': '#F59E0B',
            'width': 2
          }
        },
        {
          selector: 'edge[type="USES"]',
          style: {
            'line-color': '#EF4444',
            'target-arrow-color': '#EF4444',
            'width': 2
          }
        },
        {
          selector: 'edge[type="HEADS"]',
          style: {
            'line-color': '#DC2626',
            'target-arrow-color': '#DC2626',
            'width': 3
          }
        },
        {
          selector: 'edge[type="OWNS"]',
          style: {
            'line-color': '#7C3AED',
            'target-arrow-color': '#7C3AED',
            'width': 2
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#EF4444'
          }
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#EF4444',
            'target-arrow-color': '#EF4444',
            'width': 5
          }
        }
      ],
      layout: {
        name: 'dagre',
        rankDir: 'TB',
        spacingFactor: 1.5,
        nodeSep: 50,
        edgeSep: 20,
        rankSep: 100
      } as any,
      userZoomingEnabled: true,
      userPanningEnabled: true,
      boxSelectionEnabled: true,
      selectionType: 'single'
    })

    // Add event listeners
    cy.on('tap', 'node', (event) => {
      const node = event.target
      const nodeData = node.data()
      onNodeClick?.(nodeData)
    })

    cy.on('tap', 'edge', (event) => {
      const edge = event.target
      const edgeData = edge.data()
      onEdgeClick?.(edgeData)
    })

    cyRef.current = cy

    return () => {
      cy.destroy()
    }
  }, [onNodeClick, onEdgeClick])

  // Update graph when data changes
  useEffect(() => {
    if (!cyRef.current || !data) return

    setIsLoading(true)
    setError(null)

    try {
      console.log(`Loading graph data: ${data.nodes.length} nodes, ${data.edges.length} edges`)
      
      // Convert data to Cytoscape format
      const elements = [
        ...data.nodes.map(node => ({
          data: {
            id: node.id,
            label: node.label,
            type: node.type,
            ...node.properties
          }
        })),
        ...data.edges.map(edge => ({
          data: {
            id: edge.id,
            source: edge.source,
            target: edge.target,
            label: edge.type,
            type: edge.type,
            ...edge.properties
          }
        }))
      ]

      console.log(`Converted to Cytoscape elements: ${elements.length} total elements`)

      // Clear existing elements and add new ones
      cyRef.current.elements().remove()
      cyRef.current.add(elements)

      // Verify elements were added
      const addedNodes = cyRef.current.nodes().length
      const addedEdges = cyRef.current.edges().length
      console.log(`Cytoscape now has: ${addedNodes} nodes, ${addedEdges} edges`)

      // Apply layout with better settings for large graphs
      const layout = cyRef.current.layout({
        name: 'dagre',
        rankDir: 'TB',
        spacingFactor: 2.0,
        nodeSep: 30,
        edgeSep: 10,
        rankSep: 80,
        fit: true,
        padding: 20
      } as any)
      layout.run()

      // Fit the graph to the container
      cyRef.current.fit()

      console.log('Graph layout applied successfully')

    } catch (err) {
      console.error('Error updating graph:', err)
      setError(err instanceof Error ? err.message : 'Failed to update graph')
    } finally {
      setIsLoading(false)
    }
  }, [data])

  const refreshGraph = async () => {
    setIsLoading(true)
    try {
      const response = await fetch('http://localhost:8000/api/graph')
      if (response.ok) {
        const graphData = await response.json()
        // The parent component should handle this data update
      } else {
        throw new Error('Failed to fetch graph data')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh graph')
    } finally {
      setIsLoading(false)
    }
  }

  const zoomIn = () => {
    cyRef.current?.zoom({
      level: (cyRef.current.zoom() || 1) * 1.2,
      renderedPosition: { x: 0, y: 0 }
    })
  }

  const zoomOut = () => {
    cyRef.current?.zoom({
      level: (cyRef.current.zoom() || 1) * 0.8,
      renderedPosition: { x: 0, y: 0 }
    })
  }

  const fitToScreen = () => {
    cyRef.current?.fit()
  }

  return (
    <div className="flex flex-col h-full">
      {/* Legend - Moved to top */}
      <div className="p-2 border-b border-gray-200 bg-gray-50">
        <div className="flex flex-wrap gap-4 text-xs justify-center">
          {/* Node Types */}
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full"></div>
            <span>Person</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
            <span>Process</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-purple-500 rounded-full"></div>
            <span>Department</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500 rounded-full"></div>
            <span>Project</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span>System</span>
          </div>
          
          {/* Relationship Types */}
          <div className="border-l border-gray-300 pl-4 ml-2">
            <span className="font-semibold text-gray-600">Relationships:</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-blue-500"></div>
            <span>REPORTS_TO</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-green-500"></div>
            <span>WORKS_WITH</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-purple-500"></div>
            <span>BELONGS_TO</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-yellow-500"></div>
            <span>ASSIGNED_TO</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-red-500"></div>
            <span>USES</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-red-600"></div>
            <span>HEADS</span>
          </div>
          <div className="flex items-center space-x-1">
            <div className="w-4 h-0.5 bg-violet-500"></div>
            <span>OWNS</span>
          </div>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 relative">
        {error && (
          <div className="absolute inset-0 flex items-center justify-center bg-red-50">
            <div className="text-center">
              <p className="text-red-600 font-medium">Error loading graph</p>
              <p className="text-red-500 text-sm mt-1">{error}</p>
              <button
                onClick={refreshGraph}
                className="mt-2 px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700"
              >
                Retry
              </button>
            </div>
          </div>
        )}
        
        {!data && !error && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-50">
            <div className="text-center">
              <Network className="h-12 w-12 mx-auto mb-4 text-gray-300" />
              <p className="text-gray-500">No graph data available</p>
              <p className="text-gray-400 text-sm mt-1">
                Start a conversation to load organizational data
              </p>
            </div>
          </div>
        )}

        <div
          ref={containerRef}
          className="w-full h-full"
          style={{ minHeight: '400px' }}
        />
      </div>

    </div>
  )
}
