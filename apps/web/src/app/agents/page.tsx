'use client';

import { useQuery } from '@tanstack/react-query';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { Button } from '@/components/ui/button';
import { agentsApi } from '@/lib/api';
import { cn, getStatusColor, getStatusBg } from '@/lib/utils';
import {
  Play,
  Pause,
  Square,
  Brain,
  Eye,
  Zap,
  Shield,
  Wallet,
  Droplets,
  FlaskConical,
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
} from 'lucide-react';

const agentIcons: Record<string, React.ReactNode> = {
  MARKET_INTELLIGENCE: <Eye className="w-5 h-5" />,
  STRATEGY: <Brain className="w-5 h-5" />,
  EXECUTION: <Zap className="w-5 h-5" />,
  RISK_MANAGEMENT: <Shield className="w-5 h-5" />,
  PORTFOLIO: <Wallet className="w-5 h-5" />,
  LIQUIDITY_ANALYSIS: <Droplets className="w-5 h-5" />,
  BACKTEST: <FlaskConical className="w-5 h-5" />,
};

const agentDescriptions: Record<string, string> = {
  MARKET_INTELLIGENCE: 'Monitors real-time prices, detects market regimes, and tracks whale movements',
  STRATEGY: 'Generates trade signals using arbitrage, trend following, and mean reversion strategies',
  EXECUTION: 'Handles blockchain transactions with MEV protection and gas optimization',
  RISK_MANAGEMENT: 'Validates trades, enforces limits, and manages circuit breakers',
  PORTFOLIO: 'Tracks P&L, manages positions, and generates performance reports',
  LIQUIDITY_ANALYSIS: 'Scans pools, analyzes depth, and discovers opportunities',
  BACKTEST: 'Simulates strategies against historical data for validation',
};

export default function AgentsPage() {
  const { data: agents, isLoading } = useQuery({
    queryKey: ['agents'],
    queryFn: () => agentsApi.getAll().then((res) => res.data?.data || []),
    refetchInterval: 5000,
  });

  const { data: stats } = useQuery({
    queryKey: ['agentStats'],
    queryFn: () => agentsApi.getStats().then((res) => res.data),
    refetchInterval: 10000,
  });

  const handleStart = async (id: string) => {
    await agentsApi.start(id);
  };

  const handleStop = async (id: string) => {
    await agentsApi.stop(id);
  };

  const handlePause = async (id: string) => {
    await agentsApi.pause(id);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Header />

        <main className="flex-1 p-6 overflow-auto">
          {/* Page Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-white mb-2">Agent System</h1>
            <p className="text-muted-foreground">
              Manage and monitor your multi-agent trading system
            </p>
          </div>

          {/* Stats Overview */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Total Agents</p>
              <p className="text-2xl font-bold text-white">{stats?.by_status ? Object.values(stats.by_status).reduce((a, b) => a + b, 0) : 7}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Running</p>
              <p className="text-2xl font-bold text-crypto-green">{stats?.by_status?.RUNNING || 4}</p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Success Rate</p>
              <p className="text-2xl font-bold text-white">{stats?.total_successes && stats?.total_errors
                ? ((stats.total_successes / (stats.total_successes + stats.total_errors)) * 100).toFixed(1)
                : 94.2}%
              </p>
            </div>
            <div className="glass-card p-4">
              <p className="text-sm text-muted-foreground mb-1">Total Actions</p>
              <p className="text-2xl font-bold text-white">{formatNumber(stats?.total_successes + stats?.total_errors || 1248)}</p>
            </div>
          </div>

          {/* Agent Workflow Diagram */}
          <div className="glass-card p-6 mb-8">
            <h2 className="text-xl font-semibold text-white mb-6">Agent Workflow</h2>
            <div className="flex flex-wrap items-center justify-center gap-4">
              {['Market Intelligence', 'Strategy', 'Risk', 'Execution', 'Portfolio'].map((agent, index) => (
                <div key={agent} className="flex items-center gap-4">
                  <div className="relative">
                    <div className="w-16 h-16 rounded-xl bg-gradient-to-br from-pancake-500/20 to-pancake-600/20 border border-pancake-500/30 flex items-center justify-center">
                      <span className="text-2xl font-bold text-pancake-400">{index + 1}</span>
                    </div>
                    <div className="absolute -bottom-6 left-1/2 -translate-x-1/2 whitespace-nowrap">
                      <p className="text-xs text-muted-foreground">{agent}</p>
                    </div>
                  </div>
                  {index < 4 && (
                    <div className="hidden md:block w-8 h-px bg-gradient-to-r from-pancake-500/50 to-pancake-400/50" />
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Agents Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {isLoading ? (
              <div className="col-span-2 text-center py-12">
                <Activity className="w-8 h-8 animate-spin mx-auto text-pancake-400 mb-4" />
                <p className="text-muted-foreground">Loading agents...</p>
              </div>
            ) : agents?.length > 0 ? (
              agents.map((agent: any) => (
                <div
                  key={agent.agent_id}
                  className="glass-card p-5 card-hover"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="p-3 rounded-xl bg-pancake-500/10 text-pancake-400">
                        {agentIcons[agent.type] || <Activity className="w-5 h-5" />}
                      </div>
                      <div>
                        <h3 className="font-semibold text-white">{agent.name}</h3>
                        <p className="text-xs text-muted-foreground">{agent.type}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={cn('w-2 h-2 rounded-full animate-pulse', {
                        'bg-crypto-green': agent.status === 'RUNNING',
                        'bg-pancake-400': agent.status === 'PAUSED',
                        'bg-crypto-red': agent.status === 'ERROR' || agent.status === 'STOPPED',
                        'bg-muted-foreground': agent.status === 'IDLE',
                      })} />
                      <span className={cn('text-xs font-medium', getStatusColor(agent.status))}>
                        {agent.status}
                      </span>
                    </div>
                  </div>

                  <p className="text-sm text-muted-foreground mb-4">
                    {agentDescriptions[agent.type]}
                  </p>

                  {/* Stats */}
                  <div className="grid grid-cols-3 gap-4 mb-4">
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Success</p>
                      <p className="text-lg font-semibold text-crypto-green">{agent.success_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Errors</p>
                      <p className="text-lg font-semibold text-crypto-red">{agent.error_count || 0}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground mb-1">Total</p>
                      <p className="text-lg font-semibold text-white">{agent.total_actions || 0}</p>
                    </div>
                  </div>

                  {/* Last Action */}
                  {agent.last_action && (
                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
                      <Clock className="w-3 h-3" />
                      <span>Last action: {agent.last_action}</span>
                      {agent.last_action_at && (
                        <span>• {new Date(agent.last_action_at).toLocaleTimeString()}</span>
                      )}
                    </div>
                  )}

                  {/* Actions */}
                  <div className="flex gap-2">
                    {agent.status !== 'RUNNING' ? (
                      <Button
                        size="sm"
                        onClick={() => handleStart(agent.agent_id)}
                        className="flex-1"
                      >
                        <Play className="w-4 h-4 mr-1" />
                        Start
                      </Button>
                    ) : (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handlePause(agent.agent_id)}
                          className="flex-1"
                        >
                          <Pause className="w-4 h-4 mr-1" />
                          Pause
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleStop(agent.agent_id)}
                          className="flex-1"
                        >
                          <Square className="w-4 h-4 mr-1" />
                          Stop
                        </Button>
                      </>
                    )}
                  </div>
                </div>
              ))
            ) : (
              <>
                {/* Mock agents for demo */}
                {Object.entries(agentDescriptions).map(([type, description], index) => (
                  <div key={type} className="glass-card p-5 card-hover">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="p-3 rounded-xl bg-pancake-500/10 text-pancake-400">
                          {agentIcons[type]}
                        </div>
                        <div>
                          <h3 className="font-semibold text-white">{type.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, l => l.toUpperCase())}</h3>
                          <p className="text-xs text-muted-foreground">{type}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={cn('w-2 h-2 rounded-full animate-pulse', {
                          'bg-crypto-green': index < 4,
                          'bg-muted-foreground': index >= 4,
                        })} />
                        <span className={cn('text-xs font-medium', {
                          'text-crypto-green': index < 4,
                          'text-muted-foreground': index >= 4,
                        })} >
                          {index < 4 ? 'RUNNING' : 'IDLE'}
                        </span>
                      </div>
                    </div>

                    <p className="text-sm text-muted-foreground mb-4">{description}</p>

                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Success</p>
                        <p className="text-lg font-semibold text-crypto-green">{[156, 89, 234, 45, 78, 123, 12][index]}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Errors</p>
                        <p className="text-lg font-semibold text-crypto-red">{[3, 2, 5, 1, 0, 2, 0][index]}</p>
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground mb-1">Total</p>
                        <p className="text-lg font-semibold text-white">{[159, 91, 239, 46, 78, 125, 12][index]}</p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 text-xs text-muted-foreground mb-4">
                      <Clock className="w-3 h-3" />
                      <span>Last action: market_scan</span>
                      <span>• 2s ago</span>
                    </div>

                    <div className="flex gap-2">
                      {index < 4 ? (
                        <>
                          <Button size="sm" variant="outline" className="flex-1">
                            <Pause className="w-4 h-4 mr-1" />
                            Pause
                          </Button>
                          <Button size="sm" variant="destructive" className="flex-1">
                            <Square className="w-4 h-4 mr-1" />
                            Stop
                          </Button>
                        </>
                      ) : (
                        <Button size="sm" className="flex-1">
                          <Play className="w-4 h-4 mr-1" />
                          Start
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}

function formatNumber(num: number): string {
  if (num >= 1_000_000) return `${(num / 1_000_000).toFixed(1)}M`;
  if (num >= 1_000) return `${(num / 1_000).toFixed(1)}K`;
  return num.toString();
}
