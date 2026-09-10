import React, { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Store,
  Package,
  Users,
  ShoppingCart,
  Layers,
  ChevronDown,
  ChevronUp,
  ArrowUpRight,
  AlertTriangle,
  Sparkles,
  Award
} from 'lucide-react';
import { RetailIntelligence } from '../types';

interface RetailIntelligenceSectionProps {
  retailIntelligence?: RetailIntelligence;
}

export const RetailIntelligenceSection: React.FC<RetailIntelligenceSectionProps> = ({
  retailIntelligence
}) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);
  const [activeTab, setActiveTab] = useState<'overview' | 'items' | 'stores' | 'customers' | 'forecast'>('overview');

  if (!retailIntelligence) return null;

  const {
    entity_type,
    entity_label,
    entity_breakdown,
    best_selling_items = [],
    least_selling_items = [],
    store_sales = [],
    customer_patterns = [],
    sales_forecast = [],
    inventory_recommendations = [],
    summary_metrics = []
  } = retailIntelligence;

  const getEntityIcon = (type: string) => {
    switch (type) {
      case 'STORE':
        return <Store className="w-5 h-5 text-emerald-600" />;
      case 'ITEM':
        return <Package className="w-5 h-5 text-indigo-600" />;
      case 'CUSTOMER':
        return <Users className="w-5 h-5 text-blue-600" />;
      case 'COMBINED_TRANSACTION':
        return <ShoppingCart className="w-5 h-5 text-violet-600" />;
      default:
        return <Layers className="w-5 h-5 text-slate-600" />;
    }
  };

  const getEntityBadgeColor = (type: string) => {
    switch (type) {
      case 'STORE':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'ITEM':
        return 'bg-indigo-50 text-indigo-700 border-indigo-200';
      case 'CUSTOMER':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'COMBINED_TRANSACTION':
        return 'bg-violet-50 text-violet-700 border-violet-200';
      default:
        return 'bg-slate-50 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden transition-all mb-6">
      {/* Header Bar */}
      <div className="px-6 py-4 bg-slate-50/60 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-white shadow-sm border border-slate-200/80">
            {getEntityIcon(entity_type)}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base font-bold text-slate-900 tracking-tight">
                Retail Intelligence & Entity Classification
              </h2>
              <span className={`text-xs font-semibold px-2.5 py-0.5 rounded-full border ${getEntityBadgeColor(entity_type)}`}>
                {entity_type.replace('_', ' ')}
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-0.5">
              {entity_label}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Navigation Tabs */}
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-medium">
            <button
              onClick={() => setActiveTab('overview')}
              className={`px-3 py-1.5 rounded-md transition-colors ${
                activeTab === 'overview' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Overview
            </button>
            {best_selling_items.length > 0 && (
              <button
                onClick={() => setActiveTab('items')}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === 'items' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Item Sales
              </button>
            )}
            {store_sales.length > 0 && (
              <button
                onClick={() => setActiveTab('stores')}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === 'stores' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Store Sales
              </button>
            )}
            {customer_patterns.length > 0 && (
              <button
                onClick={() => setActiveTab('customers')}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === 'customers' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Customer Patterns
              </button>
            )}
            {sales_forecast.length > 0 && (
              <button
                onClick={() => setActiveTab('forecast')}
                className={`px-3 py-1.5 rounded-md transition-colors ${
                  activeTab === 'forecast' ? 'bg-white text-slate-900 shadow-sm font-semibold' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                Demand Forecast
              </button>
            )}
          </div>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100 transition-colors"
          >
            {isOpen ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {isOpen && (
        <div className="p-6 space-y-6">
          {/* Entity Separation Tags */}
          {entity_breakdown && (
            <div className="p-4 bg-slate-50/50 rounded-xl border border-slate-200/80">
              <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2.5 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-slate-400" />
                <span>Automated Entity Separation & Field Classification</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {/* Store Fields */}
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-emerald-700 mb-1.5">
                    <Store className="w-3.5 h-3.5" />
                    <span>Store Fields ({entity_breakdown.store_fields?.length || 0})</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {entity_breakdown.store_fields?.length ? (
                      entity_breakdown.store_fields.map((f, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 bg-emerald-50 text-emerald-700 rounded border border-emerald-100 font-mono">
                          {f}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No store columns</span>
                    )}
                  </div>
                </div>

                {/* Item Fields */}
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-indigo-700 mb-1.5">
                    <Package className="w-3.5 h-3.5" />
                    <span>Item Fields ({entity_breakdown.item_fields?.length || 0})</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {entity_breakdown.item_fields?.length ? (
                      entity_breakdown.item_fields.map((f, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded border border-indigo-100 font-mono">
                          {f}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No item columns</span>
                    )}
                  </div>
                </div>

                {/* Customer Fields */}
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-blue-700 mb-1.5">
                    <Users className="w-3.5 h-3.5" />
                    <span>Customer Fields ({entity_breakdown.customer_fields?.length || 0})</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {entity_breakdown.customer_fields?.length ? (
                      entity_breakdown.customer_fields.map((f, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 bg-blue-50 text-blue-700 rounded border border-blue-100 font-mono">
                          {f}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No customer columns</span>
                    )}
                  </div>
                </div>

                {/* Transaction Fields */}
                <div className="p-3 bg-white rounded-lg border border-slate-200">
                  <div className="flex items-center gap-1.5 text-xs font-bold text-violet-700 mb-1.5">
                    <ShoppingCart className="w-3.5 h-3.5" />
                    <span>Order / Bill Fields ({entity_breakdown.transaction_fields?.length || 0})</span>
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {entity_breakdown.transaction_fields?.length ? (
                      entity_breakdown.transaction_fields.map((f, i) => (
                        <span key={i} className="text-[11px] px-2 py-0.5 bg-violet-50 text-violet-700 rounded border border-violet-100 font-mono">
                          {f}
                        </span>
                      ))
                    ) : (
                      <span className="text-[11px] text-slate-400 italic">No transaction columns</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Metric KPI Cards */}
          {summary_metrics.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {summary_metrics.map((metric, idx) => (
                <div key={idx} className="p-4 bg-white rounded-xl border border-slate-200 shadow-xs hover:border-slate-300 transition-all">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-slate-500">{metric.label}</span>
                    {metric.trend === 'up' && <TrendingUp className="w-4 h-4 text-emerald-500" />}
                    {metric.trend === 'down' && <TrendingDown className="w-4 h-4 text-rose-500" />}
                    {metric.trend === 'neutral' && <Sparkles className="w-4 h-4 text-blue-500" />}
                  </div>
                  <div className="text-lg font-bold text-slate-900 tracking-tight">{metric.value}</div>
                  {metric.subtext && (
                    <div className="text-xs text-slate-400 mt-0.5 truncate">{metric.subtext}</div>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* Content View Based on Active Tab */}
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Best Selling Items */}
              {best_selling_items.length > 0 && (
                <div className="p-5 bg-white rounded-xl border border-slate-200">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-amber-500" />
                      <h3 className="text-sm font-bold text-slate-900">Top Best-Selling Items</h3>
                    </div>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200">
                      Ranked by Volume
                    </span>
                  </div>
                  <div className="space-y-2.5">
                    {best_selling_items.map((item) => (
                      <div key={item.rank} className="flex items-center justify-between p-2.5 rounded-lg bg-slate-50/70 border border-slate-100">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className={`w-5 h-5 flex items-center justify-center rounded-full text-[11px] font-bold ${
                            item.rank === 1 ? 'bg-amber-500 text-white' : 'bg-slate-200 text-slate-700'
                          }`}>
                            {item.rank}
                          </span>
                          <span className="text-xs font-semibold text-slate-800 truncate">{item.name}</span>
                        </div>
                        <span className="text-xs font-bold text-slate-900 shrink-0 ml-2">
                          {item.metric_value.toLocaleString()} {item.metric_label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Least Selling Items */}
              {least_selling_items.length > 0 && (
                <div className="p-5 bg-white rounded-xl border border-slate-200">
                  <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                    <div className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-rose-500" />
                      <h3 className="text-sm font-bold text-slate-900">Slow-Moving / Least-Selling Items</h3>
                    </div>
                    <span className="text-[11px] font-semibold px-2 py-0.5 rounded bg-rose-50 text-rose-700 border border-rose-200">
                      Clearance Watch
                    </span>
                  </div>
                  <div className="space-y-2.5">
                    {least_selling_items.map((item) => (
                      <div key={item.rank} className="flex items-center justify-between p-2.5 rounded-lg bg-rose-50/30 border border-rose-100/60">
                        <div className="flex items-center gap-2.5 min-w-0">
                          <span className="w-5 h-5 flex items-center justify-center rounded-full text-[11px] font-bold bg-rose-100 text-rose-700">
                            {item.rank}
                          </span>
                          <span className="text-xs font-semibold text-slate-800 truncate">{item.name}</span>
                        </div>
                        <span className="text-xs font-bold text-rose-800 shrink-0 ml-2">
                          {item.metric_value.toLocaleString()} {item.metric_label}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Inventory Recommendations */}
              {inventory_recommendations.length > 0 && (
                <div className="lg:col-span-2 p-5 bg-gradient-to-r from-blue-50/50 to-indigo-50/50 rounded-xl border border-blue-100">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertTriangle className="w-4 h-4 text-blue-600" />
                    <h3 className="text-sm font-bold text-slate-900">Automated Retail & Inventory Actions</h3>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    {inventory_recommendations.map((rec, i) => (
                      <div key={i} className="p-3.5 bg-white rounded-lg border border-blue-200/70 shadow-2xs">
                        <div className="flex items-center justify-between mb-1.5">
                          <span className="text-xs font-bold text-slate-900">{rec.action}: {rec.item}</span>
                          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                            rec.type === 'urgent' ? 'bg-amber-100 text-amber-800 border border-amber-200' : 'bg-blue-100 text-blue-800 border border-blue-200'
                          }`}>
                            {rec.badge}
                          </span>
                        </div>
                        <p className="text-xs text-slate-600">{rec.reason}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Item Tab */}
          {activeTab === 'items' && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-3">
                  <h3 className="text-sm font-bold text-slate-900">Top 5 Best Selling Ranked</h3>
                  {best_selling_items.map((item) => (
                    <div key={item.rank} className="p-3 bg-emerald-50/40 rounded-lg border border-emerald-100 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800">{item.rank}. {item.name}</span>
                      <span className="text-xs font-bold text-emerald-800">{item.metric_value} {item.metric_label}</span>
                    </div>
                  ))}
                </div>
                <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-3">
                  <h3 className="text-sm font-bold text-slate-900">Slowest Moving Products</h3>
                  {least_selling_items.map((item) => (
                    <div key={item.rank} className="p-3 bg-rose-50/40 rounded-lg border border-rose-100 flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-800">{item.rank}. {item.name}</span>
                      <span className="text-xs font-bold text-rose-800">{item.metric_value} {item.metric_label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Store Tab */}
          {activeTab === 'stores' && store_sales.length > 0 && (
            <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Store-wise Sales Performance</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {store_sales.map((st, i) => (
                  <div key={i} className="p-3.5 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Store className="w-4 h-4 text-emerald-600" />
                      <span className="text-xs font-bold text-slate-800">{st.store}</span>
                    </div>
                    <span className="text-xs font-bold text-slate-900">{st.sales} {st.unit}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Customer Tab */}
          {activeTab === 'customers' && customer_patterns.length > 0 && (
            <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-4">
              <h3 className="text-sm font-bold text-slate-900">Customer Purchase & Loyalty Segments</h3>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {customer_patterns.map((seg, i) => (
                  <div key={i} className="p-4 bg-blue-50/40 rounded-xl border border-blue-100">
                    <div className="text-xs font-medium text-blue-700">{seg.segment}</div>
                    <div className="text-xl font-bold text-slate-900 mt-1">{seg.count} Shoppers</div>
                    <div className="text-xs text-slate-500 mt-0.5">Share of Total: <span className="font-semibold text-blue-600">{seg.share}</span></div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Forecast Tab */}
          {activeTab === 'forecast' && sales_forecast.length > 0 && (
            <div className="p-5 bg-white rounded-xl border border-slate-200 space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-bold text-slate-900">Historical Sales & Future Demand Forecast</h3>
                <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 flex items-center gap-1">
                  <ArrowUpRight className="w-3.5 h-3.5" />
                  Moving Average +5% Growth Model
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
                {sales_forecast.map((fc, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border ${
                      fc.type === 'Projected Demand'
                        ? 'bg-indigo-50/70 border-indigo-200 shadow-2xs'
                        : 'bg-slate-50 border-slate-200'
                    }`}
                  >
                    <div className="text-[10px] font-bold text-slate-500 uppercase">{fc.period}</div>
                    <div className={`text-base font-bold mt-1 ${fc.type === 'Projected Demand' ? 'text-indigo-700' : 'text-slate-900'}`}>
                      ${fc.value.toLocaleString()}
                    </div>
                    <div className="text-[10px] text-slate-400 mt-0.5">{fc.type}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
