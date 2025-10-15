'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentType?: string
  timestamp: string
}

interface AgentInfo {
  name: string
  role: string
  available_tools: string[]
  description: string
}

interface AgentChatProps {
  onGraphUpdate?: (data: any) => void
}

export default function AgentChat({ onGraphUpdate }: AgentChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [selectedAgent, setSelectedAgent] = useState('graph')
  const [agents, setAgents] = useState<Record<string, AgentInfo>>({})
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // Load available agents on component mount
  useEffect(() => {
    fetchAgents()
  }, [])

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const fetchAgents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/agents')
      if (response.ok) {
        const agentsData = await response.json()
        setAgents(agentsData)
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
    }
  }

  const sendMessage = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: input,
          agent_type: selectedAgent
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.response,
          agentType: data.agent_type,
          timestamp: data.timestamp
        }
        setMessages(prev => [...prev, assistantMessage])

        // Check if the response contains graph data and update the graph
        if (onGraphUpdate && data.response.includes('graph') || data.response.includes('node')) {
          fetchGraphData()
        }
      } else {
        throw new Error('Failed to send message')
      }
    } catch (error) {
      console.error('Error sending message:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again.',
        timestamp: new Date().toISOString()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const fetchGraphData = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/graph')
      if (response.ok) {
        const graphData = await response.json()
        onGraphUpdate?.(graphData)
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    }
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="flex flex-col h-full">
      {/* Input Section - At the top */}
      <div className="p-3 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center space-x-3">
          {/* Agent Selector */}
          <select
            value={selectedAgent}
            onChange={(e) => setSelectedAgent(e.target.value)}
            className="px-3 py-1 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
          >
            {Object.entries(agents).map(([key, agent]) => (
              <option key={key} value={key}>
                {agent.name} ({agent.role})
              </option>
            ))}
          </select>
          
          {/* Chat Input */}
          <form onSubmit={sendMessage} className="flex-1 flex space-x-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your organization..."
              className="flex-1 px-3 py-1 border border-gray-300 rounded-md focus:ring-1 focus:ring-blue-500 focus:border-blue-500 text-sm"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-3 py-1 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm flex items-center space-x-1"
            >
              <Send className="h-4 w-4" />
            </button>
          </form>
          
          {/* Clear button */}
          <button
            onClick={clearMessages}
            className="px-2 py-1 text-xs text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md transition-colors"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Messages - Below input */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 py-6">
            <Bot className="h-8 w-8 mx-auto mb-3 text-gray-300" />
            <p className="text-sm">Start a conversation with your selected agent</p>
            <p className="text-xs mt-1 text-gray-400">
              Try asking: "Show me all people in the organization" or "Find bottlenecks in our processes"
            </p>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs lg:max-w-md px-3 py-2 rounded-lg ${
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}
              >
                <div className="flex items-center space-x-2 mb-1">
                  {message.role === 'user' ? (
                    <User className="h-3 w-3" />
                  ) : (
                    <Bot className="h-3 w-3" />
                  )}
                  <span className="text-xs opacity-75">
                    {message.role === 'user' ? 'You' : agents[message.agentType || selectedAgent]?.name || 'Agent'}
                  </span>
                </div>
                <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                <p className="text-xs opacity-50 mt-1">
                  {new Date(message.timestamp).toLocaleTimeString()}
                </p>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 text-gray-900 px-3 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
