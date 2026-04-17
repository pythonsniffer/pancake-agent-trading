'use client';

import { useQuery } from '@tanstack/react-query';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { MetricsCard } from '@/components/metrics-card';
import { CustomLineChart } from '@/components/charts/line-chart';
import { CustomBarChart } from '@/components/charts/bar-chart';
import { portfolioApi, tradesApi, agentsApi } from '@/lib/api';
import {
  TrendingUp,
  Activity,
  Users,
  ArrowRightLeft,
  Wallet,
  Bot,
  AlertCircle,
} from 'lucide-react';

export default function DashboardPage() {
  // Fetch portfolio data
  const { data: portfolio } = useQuery({
    queryKey: ['portfolio'],
    queryFn: () => portfolioApi.getCurrent().then((res) => res.data),
    refetchInterval: 30000,
  });

  // Fetch trade stats
  const { data: tradeStats } = useQuery({
    queryKey: ['tradeStats'],
    queryFn: () => tradesApi.getStats().then((res) => res.data),
    refetchInterval: 30000,
  });

  // Fetch agent stats
  const { data: agentStats } = useQuery({
    queryKey: ['agentStats'],
    queryFn: () => agentsApi.getStats().then((res) => res.data),
    refetchInterval: 30000,
  });

  // Mock data for charts (would come from API)
  const portfolioHistory = [
    { date: 'Mon', value: 11000 },
    { date: 'Tue', value: 11200 },
    { date: 'Wed', value: 11800 },
    { date: 'Thu', value: 11500 },
    { date: 'Fri', value: 12200 },
    { date: 'Sat', value: 12450 },
    { date: 'Sun', value: 12450.8 },
  ];

  const tradeDistribution = [
    { name: 'Arbitrage', value: 45 },
    { name: 'Trend', value: 30 },
    { name: 'Mean Rev', value: 15 },
    { name: 'LP Yield', value: 10 },
  ];

  const metrics = [
    {
      title: 'Portfolio Value',
      value: portfolio?.data?.total_value_usd || 12450.8,
      change: 3.2,
      icon: <Wallet className="w-5 h-5 text-pancake-400" />,
    },
    {
      title: 'Total P&L',
      value: portfolio?.data?.total_pnl_usd || 2450.8,
      change: 12.5,
      icon: <TrendingUp className="w-5 h-5 text-crypto-green" />,
    },
    {
      title: 'Total Trades',
      value: tradeStats?.total_trades || 156,
      change: 8.3,
      icon: <ArrowRightLeft className="w-5 h-5 text-crypto-blue" />,
    },
    {
      title: 'Win Rate',
      value: tradeStats?.win_rate || 68.5,
      change: -2.1,
      prefix: '',
      suffix: '%',
      icon: <Activity className="w-5 h-5 text-crypto-purple" />,
    },
  ];

  const activeAgents = [
    { name: 'Market Intelligence', status: 'RUNNING', lastAction: '2s ago' },
    { name: 'Strategy', status: 'RUNNING', lastAction: '5s ago' },
    { name: 'Risk Management', status: 'RUNNING', lastAction: '1s ago' },
    { name: 'Execution', status: 'IDLE', lastAction: '2m ago' },
  ];

  const recentTrades = [
    { id: '1', tokenIn: 'BNB', tokenOut: 'USDT', amount: 1.5, profit: 12.5, status: 'SUCCESS', time: '2m ago' },
    { id: '2', tokenIn: 'ETH', tokenOut: 'USDC', amount: 0.5, profit: -3.2, status: 'FAILED', time: '5m ago' },
    { id: '3', tokenIn: 'CAKE', tokenOut: 'BNB', amount: 100, profit: 8.7, status: 'SUCCESS', time: '12m ago' },
    { id: '4', tokenIn: 'BTCB', tokenOut: 'USDT', amount: 0.1, profit: 25.3, status: 'SUCCESS', time: '18m ago' },
  ];

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />

      <div className="flex-1 flex flex-col">
        <Header />

        <main className="flex-1 p-6 overflow-auto">
          {/* Metrics Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {metrics.map((metric) => (
              <MetricsCard
                key={metric.title}
                title={metric.title}
                value={metric.value}
                change={metric.change}
                prefix={metric.prefix}
                suffix={metric.suffix}
                decimals={metric.title === 'Win Rate' ? 1 : 2}
                icon={metric.icon}
              />
            ))}
          </div>

          {/* Charts Section */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
            {/* Portfolio Chart */}
            <div className="lg:col-span-2 glass-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Portfolio Performance</h3>
                <div className="flex gap-2">
                  <button className="px-3 py-1 text-xs rounded bg-pancake-500/20 text-pancake-400">1D</button>
                  <button className="px-3 py-1 text-xs rounded bg-white/5 text-muted-foreground">1W</button>
                  <button className="px-3 py-1 text-xs rounded bg-white/5 text-muted-foreground">1M</button>
                  <button className="px-3 py-1 text-xs rounded bg-white/5 text-muted-foreground">1Y</button>
                </div>
              </div>
              <CustomLineChart
                data={portfolioHistory}
                dataKey="value"
                xKey="date"
                color="#f59e0b"
                height={300}
              />
            </div>

            {/* Trade Distribution */}
            <div className="glass-card p-5">
              <h3 className="text-lg font-semibold text-white mb-4">Strategy Distribution</h3>
              <CustomBarChart
                data={tradeDistribution}
                dataKey="value"
                xKey="name"
                height={250}
              />
              <div className="mt-4 space-y-2">
                {tradeDistribution.map((item, index) => (
                  <div key={item.name} className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${
                        index === 0 ? 'bg-crypto-green' :
                        index === 1 ? 'bg-crypto-red' :
                        index === 2 ? 'bg-pancake-500' : 'bg-crypto-blue'
                      }`} />
                      <span className="text-muted-foreground">{item.name}</span>
                    </div>
                    <span className="text-white font-medium">{item.value}%</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Section */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Active Agents */}
            <div className="glass-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Active Agents</h3>
                <button className="text-xs text-pancake-400 hover:text-pancake-300">
                  View All
                </button>
              </div>
              <div className="space-y-3">
                {activeAgents.map((agent) => (
                  <div
                    key={agent.name}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="p-2 rounded-lg bg-pancake-500/10">
                        <Bot className="w-4 h-4 text-pancake-400" />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">{agent.name}</p>
                        <p className="text-xs text-muted-foreground">Last action: {agent.lastAction}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${
                        agent.status === 'RUNNING' ? 'bg-crypto-green animate-pulse' : 'bg-muted-foreground'
                      }`} />
                      <span className={`text-xs font-medium ${
                        agent.status === 'RUNNING' ? 'text-crypto-green' : 'text-muted-foreground'
                      }`}>
                        {agent.status}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Trades */}
            <div className="glass-card p-5">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-white">Recent Trades</h3>
                <button className="text-xs text-pancake-400 hover:text-pancake-300">
                  View All
                </button>
              </div>
              <div className="space-y-3">
                {recentTrades.map((trade) => (
                  <div
                    key={trade.id}
                    className="flex items-center justify-between p-3 rounded-lg bg-white/5 hover:bg-white/10 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className={`p-2 rounded-lg ${
                        trade.status === 'SUCCESS' ? 'bg-crypto-green/10' : 'bg-crypto-red/10'
                      }`}>
                        <ArrowRightLeft className={`w-4 h-4 ${
                          trade.status === 'SUCCESS' ? 'text-crypto-green' : 'text-crypto-red'
                        }`} />
                      </div>
                      <div>
                        <p className="text-sm font-medium text-white">
                          {trade.tokenIn} → {trade.tokenOut}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {trade.amount} {trade.tokenIn} • {trade.time}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className={`text-sm font-medium ${
                        trade.profit >= 0 ? 'text-crypto-green' : 'text-crypto-red'
                      }`}>
                        {trade.profit >= 0 ? '+' : ''}{trade.profit.toFixed(2)} USD
                      </p>
                      <p className={`text-xs ${
                        trade.status === 'SUCCESS' ? 'text-crypto-green' : 'text-crypto-red'
                      }`}>
                        {trade.status}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
