/**
 * Agent Decision Graph Visualization
 *
 * Displays the LangGraph state machine with:
 * - Animated agent execution flow
 * - Real-time state updates
 * - Decision paths and branches
 * - Agent status indicators
 */

'use client';

import React, { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  type Node,
  type Edge,
  ConnectionMode,
  Handle,
  Position,
  BaseEdge,
  getStraightPath,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';

import {
  Bot,
  Brain,
  Shield,
  Zap,
  Wallet,
  Droplets,
  Activity,
  TestTube,
  ArrowRight,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react';

// Agent node data type
interface AgentNodeData {
  label: string;
  type: string;
  status: 'IDLE' | 'RUNNING' | 'COMPLETED' | 'ERROR';
  lastAction?: string;
  confidence?: number;
  duration?: number;
  [key: string]: unknown;
}

// Props for the graph component
interface AgentFlowGraphProps {
  currentState?: {
    status: string;
    activeAgent?: string;
    lastCompleted?: string;
    agentActions?: any[];
  };
  onNodeClick?: (nodeId: string, data: AgentNodeData) => void;
}

// Custom node component
function AgentNode({ data, selected }: { data: AgentNodeData; selected: boolean }) {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'RUNNING': return 'border-yellow-500 bg-yellow-500/10';
      case 'COMPLETED': return 'border-green-500 bg-green-500/10';
      case 'ERROR': return 'border-red-500 bg-red-500/10';
      default: return 'border-slate-600 bg-slate-800/50';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'RUNNING': return <Clock className="w-4 h-4 text-yellow-400 animate-pulse" />;
      case 'COMPLETED': return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'ERROR': return <XCircle className="w-4 h-4 text-red-400" />;
      default: return <Bot className="w-4 h-4 text-slate-400" />;
    }
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'market': return <Brain className="w-5 h-5 text-blue-400" />;
      case 'strategy': return <Zap className="w-5 h-5 text-purple-400" />;
      case 'risk': return <Shield className="w-5 h-5 text-red-400" />;
      case 'execution': return <Zap className="w-5 h-5 text-yellow-400" />;
      case 'portfolio': return <Wallet className="w-5 h-5 text-green-400" />;
      case 'liquidity': return <Droplets className="w-5 h-5 text-cyan-400" />;
      case 'backtest': return <TestTube className="w-5 h-5 text-pink-400" />;
      default: return <Activity className="w-5 h-5 text-slate-400" />;
    }
  };

  return (
    <div
      className={`
        relative min-w-[180px] p-4 rounded-xl border-2 transition-all duration-300
        ${getStatusColor(data.status)}
        ${selected ? 'ring-2 ring-white/50 shadow-lg shadow-white/10' : ''}
        ${data.status === 'RUNNING' ? 'shadow-lg shadow-yellow-500/20' : ''}
      `}
    >
      <Handle type="target" position={Position.Top} className="!bg-slate-500 !w-2 !h-2" />
      <Handle type="source" position={Position.Bottom} className="!bg-slate-500 !w-2 !h-2" />

      {/* Status Indicator */}
      <div className="absolute -top-2 -right-2">
        {getStatusIcon(data.status)}
      </div>

      {/* Agent Icon */}
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-white/5">
          {getAgentIcon(data.type)}
        </div>
        <div>
          <h4 className="font-semibold text-white text-sm">{data.label}</h4>
          <p className="text-xs text-slate-400 capitalize">{data.status.toLowerCase()}</p>
        </div>
      </div>

      {/* Action Info */}
      {data.lastAction && (
        <div className="mt-2 pt-2 border-t border-white/10">
          <p className="text-xs text-slate-300 truncate">
            {data.lastAction}
          </p>
        </div>
      )}

      {/* Confidence & Duration */}
      {(data.confidence !== undefined || data.duration !== undefined) && (
        <div className="mt-2 flex items-center gap-3 text-xs">
          {data.confidence !== undefined && (
            <span className="text-cyan-400">
              {Math.round(data.confidence * 100)}% conf
            </span>
          )}
          {data.duration !== undefined && (
            <span className="text-slate-400">
              {data.duration}ms
            </span>
          )}
        </div>
      )}

      {/* Running Animation */}
      {data.status === 'RUNNING' && (
        <motion.div
          className="absolute inset-0 rounded-xl border-2 border-yellow-500/50 pointer-events-none"
          animate={{
            scale: [1, 1.02, 1],
            opacity: [0.5, 0.8, 0.5],
          }}
          transition={{
            duration: 1.5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      )}
    </div>
  );
}

// Main graph component
export const AgentFlowGraph: React.FC<AgentFlowGraphProps> = ({
  currentState,
  onNodeClick,
}) => {
  const initialNodes: Node[] = [
    {
      id: 'market',
      type: 'agent',
      position: { x: 100, y: 50 },
      data: {
        label: 'Market Intelligence',
        type: 'market',
        status: 'IDLE',
        lastAction: 'Scanning 45 pools',
      },
    },
    {
      id: 'liquidity',
      type: 'agent',
      position: { x: 400, y: 50 },
      data: {
        label: 'Liquidity Analysis',
        type: 'liquidity',
        status: 'IDLE',
        lastAction: 'Analyzing depth',
      },
    },
    {
      id: 'strategy',
      type: 'agent',
      position: { x: 250, y: 200 },
      data: {
        label: 'Strategy Engine',
        type: 'strategy',
        status: 'IDLE',
        lastAction: 'Generating signals',
      },
    },
    {
      id: 'risk',
      type: 'agent',
      position: { x: 250, y: 350 },
      data: {
        label: 'Risk Management',
        type: 'risk',
        status: 'IDLE',
        lastAction: 'Validating signals',
      },
    },
    {
      id: 'execution',
      type: 'agent',
      position: { x: 100, y: 500 },
      data: {
        label: 'Execution',
        type: 'execution',
        status: 'IDLE',
        lastAction: 'Waiting for trades',
      },
    },
    {
      id: 'portfolio',
      type: 'agent',
      position: { x: 400, y: 500 },
      data: {
        label: 'Portfolio Manager',
        type: 'portfolio',
        status: 'IDLE',
        lastAction: 'Updating PnL',
      },
    },
    {
      id: 'backtest',
      type: 'agent',
      position: { x: 550, y: 200 },
      data: {
        label: 'Backtester',
        type: 'backtest',
        status: 'IDLE',
        lastAction: 'Simulating strategies',
      },
    },
  ];

  const initialEdges: Edge[] = [
    { id: 'e1', source: 'market', target: 'strategy', animated: true, style: { stroke: '#475569', strokeWidth: 2 } },
    { id: 'e2', source: 'liquidity', target: 'strategy', animated: true, style: { stroke: '#475569', strokeWidth: 2 } },
    { id: 'e3', source: 'strategy', target: 'risk', animated: true, style: { stroke: '#475569', strokeWidth: 2 } },
    { id: 'e4', source: 'risk', target: 'execution', label: 'Approved', style: { stroke: '#22c55e', strokeWidth: 2 } },
    { id: 'e5', source: 'risk', target: 'portfolio', label: 'Rejected', style: { stroke: '#ef4444', strokeWidth: 2 } },
    { id: 'e6', source: 'execution', target: 'portfolio', animated: true, style: { stroke: '#475569', strokeWidth: 2 } },
    { id: 'e7', source: 'backtest', target: 'strategy', style: { stroke: '#475569', strokeWidth: 2, strokeDasharray: '5 5' } },
  ];

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [executionHistory, setExecutionHistory] = useState<string[]>([]);

  // Simulate execution flow for demo
  useEffect(() => {
    const flow = ['market', 'liquidity', 'strategy', 'risk', 'execution', 'portfolio'];
    let step = 0;

    const interval = setInterval(() => {
      const activeId = flow[step % flow.length];
      const prevId = step > 0 ? flow[(step - 1) % flow.length] : null;

      setNodes((nds) =>
        nds.map((node) => ({
          ...node,
          data: {
            ...node.data,
            status: node.id === activeId ? 'RUNNING' : node.id === prevId ? 'COMPLETED' : 'IDLE',
          },
        }))
      );

      setEdges((eds) =>
        eds.map((edge) => ({
          ...edge,
          animated: edge.source === activeId || edge.source === prevId,
          style: {
            ...edge.style,
            stroke: edge.source === activeId ? '#fbbf24' : edge.source === prevId ? '#22c55e' : '#475569',
            strokeWidth: edge.source === activeId ? 3 : 2,
          },
        }))
      );

      setExecutionHistory((prev) => {
        const next = [...prev, activeId];
        return next.slice(-6);
      });

      step++;
    }, 3000);

    return () => clearInterval(interval);
  }, [setNodes, setEdges]);

  // Apply external state updates
  useEffect(() => {
    if (!currentState) return;

    setNodes((nds) =>
      nds.map((node) => {
        const isActive = currentState.activeAgent === node.id;
        const isCompleted = currentState.lastCompleted === node.id;

        return {
          ...node,
          data: {
            ...node.data,
            status: isActive ? 'RUNNING' : isCompleted ? 'COMPLETED' : node.data.status as string,
          },
        };
      })
    );
  }, [currentState, setNodes]);

  const nodeTypes = {
    agent: AgentNode,
  };

  return (
    <div className="w-full h-full min-h-[600px] bg-slate-900/50 rounded-xl overflow-hidden relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        onNodeClick={(_, node) => onNodeClick?.(node.id, node.data as AgentNodeData)}
        fitView
        connectionMode={ConnectionMode.Loose}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#334155" gap={16} size={1} />
        <Controls className="bg-slate-800 border-slate-700" />
        <MiniMap
          nodeColor={(node) => {
            switch ((node.data as any)?.status) {
              case 'RUNNING': return '#fbbf24';
              case 'COMPLETED': return '#22c55e';
              case 'ERROR': return '#ef4444';
              default: return '#64748b';
            }
          }}
          maskColor="rgba(15, 23, 42, 0.7)"
          className="bg-slate-900/80"
        />
      </ReactFlow>

      {/* Execution History Panel */}
      <div className="absolute bottom-4 left-4 bg-slate-800/90 backdrop-blur-sm rounded-lg p-3 border border-slate-700">
        <h4 className="text-xs font-semibold text-slate-400 mb-2">Execution Path</h4>
        <div className="flex items-center gap-1">
          {executionHistory.map((agent, idx) => (
            <React.Fragment key={idx}>
              <span className="text-xs text-cyan-400 capitalize">{agent}</span>
              {idx < executionHistory.length - 1 && (
                <ArrowRight className="w-3 h-3 text-slate-500" />
              )}
            </React.Fragment>
          ))}
          {executionHistory.length === 0 && (
            <span className="text-xs text-slate-500">Waiting for execution...</span>
          )}
        </div>
      </div>

      {/* Legend */}
      <div className="absolute top-4 right-4 bg-slate-800/90 backdrop-blur-sm rounded-lg p-3 border border-slate-700">
        <h4 className="text-xs font-semibold text-slate-400 mb-2">Status Legend</h4>
        <div className="space-y-1 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-slate-600" />
            <span className="text-slate-300">Idle</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
            <span className="text-slate-300">Running</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-green-500" />
            <span className="text-slate-300">Completed</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-red-500" />
            <span className="text-slate-300">Error</span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AgentFlowGraph;
