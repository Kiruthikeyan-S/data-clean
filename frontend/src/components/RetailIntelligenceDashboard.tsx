import React, { useState } from 'react';
import {
  TrendingUp,
  Award,
  Users,
  ShoppingBag,
  Sparkles,
  ArrowUpRight,
  AlertCircle,
  Package,
  Zap,
  Target,
  BarChart3,
  Database
} from 'lucide-react';
import { RetailIntelligenceReport, UnifiedWarehouseView } from '../types';

interface RetailIntelligenceDashboardProps {
  intelligence?: RetailIntelligenceReport;
  unifiedWarehouse?: UnifiedWarehouseView;
}

type TabType = 'overview' | 'products' | 'rfm' | 'basket' | 'forecast' | 'warehouse';

export const RetailIntelligenceDashboard: React.FC<RetailIntelligenceDashboardProps> = ({
  intelligence,
  unifiedWarehouse
}) => {
  if (!intelligence && !unifiedWarehouse) return null;

  const defaultTab: TabType = intelligence ? 'overview' : 'warehouse';
  const [activeTab, setActiveTab] = useState<TabType>(defaultTab);

  const kpis = intelligence?.kpis;
  const products = intelligence?.product_analytics;
  const customers = intelligence?.customer_intelligence;
  const basket = intelligence?.basket_analysis;
  const forecast = intelligence?.demand_forecasting;
  const entityInfo = intelligence?.entity_classification;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden mb-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 px-6 py-4 text-white flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 bg-blue-500/20 border border-blue-400/30 rounded-lg text-blue-400">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-white tracking-tight">
                Retail Intelligence & Predictive Forecasting
              </h3>
              {entityInfo?.primary_entity && (
                <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/30">
                  {entityInfo.primary_entity} DOMAIN
                </span>
              )}
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              Automated heuristics + AI extracted business insights, RFM customer tiers, and inventory demand predictions
            </p>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex items-center gap-1.5 overflow-x-auto bg-slate-800/80 p-1 rounded-lg border border-slate-700/60">
          {intelligence && (
            <>
              <button
                type="button"
                onClick={() => setActiveTab('overview')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeTab === 'overview'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                <span>Executive KPIs</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('products')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeTab === 'products'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Award className="w-3.5 h-3.5" />
                <span>Product Analytics</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('rfm')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeTab === 'rfm'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <Users className="w-3.5 h-3.5" />
                <span>Customer RFM</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('basket')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeTab === 'basket'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <ShoppingBag className="w-3.5 h-3.5" />
                <span>Market Basket</span>
              </button>

              <button
                type="button"
                onClick={() => setActiveTab('forecast')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeTab === 'forecast'
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
                }`}
              >
                <TrendingUp className="w-3.5 h-3.5" />
                <span>Demand Forecast</span>
              </button>
            </>
          )}

          {unifiedWarehouse && (
            <button
              type="button"
              onClick={() => setActiveTab('warehouse')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'warehouse'
                  ? 'bg-indigo-600 text-white shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Database className="w-3.5 h-3.5" />
              <span>Unified Warehouse ({unifiedWarehouse.total_records})</span>
            </button>
          )}
        </div>
      </div>

      {/* Tab Contents */}
      <div className="p-6 space-y-6">
        {/* 1. Executive Overview */}
        {activeTab === 'overview' && kpis && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-50/60 to-white p-4 rounded-xl border border-blue-200/80 shadow-2xs">
                <span className="text-[11px] font-bold tracking-wider text-blue-700 uppercase">Total Revenue</span>
                <div className="text-2xl font-black text-slate-900 mt-1">
                  ${kpis.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                </div>
                <div className="text-xs text-blue-600/80 mt-1 font-medium flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  <span>Calculated from transaction data</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-emerald-50/60 to-white p-4 rounded-xl border border-emerald-200/80 shadow-2xs">
                <span className="text-[11px] font-bold tracking-wider text-emerald-700 uppercase">Units Sold</span>
                <div className="text-2xl font-black text-slate-900 mt-1">
                  {kpis.total_units_sold.toLocaleString()}
                </div>
                <div className="text-xs text-emerald-600/80 mt-1 font-medium flex items-center gap-1">
                  <Package className="w-3.5 h-3.5" />
                  <span>Across {kpis.total_transactions} orders</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-indigo-50/60 to-white p-4 rounded-xl border border-indigo-200/80 shadow-2xs">
                <span className="text-[11px] font-bold tracking-wider text-indigo-700 uppercase">Avg Order Value</span>
                <div className="text-2xl font-black text-slate-900 mt-1">
                  ${kpis.avg_order_value.toFixed(2)}
                </div>
                <div className="text-xs text-indigo-600/80 mt-1 font-medium flex items-center gap-1">
                  <Target className="w-3.5 h-3.5" />
                  <span>Revenue per transaction</span>
                </div>
              </div>

              <div className="bg-gradient-to-br from-amber-50/60 to-white p-4 rounded-xl border border-amber-200/80 shadow-2xs">
                <span className="text-[11px] font-bold tracking-wider text-amber-700 uppercase">Customer Base</span>
                <div className="text-2xl font-black text-slate-900 mt-1">
                  {kpis.unique_customers ? kpis.unique_customers.toLocaleString() : customers?.total_profiled_customers || 'Profiled'}
                </div>
                <div className="text-xs text-amber-600/80 mt-1 font-medium flex items-center gap-1">
                  <Users className="w-3.5 h-3.5" />
                  <span>Unique buyers / accounts</span>
                </div>
              </div>
            </div>

            {/* Quick Summary Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              {/* Top Seller Teaser */}
              {products?.top_selling && products.top_selling.length > 0 && (
                <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/90">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Award className="w-4 h-4 text-amber-500" />
                      Top Revenue Drivers
                    </h4>
                    <button
                      onClick={() => setActiveTab('products')}
                      className="text-xs font-semibold text-blue-600 hover:underline"
                    >
                      View All
                    </button>
                  </div>
                  <div className="space-y-2">
                    {products.top_selling.slice(0, 3).map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2.5 bg-white rounded-lg border border-slate-200/80 shadow-2xs">
                        <div className="flex items-center gap-2.5">
                          <span className="w-5 h-5 rounded-full bg-slate-100 text-slate-700 text-[11px] font-bold flex items-center justify-center">
                            {idx + 1}
                          </span>
                          <div>
                            <div className="text-xs font-bold text-slate-900">{item.product_name}</div>
                            <div className="text-[10px] text-slate-500">{item.category} • {item.units_sold} units sold</div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-xs font-bold text-emerald-700">${item.revenue.toFixed(2)}</div>
                          <div className="text-[10px] text-slate-500">{item.revenue_share_pct}% share</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Customer Segment Breakdown Teaser */}
              {customers?.segments_summary && customers.segments_summary.length > 0 && (
                <div className="p-4 bg-slate-50/70 rounded-xl border border-slate-200/90">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Users className="w-4 h-4 text-blue-500" />
                      Customer Segmentation
                    </h4>
                    <button
                      onClick={() => setActiveTab('rfm')}
                      className="text-xs font-semibold text-blue-600 hover:underline"
                    >
                      View RFM
                    </button>
                  </div>
                  <div className="space-y-2">
                    {customers.segments_summary.slice(0, 3).map((seg, idx) => (
                      <div key={idx} className="p-2.5 bg-white rounded-lg border border-slate-200/80 shadow-2xs">
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-xs font-bold text-slate-900">{seg.segment_name}</span>
                          <span className="text-xs font-bold text-blue-700">{seg.percentage}% ({seg.customer_count})</span>
                        </div>
                        <div className="w-full bg-slate-100 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-blue-600 h-full rounded-full"
                            style={{ width: `${seg.percentage}%` }}
                          />
                        </div>
                        <div className="text-[10px] text-slate-500 mt-1 truncate">{seg.actionable_strategy}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 2. Product Analytics */}
        {activeTab === 'products' && products && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Top Selling Products */}
              <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-2xs">
                <div className="flex items-center gap-2 font-bold text-sm text-slate-900 mb-4 pb-2 border-b border-slate-100">
                  <Award className="w-4 h-4 text-emerald-600" />
                  <span>Top 5 Best-Selling Products (by Revenue)</span>
                </div>
                <div className="space-y-3">
                  {products.top_selling.map((item, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-6 h-6 rounded-md bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center">
                            #{idx + 1}
                          </span>
                          <span className="text-xs font-bold text-slate-900">{item.product_name}</span>
                        </div>
                        <span className="text-xs font-black text-emerald-700">${item.revenue.toFixed(2)}</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-2">
                        <span>Category: {item.category}</span>
                        <span>{item.units_sold} Units Sold</span>
                        <span>{item.revenue_share_pct}% Revenue Share</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Least Selling / Low Volume */}
              <div className="border border-slate-200 rounded-xl p-5 bg-white shadow-2xs">
                <div className="flex items-center gap-2 font-bold text-sm text-slate-900 mb-4 pb-2 border-b border-slate-100">
                  <AlertCircle className="w-4 h-4 text-amber-500" />
                  <span>Least-Selling / Underperforming Items</span>
                </div>
                <div className="space-y-3">
                  {products.least_selling.map((item, idx) => (
                    <div key={idx} className="p-3 bg-slate-50 rounded-lg border border-slate-200/80">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900">{item.product_name}</span>
                        <span className="text-xs font-bold text-slate-700">{item.units_sold} Units Sold</span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] text-slate-500 mt-1">
                        <span>Category: {item.category}</span>
                        <span>Revenue: ${item.revenue.toFixed(2)}</span>
                        <span className="text-amber-700 font-medium">Underperforming</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Trending Products */}
            {products.trending_products && products.trending_products.length > 0 && (
              <div className="border border-indigo-200/80 bg-indigo-50/30 rounded-xl p-5 shadow-2xs">
                <div className="flex items-center gap-2 font-bold text-sm text-indigo-950 mb-3">
                  <Zap className="w-4 h-4 text-indigo-600" />
                  <span>High-Velocity & Trending Products</span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {products.trending_products.map((t, idx) => (
                    <div key={idx} className="bg-white p-3.5 rounded-lg border border-indigo-200 shadow-2xs">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-slate-900 truncate">{t.product_name}</span>
                        <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-indigo-100 text-indigo-800">
                          +{t.growth_rate_pct}%
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-600 mt-2">{t.recommendation}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 3. Customer RFM */}
        {activeTab === 'rfm' && customers && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {customers.segments_summary.map((seg, idx) => (
                <div key={idx} className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-slate-900">{seg.segment_name}</span>
                    <span className="text-xs font-bold px-2 py-0.5 rounded-full bg-blue-50 text-blue-700 border border-blue-200">
                      {seg.customer_count} Customers ({seg.percentage}%)
                    </span>
                  </div>
                  <div className="text-sm font-black text-slate-900">
                    Avg Spend: ${seg.avg_spend.toFixed(2)}
                  </div>
                  <p className="text-[11px] text-slate-600 leading-relaxed bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                    💡 <span className="font-semibold text-slate-700">Strategy:</span> {seg.actionable_strategy}
                  </p>
                </div>
              ))}
            </div>

            {/* Top Customer Profiles */}
            {customers.top_customers && customers.top_customers.length > 0 && (
              <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
                <div className="bg-slate-50 px-4 py-3 border-b border-slate-200 flex items-center justify-between">
                  <span className="text-xs font-bold text-slate-900 uppercase tracking-wider">
                    High-Value Customer Profiles (Top Spenders)
                  </span>
                  <span className="text-xs text-slate-500 font-medium">
                    Profiled from transactions
                  </span>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-slate-100/80 text-slate-600 font-semibold uppercase tracking-wider text-[10px]">
                      <tr>
                        <th className="px-4 py-2.5">Customer / Client ID</th>
                        <th className="px-4 py-2.5">RFM Segment</th>
                        <th className="px-4 py-2.5">Orders Count</th>
                        <th className="px-4 py-2.5">Total Spend</th>
                        <th className="px-4 py-2.5">Last Active</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {customers.top_customers.map((c, idx) => (
                        <tr key={idx} className="hover:bg-slate-50/80">
                          <td className="px-4 py-2.5 font-mono font-bold text-slate-900">{c.customer_id}</td>
                          <td className="px-4 py-2.5">
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-emerald-50 text-emerald-800 border border-emerald-200">
                              {c.segment}
                            </span>
                          </td>
                          <td className="px-4 py-2.5 text-slate-700">{c.orders_count} orders</td>
                          <td className="px-4 py-2.5 font-bold text-emerald-700">${c.total_spend.toFixed(2)}</td>
                          <td className="px-4 py-2.5 text-slate-500">{c.last_active_days_ago} days ago</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Market Basket */}
        {activeTab === 'basket' && basket && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div>
                <h4 className="text-sm font-bold text-slate-900">Frequently Bought Together & Cross-Sell Affinities</h4>
                <p className="text-xs text-slate-500">Co-occurrence analysis across {basket.total_basket_transactions} customer shopping baskets</p>
              </div>
            </div>

            {basket.pairs.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-xs bg-slate-50 rounded-xl border border-dashed border-slate-200">
                Not enough multiple-item transaction baskets detected to establish product pairings.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {basket.pairs.map((p, idx) => (
                  <div key={idx} className="bg-white p-4 rounded-xl border border-slate-200 shadow-2xs space-y-3">
                    <div className="flex items-center gap-2 text-xs font-bold text-slate-900">
                      <span className="p-1.5 rounded-md bg-blue-50 text-blue-700 border border-blue-200 font-mono">
                        {p.item_a}
                      </span>
                      <span className="text-slate-400 font-bold">+</span>
                      <span className="p-1.5 rounded-md bg-indigo-50 text-indigo-700 border border-indigo-200 font-mono">
                        {p.item_b}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs font-medium text-slate-600 bg-slate-50 p-2 rounded-lg">
                      <span>Co-purchased: <strong>{p.co_occurrence_count} times</strong></span>
                      <span className="text-blue-700 font-bold">{p.confidence_pct}% Confidence</span>
                    </div>

                    <div className="text-[11px] text-slate-600 bg-emerald-50/60 border border-emerald-200 p-2.5 rounded-lg">
                      🎯 <strong className="text-emerald-900">Action:</strong> {p.recommendation}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* 5. Demand Forecast */}
        {activeTab === 'forecast' && forecast && (
          <div className="space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-slate-200">
              <div>
                <h4 className="text-sm font-bold text-slate-900">Demand Forecasting & Inventory Advisory</h4>
                <p className="text-xs text-slate-500">Methodology: {forecast.model_used}</p>
              </div>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    <th className="px-4 py-3">Product Name</th>
                    <th className="px-4 py-3">Historical Sold</th>
                    <th className="px-4 py-3">Run Rate / Day</th>
                    <th className="px-4 py-3">7-Day Demand</th>
                    <th className="px-4 py-3">30-Day Demand</th>
                    <th className="px-4 py-3">Stock Status</th>
                    <th className="px-4 py-3">Inventory Recommendation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {forecast.forecasts.map((f, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/80">
                      <td className="px-4 py-3 font-bold text-slate-900">{f.product_name}</td>
                      <td className="px-4 py-3 text-slate-700">{f.historical_units_sold} units</td>
                      <td className="px-4 py-3 text-slate-700 font-mono">{f.daily_run_rate}/day</td>
                      <td className="px-4 py-3 font-bold text-blue-700">{f.projected_demand_7d} units</td>
                      <td className="px-4 py-3 font-bold text-indigo-700">{f.projected_demand_30d} units</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                          f.inventory_status === 'CRITICAL_RESTOCK'
                            ? 'bg-rose-100 text-rose-800 border border-rose-300'
                            : f.inventory_status === 'RESTOCK_SOON'
                            ? 'bg-amber-100 text-amber-800 border border-amber-300'
                            : 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        }`}>
                          {f.inventory_status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-[11px] text-slate-600 max-w-[280px]">
                        {f.actionable_advice}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* 6. Unified Warehouse */}
        {activeTab === 'warehouse' && unifiedWarehouse && (
          <div className="space-y-4">
            <div className="p-4 bg-indigo-50/60 rounded-xl border border-indigo-200">
              <div className="flex items-center gap-2 font-bold text-indigo-950 text-sm">
                <Database className="w-4 h-4 text-indigo-600" />
                <span>{unifiedWarehouse.title}</span>
              </div>
              <p className="text-xs text-indigo-800 mt-1">
                Relational foreign-key merge across <strong>{unifiedWarehouse.source_tables.join(' + ')}</strong> produced {unifiedWarehouse.total_records} consolidated analytical warehouse rows.
              </p>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-x-auto shadow-2xs">
              <table className="w-full text-xs text-left">
                <thead className="bg-slate-100 text-slate-700 font-semibold uppercase tracking-wider text-[10px]">
                  <tr>
                    {unifiedWarehouse.columns.map((c, i) => (
                      <th key={i} className="px-4 py-2.5 whitespace-nowrap">{c}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {unifiedWarehouse.records.slice(0, 15).map((row, rIdx) => (
                    <tr key={rIdx} className="hover:bg-slate-50/80">
                      {unifiedWarehouse.columns.map((col, cIdx) => (
                        <td key={cIdx} className="px-4 py-2 font-mono text-slate-800 whitespace-nowrap">
                          {String(row[col] ?? '')}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
