'use client';

import { useQuery } from '@tanstack/react-query';
import { Sidebar } from '@/components/sidebar';
import { Header } from '@/components/header';
import { poolsApi } from '@/lib/api';
import { formatCurrency, formatNumber, cn } from '@/lib/utils';
import { Activity, Droplets, TrendingUp, Search, ExternalLink } from 'lucide-react';

export default function PoolsPage() {
  const { data: poolsData, isLoading } = useQuery({
    queryKey: ['pools'],
    queryFn: () => poolsApi.getAll({ limit: 20 }).then((res) => res.data),
    refetchInterval: 30000,
  });

  const { data: topApys } = useQuery({
    queryKey: ['topApys'],
    queryFn: () => poolsApi.getTopApys(5).then((res) => res.data),
  });

  const pools = poolsData?.pools || [];

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <div className="flex-1 flex flex-col">
        <Header />
        <main className="flex-1 p-6 overflow-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h1 className="text-3xl font-bold text-white mb-2">Liquidity Pools</h1>
              <p className="text-muted-foreground">Monitor PancakeSwap pools and discover opportunities</p>
            </div>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <input
                type="text"
                placeholder="Search pools..."
                className="input-field w-64 pl-10 text-sm"
              />
            </div>
          </div>

          {/* Top APY Pools */}
          <div className="mb-6">
            <h2 className="text-lg font-semibold text-white mb-3">Top APY Pools</h2>
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {(topApys?.pools || []).slice(0, 5).map((pool: any, i: number) => (
                <div key={pool.id || i} className="glass-card p-4 card-hover">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 rounded-lg bg-crypto-green/10">
                      <TrendingUp className="w-3.5 h-3.5 text-crypto-green" />
                    </div>
                    <span className="text-sm font-medium text-white">{pool.token0?.symbol}/{pool.token1?.symbol}</span>
                  </div>
                  <p className="text-xl font-bold text-crypto-green">{pool.apr24h?.toFixed(1)}%</p>
                  <p className="text-xs text-muted-foreground">APR · TVL {formatNumber(pool.tvl_usd, 0)}</p>
                </div>
              ))}
              {(!topApys?.pools || topApys.pools.length === 0) && [
                { pair: 'CAKE/USDT', apr: 95.8, tvl: 8500000 },
                { pair: 'CAKE/BNB', apr: 85.2, tvl: 28000000 },
                { pair: 'BNB/USDT', apr: 42.5, tvl: 45000000 },
                { pair: 'ETH/BNB', apr: 38.7, tvl: 35000000 },
                { pair: 'BNB/BUSD', apr: 35.4, tvl: 6200000 },
              ].map((p) => (
                <div key={p.pair} className="glass-card p-4 card-hover">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="p-1.5 rounded-lg bg-crypto-green/10">
                      <TrendingUp className="w-3.5 h-3.5 text-crypto-green" />
                    </div>
                    <span className="text-sm font-medium text-white">{p.pair}</span>
                  </div>
                  <p className="text-xl font-bold text-crypto-green">{p.apr}%</p>
                  <p className="text-xs text-muted-foreground">APR · TVL ${formatNumber(p.tvl, 0)}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Pools Table */}
          <div className="glass-card overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border">
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">Pool</th>
                  <th className="text-left p-4 text-sm font-medium text-muted-foreground">DEX</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">TVL</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Volume 24h</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">APR</th>
                  <th className="text-right p-4 text-sm font-medium text-muted-foreground">Fee</th>
                  <th className="text-center p-4 text-sm font-medium text-muted-foreground">Category</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">
                      <Activity className="w-6 h-6 animate-spin mx-auto mb-2 text-pancake-400" />
                      Loading pools...
                    </td>
                  </tr>
                ) : pools.length > 0 ? (
                  pools.map((pool: any) => (
                    <tr key={pool.id} className="border-b border-border/50 hover:bg-white/5 transition-colors">
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <div className="p-2 rounded-lg bg-pancake-500/10">
                            <Droplets className="w-4 h-4 text-pancake-400" />
                          </div>
                          <div>
                            <p className="text-sm font-medium text-white">{pool.token0?.symbol}/{pool.token1?.symbol}</p>
                            <p className="text-xs text-muted-foreground">{pool.version}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-sm text-white capitalize">{pool.dex}</td>
                      <td className="p-4 text-right text-sm text-white">{formatCurrency(pool.tvl_usd)}</td>
                      <td className="p-4 text-right text-sm text-white">{formatCurrency(pool.volume24h_usd || 0)}</td>
                      <td className="p-4 text-right">
                        <span className="text-sm font-medium text-crypto-green">{pool.apr24h?.toFixed(1) || '—'}%</span>
                      </td>
                      <td className="p-4 text-right text-sm text-muted-foreground">{(pool.fee_rate * 100).toFixed(2)}%</td>
                      <td className="p-4 text-center">
                        <span className={cn('px-2 py-1 rounded text-xs font-medium', {
                          'bg-crypto-blue/10 text-crypto-blue': pool.category === 'BLUE_CHIP',
                          'bg-pancake-500/10 text-pancake-400': pool.category === 'MID_CAP',
                          'bg-crypto-purple/10 text-crypto-purple': pool.category === 'DEGEN',
                          'bg-white/5 text-muted-foreground': !pool.category || pool.category === 'UNKNOWN',
                        })}>
                          {pool.category?.replace('_', ' ') || 'UNKNOWN'}
                        </span>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={7} className="p-8 text-center text-muted-foreground">No pools found</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </main>
      </div>
    </div>
  );
}
