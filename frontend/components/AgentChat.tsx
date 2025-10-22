'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2 } from 'lucide-react'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  agentType?: string
  timestamp: string
  source?: string
  links?: Array<{
    title: string
    url: string
    snippet: string
    published_date?: string
    author?: string
    score?: number
  }>
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
  const [useExa, setUseExa] = useState(false)
  const [enhanceQuery, setEnhanceQuery] = useState(false)
  const [maxNodes, setMaxNodes] = useState(25)
  const [deepSearch, setDeepSearch] = useState(false)
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
      const response = await fetch('/api/agents')
      if (response.ok) {
        const agentsData = await response.json()
        if (agentsData && Object.keys(agentsData).length > 0) {
          setAgents(agentsData)
        } else {
          // RL-related placeholders when none are returned
          setAgents({
            graph: {
              name: 'Strategy Copilot',
              role: 'Graph Strategy',
              available_tools: ['neo4j', 'sagemaker', 'exa'],
              description: 'Graph-aware strategy generation'
            },
            rl_coach: {
              name: 'RL Coach',
              role: 'Training Advisor',
              available_tools: ['logs', 'metrics'],
              description: 'Suggests GRPO settings, K rollouts, KL, epochs'
            },
            reward_tuner: {
              name: 'Reward Tuner',
              role: 'Reward Design',
              available_tools: ['dataset'],
              description: 'Helps shape and calibrate reward functions'
            },
            eval_judge: {
              name: 'Eval Judge',
              role: 'Evaluation',
              available_tools: ['eval_set'],
              description: 'Scores outputs with rubric and reports regressions'
            }
          })
        }
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error)
      // Fallback placeholders if API fails
      setAgents({
        graph: {
          name: 'Strategy Copilot',
          role: 'Graph Strategy',
          available_tools: ['neo4j', 'sagemaker', 'exa'],
          description: 'Graph-aware strategy generation'
        },
        rl_coach: {
          name: 'RL Coach',
          role: 'Training Advisor',
          available_tools: ['logs', 'metrics'],
          description: 'Suggests GRPO settings, K rollouts, KL, epochs'
        },
        reward_tuner: {
          name: 'Reward Tuner',
          role: 'Reward Design',
          available_tools: ['dataset'],
          description: 'Helps shape and calibrate reward functions'
        },
        eval_judge: {
          name: 'Eval Judge',
          role: 'Evaluation',
          available_tools: ['eval_set'],
          description: 'Scores outputs with rubric and reports regressions'
        }
      })
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
      // Prefer new strategy endpoint; backend also exposes legacy /api/chat
      const response = await fetch('/api/strategy', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          query: input, 
          useExa: useExa,
          enhance: enhanceQuery,
          maxNodes: maxNodes,
          deepSearch: deepSearch
        })
      })

      if (response.ok) {
        const data = await response.json()
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: data.text || data.response || '',
          agentType: 'graph',
          timestamp: new Date().toISOString(),
          source: data.source,
          links: data.links || []
        }
        setMessages(prev => [...prev, assistantMessage])

        // Check if the response contains graph data and update the graph
        if (onGraphUpdate) {
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
      const response = await fetch(`/api/graph-context?maxNodes=${maxNodes}`)
      if (response.ok) {
        const graphData = await response.json()
        // graph-context returns { summary, graph }
        onGraphUpdate?.(graphData.graph || graphData)
      }
    } catch (error) {
      console.error('Failed to fetch graph data:', error)
    }
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="flex flex-col h-full bg-white dark:bg-gray-900">
      {/* Input Section - At the top */}
      <div className="p-5 border-b-2 border-gray-200 dark:border-gray-700 bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-800 dark:to-gray-850">
        <div className="space-y-3.5">
          {/* Top Row: Agent Selector & Controls */}
          <div className="flex items-center justify-between gap-3 flex-wrap">
            {/* Agent Selector */}
            <select
              value={selectedAgent}
              onChange={(e) => setSelectedAgent(e.target.value)}
              className="px-4 py-2.5 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 min-w-[200px] font-medium shadow-sm transition-all hover:border-gray-400 dark:hover:border-gray-500"
            >
              {Object.entries(agents).map(([key, agent]) => (
                <option key={key} value={key}>
                  {agent.name}
                </option>
              ))}
            </select>
            
            <div className="flex items-center gap-2.5">
              {/* Graph Size Selector */}
              <select
                value={maxNodes}
                onChange={(e) => setMaxNodes(Number(e.target.value))}
                className="px-3 py-2.5 text-sm border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 font-medium shadow-sm transition-all hover:border-gray-400 dark:hover:border-gray-500"
                title="Graph size"
              >
                <option value={5}>Small (5)</option>
                <option value={15}>Medium (15)</option>
                <option value={25}>Large (25)</option>
                <option value={30}>XL (30)</option>
              </select>

              {/* Query Enhancement Toggle */}
              <button
                onClick={() => setEnhanceQuery(!enhanceQuery)}
                className={`px-3 py-2.5 text-sm rounded-lg transition-all flex items-center space-x-1.5 font-semibold whitespace-nowrap border-2 ${
                  enhanceQuery 
                    ? 'bg-purple-600 dark:bg-purple-500 text-white hover:bg-purple-700 dark:hover:bg-purple-600 shadow-md border-purple-700 dark:border-purple-600 hover:shadow-lg transform hover:scale-105' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-300 dark:border-gray-600 shadow-sm'
                }`}
                title={enhanceQuery ? 'Disable query enhancement' : 'Enable query enhancement with Claude'}
              >
                <span className="text-base">{enhanceQuery ? '✨' : '💡'}</span>
                <span>{enhanceQuery ? 'Enhance' : 'Raw'}</span>
              </button>

              {/* Exa.ai Toggle */}
              <button
                onClick={() => setUseExa(!useExa)}
                className={`px-3 py-2.5 text-sm rounded-lg transition-all flex items-center space-x-2 font-semibold whitespace-nowrap border-2 ${
                  useExa 
                    ? 'bg-green-600 dark:bg-green-500 text-white hover:bg-green-700 dark:hover:bg-green-600 shadow-md border-green-700 dark:border-green-600 hover:shadow-lg transform hover:scale-105' 
                    : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-300 dark:border-gray-600 shadow-sm'
                }`}
                title={useExa ? 'Disable Exa.ai web search' : 'Enable Exa.ai web search'}
              >
                <span className="text-base">{useExa ? '🌐' : '🔍'}</span>
                <span>{useExa ? 'Exa ON' : 'Exa OFF'}</span>
              </button>

              {/* Deep Search Toggle */}
              {useExa && (
                <button
                  onClick={() => setDeepSearch(!deepSearch)}
                  className={`px-3 py-2.5 text-sm rounded-lg transition-all flex items-center space-x-1.5 font-semibold whitespace-nowrap border-2 ${
                    deepSearch 
                      ? 'bg-purple-600 dark:bg-purple-500 text-white hover:bg-purple-700 dark:hover:bg-purple-600 shadow-md border-purple-700 dark:border-purple-600 hover:shadow-lg transform hover:scale-105' 
                      : 'bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 border-gray-300 dark:border-gray-600 shadow-sm'
                  }`}
                  title={deepSearch ? 'Disable deep multi-query search' : 'Enable deep multi-query search'}
                >
                  <span className="text-base">{deepSearch ? '🚀' : '⚡'}</span>
                  <span>{deepSearch ? 'Deep' : 'Quick'}</span>
                </button>
              )}
              
              {/* Clear button */}
              <button
                onClick={clearMessages}
                className="px-4 py-2.5 text-sm text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-gray-100 hover:bg-white dark:hover:bg-gray-700 rounded-lg transition-all whitespace-nowrap border-2 border-transparent hover:border-gray-300 dark:hover:border-gray-600 font-medium"
                title="Clear conversation"
              >
                Clear
              </button>
            </div>
          </div>
          
          {/* Bottom Row: Chat Input */}
          <form onSubmit={sendMessage} className="flex gap-3">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask about your organization... (e.g., 'Who reports to Sarah Chen?')"
              className="flex-1 px-5 py-3 border-2 border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500 shadow-sm transition-all hover:border-gray-400 dark:hover:border-gray-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-blue-600 to-blue-700 dark:from-blue-500 dark:to-blue-600 text-white rounded-lg hover:from-blue-700 hover:to-blue-800 dark:hover:from-blue-600 dark:hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm flex items-center space-x-2 font-semibold shadow-md hover:shadow-lg transform hover:scale-105 whitespace-nowrap"
            >
              <Send className="h-4 w-4" />
              <span>Send</span>
            </button>
          </form>
        </div>
      </div>

      {/* Messages - Below input */}
      <div className="flex-1 overflow-y-auto p-5 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-gray-500 dark:text-gray-400 py-12 px-4">
            <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-gradient-to-br from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 mb-4">
              <Bot className="h-8 w-8 text-blue-600 dark:text-blue-400" />
            </div>
            <h3 className="text-lg font-semibold text-gray-700 dark:text-gray-300 mb-2">
              Ready to assist you
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4 max-w-md mx-auto">
              Start a conversation with your Strategy Copilot. Ask about people, processes, projects, or organizational insights.
            </p>
            <div className="flex flex-wrap gap-2 justify-center max-w-2xl mx-auto">
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
                "Who reports to Sarah Chen?"
              </span>
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
                "Find bottlenecks in our processes"
              </span>
              <span className="px-3 py-1.5 bg-gray-100 dark:bg-gray-800 rounded-full text-xs text-gray-600 dark:text-gray-400 border border-gray-200 dark:border-gray-700">
                "Show Engineering department structure"
              </span>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
            >
              <div
                className={`max-w-xs lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-2xl shadow-sm ${
                  message.role === 'user'
                    ? 'bg-gradient-to-br from-blue-600 to-blue-700 dark:from-blue-500 dark:to-blue-600 text-white'
                    : 'bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 border-2 border-gray-200 dark:border-gray-700'
                }`}
              >
                <div className="flex items-center space-x-2 mb-2">
                  {message.role === 'user' ? (
                    <User className="h-4 w-4" />
                  ) : (
                    <Bot className="h-4 w-4 text-blue-500 dark:text-blue-400" />
                  )}
                  <span className="text-xs font-semibold opacity-90">
                    {message.role === 'user' ? 'You' : agents[message.agentType || selectedAgent]?.name || 'Agent'}
                  </span>
                  <span className="text-xs opacity-50 ml-auto">
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                  {message.role === 'assistant' && message.source && (
                    <span className={`ml-2 px-2 py-0.5 rounded-full text-[10px] font-semibold border ${
                      message.source === 'sagemaker'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800'
                        : 'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800'
                    }`}>
                      {message.source === 'sagemaker' ? 'SageMaker' : message.source === 'bedrock' ? 'Bedrock' : 'Claude'}
                    </span>
                  )}
                </div>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                
                {/* Exa.ai Links */}
                {message.links && message.links.length > 0 && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <div className="text-xs font-semibold text-gray-600 dark:text-gray-400 mb-2 flex items-center">
                      <span className="mr-1">🔗</span>
                      Sources ({message.links.length})
                      {message.links.some(l => l.score) && (
                        <span className="ml-2 px-2 py-0.5 bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 rounded-full text-xs">
                          AI-Ranked
                        </span>
                      )}
                    </div>
                    <div className="space-y-2">
                      {message.links.map((link, index) => (
                        <div key={index} className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3 border border-gray-200 dark:border-gray-700 hover:shadow-sm transition-shadow">
                          <div className="flex items-start justify-between mb-1">
                            <a 
                              href={link.url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-sm font-medium text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 hover:underline flex-1"
                            >
                              {link.title}
                            </a>
                            {link.score && (
                              <span className="ml-2 px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                                {Math.round(link.score * 100)}%
                              </span>
                            )}
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400 leading-relaxed mb-2">
                            {link.snippet}
                          </p>
                          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-500">
                            <div className="truncate flex-1 mr-2">
                              {link.url}
                            </div>
                            <div className="flex items-center space-x-2 text-xs">
                              {link.author && (
                                <span className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                                  {link.author}
                                </span>
                              )}
                              {link.published_date && (
                                <span className="px-1.5 py-0.5 bg-gray-200 dark:bg-gray-700 rounded">
                                  {new Date(link.published_date).toLocaleDateString()}
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-gray-100 px-3 py-2 rounded-lg">
              <div className="flex items-center space-x-2">
                <Loader2 className="h-3 w-3 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
              {/* Thought bubbles */}
              <div className="mt-2 flex space-x-2">
                <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse"></span>
                <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse [animation-delay:150ms]"></span>
                <span className="inline-block h-2 w-2 rounded-full bg-blue-400 animate-pulse [animation-delay:300ms]"></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
    </div>
  )
}
