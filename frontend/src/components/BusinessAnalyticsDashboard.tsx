import React, { useState, useMemo } from 'react';
import {
  DollarSign,
  ShoppingCart,
  TrendingUp,
  AlertOctagon,
  Package,
  Users,
  Store,
  CheckCircle2,
  AlertTriangle,
  Info,
  BarChart3,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { BusinessAnalyticsReport, DemandPredictionReport } from '../types';

interface Props {
  analytics?: BusinessAnalyticsReport;
  demand?: DemandPredictionReport;
}

const PAGE_SIZE = 15;

export const BusinessAnalyticsDashboard: React.FC<Props> = ({ analytics, demand }) => {
  const [statusFilter, setStatusFilter] = useState<'all' | 'alerts' | 'healthy'>('all');
  const [page, setPage] = useState(1);

  const forecasts = demand?.forecasts || [];
  const filteredForecasts = useMemo(() => {
    if (statusFilter === 'alerts') {
      return forecasts.filter(f => f.reorder_urgency !== 'healthy');
    }
    if (statusFilter === 'healthy') {
      return forecasts.filter(f => f.reorder_urgency === 'healthy');
    }
    return forecasts;
  }, [forecasts, statusFilter]);

  // Top 6 items for visual Stock vs. 30-Day Demand chart
  const chartItems = useMemo(() => {
    return [...forecasts]
      .sort((a, b) => b.predicted_demand - a.predicted_demand)
      .slice(0, 6);
  }, [forecasts]);

  if (!analytics && !demand) {
    return (
      <div className="p-8 text-center bg-white rounded-xl border border-slate-200">
        <TrendingUp className="w-10 h-10 text-slate-400 mx-auto mb-2" />
        <h3 className="text-sm font-bold text-slate-800">Business Analytics Ready</h3>
        <p className="text-xs text-slate-500 mt-1">
          Upload and clean retail or inventory data to view revenue insights and 30-day stock predictions.
        </p>
      </div>
    );
  }

  const txn = analytics?.transaction_analytics;
  const store = analytics?.store_analytics;
  const cust = analytics?.customer_analytics;

  const formatCurrency = (val?: number) => {
    const num = val ?? 0;
    if (num >= 100) {
      return `$${Math.round(num).toLocaleString()}`;
    }
    return `$${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  };

  const formatUnits = (val?: number) => {
    return `${Math.round(val ?? 0).toLocaleString()} units`;
  };

  // Convert fractional daily velocity into clean human-readable whole units (zero ugly floats)
  const formatDailySales = (vel: number, pred30: number) => {
    if (vel >= 1) {
      return {
        main: `${Math.round(vel).toLocaleString()} units / day`,
        sub: `~${Math.round(vel * 7).toLocaleString()} per week`
      };
    }
    const weekly = Math.max(1, Math.round(vel * 7));
    const monthly = Math.max(1, Math.round(pred30 || vel * 30));
    return {
      main: `${weekly.toLocaleString()} units / week`,
      sub: `~${monthly.toLocaleString()} per month`
    };
  };

  // Format plain-English Reorder Action without floats or technical jargon
  const formatActionText = (
    urgency: 'critical' | 'medium' | 'healthy',
    reorderQty: number,
    daysLeft?: number,
    rawAction?: string
  ) => {
    const qtyInt = Math.max(1, Math.round(reorderQty || 0));
    const daysInt = daysLeft !== undefined && daysLeft !== null ? Math.max(0, Math.round(daysLeft)) : null;

    if (urgency === 'critical') {
      return daysInt !== null
        ? `Order ${qtyInt.toLocaleString()} units now — stock runs out in ~${daysInt} days`
        : `Order ${qtyInt.toLocaleString()} units immediately to prevent stockout`;
    }
    if (urgency === 'medium') {
      return `Plan order of ${qtyInt.toLocaleString()} units — 30-day demand exceeds current stock`;
    }
    if (
      rawAction &&
      !rawAction.toLowerCase().includes('forecast horizon') &&
      !rawAction.toLowerCase().includes('monitor stock')
    ) {
      return rawAction.replace(/(\d+)\.\d+/g, '$1');
    }
    return 'No order needed — current stock easily covers the next 30 days';
  };

  const totalPages = Math.max(1, Math.ceil(filteredForecasts.length / PAGE_SIZE));
  const safePage = Math.min(page, totalPages);
  const paginatedForecasts = filteredForecasts.slice((safePage - 1) * PAGE_SIZE, safePage * PAGE_SIZE);

  const alertCount = demand?.stock_shortage_alerts_count ?? 0;
  const totalItemsCount = demand?.total_products_analyzed ?? forecasts.length;

  return (
    <div className="space-y-6">
      {/* Plain-English Executive Summary Banner */}
      <div
        className={`p-4 rounded-xl border flex items-start gap-3 ${
          alertCount > 0
            ? 'bg-amber-50/70 border-amber-200 text-amber-950'
            : 'bg-emerald-50/70 border-emerald-200 text-emerald-950'
        }`}
      >
        {alertCount > 0 ? (
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
        ) : (
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
        )}
        <div className="text-xs leading-relaxed">
          <div className="font-bold text-sm">
            Executive Summary:{' '}
            {alertCount === 0
              ? 'All Inventory Levels Are Healthy for the Next 30 Days'
              : `${alertCount} Product${alertCount > 1 ? 's Need' : ' Needs'} Restocking Within 30 Days`}
          </div>
          <p className="text-slate-700 mt-0.5">
            {txn ? (
              <>
                Recorded <strong>{(txn.total_transactions ?? 0).toLocaleString()} orders</strong> generating{' '}
                <strong>{formatCurrency(txn.total_revenue)}</strong> in total sales (average order:{' '}
                <strong>{formatCurrency(txn.average_transaction_value)}</strong>).{' '}
              </>
            ) : null}
            {totalItemsCount > 0 ? (
              alertCount === 0 ? (
                <>
                  Every single one of the <strong>{totalItemsCount.toLocaleString()} analyzed items</strong> has enough
                  warehouse stock to meet expected 30-day customer demand. No urgent purchase orders are required.
                </>
              ) : (
                <>
                  Out of <strong>{totalItemsCount.toLocaleString()} analyzed items</strong>,{' '}
                  <strong>{alertCount.toLocaleString()}</strong> may run low over the next 30 days and have recommended
                  reorder quantities listed below.
                </>
              )
            ) : null}
          </p>
        </div>
      </div>

      {/* KPI Overview Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Sales Revenue</span>
            <DollarSign className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">{formatCurrency(txn?.total_revenue)}</div>
          <div className="mt-1 text-[11px] text-emerald-600 font-semibold">Total money earned from clean orders</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Total Orders</span>
            <ShoppingCart className="w-4 h-4 text-blue-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            {(txn?.total_transactions ?? 0).toLocaleString()}
          </div>
          <div className="mt-1 text-[11px] text-slate-500 font-medium">Completed customer purchases</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Avg. Order Value</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="mt-2 text-2xl font-black text-slate-900">
            {formatCurrency(txn?.average_transaction_value)}
          </div>
          <div className="mt-1 text-[11px] text-slate-500 font-medium">Average spend per customer order</div>
        </div>

        <div className="p-4 bg-white rounded-xl border border-slate-200 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500">
            <span className="text-[11px] font-bold uppercase tracking-wider">Low-Stock Alerts</span>
            <AlertOctagon className={`w-4 h-4 ${alertCount > 0 ? 'text-rose-600' : 'text-emerald-600'}`} />
          </div>
          <div className={`mt-2 text-2xl font-black ${alertCount > 0 ? 'text-rose-600' : 'text-emerald-600'}`}>
            {alertCount.toLocaleString()}
          </div>
          <div className={`mt-1 text-[11px] font-semibold ${alertCount > 0 ? 'text-rose-700' : 'text-emerald-700'}`}>
            {alertCount > 0 ? 'Items needing restock soon' : '0 stockouts expected in 30 days'}
          </div>
        </div>
      </div>

      {/* Visual Chart: Current Stock vs. 30-Day Needed Demand */}
      {chartItems.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-indigo-600" />
                Visual Stock vs. 30-Day Customer Demand (Top Products)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Quickly compare how many units you currently have in stock against how many customers will buy next month
              </p>
            </div>
            <div className="flex items-center gap-4 text-[11px] font-semibold">
              <span className="flex items-center gap-1.5 text-slate-700">
                <span className="w-3 h-3 rounded-xs bg-emerald-500 inline-block" /> Current Stock
              </span>
              <span className="flex items-center gap-1.5 text-slate-700">
                <span className="w-3 h-3 rounded-xs bg-blue-600 inline-block" /> 30-Day Needed Demand
              </span>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {chartItems.map((item, idx) => {
              const stockInt = Math.round(item.current_stock);
              const demandInt = Math.round(item.predicted_demand);
              const maxScale = Math.max(stockInt, demandInt, 1);
              const stockPct = Math.min(100, Math.max(4, Math.round((stockInt / maxScale) * 100)));
              const demandPct = Math.min(100, Math.max(4, Math.round((demandInt / maxScale) * 100)));
              const isShort = item.reorder_urgency !== 'healthy';

              return (
                <div key={idx} className="p-3 rounded-lg bg-slate-50 border border-slate-200/80 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-slate-900 truncate pr-2">{item.item_name}</span>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        isShort ? 'bg-rose-100 text-rose-800' : 'bg-emerald-100 text-emerald-800'
                      }`}
                    >
                      {isShort ? 'Needs Restock' : 'Enough Stock'}
                    </span>
                  </div>

                  <div className="space-y-1.5 text-[11px]">
                    <div>
                      <div className="flex justify-between text-slate-600 mb-0.5">
                        <span>In Warehouse Now</span>
                        <span className="font-bold text-slate-800">{stockInt.toLocaleString()} units</span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div
                          className={`h-full rounded-full ${isShort ? 'bg-amber-500' : 'bg-emerald-500'}`}
                          style={{ width: `${stockPct}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex justify-between text-slate-600 mb-0.5">
                        <span>Needed Next 30 Days</span>
                        <span className="font-bold text-blue-700">{demandInt.toLocaleString()} units</span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${demandPct}%` }} />
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Demand Prediction & Inventory Forecast Table */}
      {demand && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Package className="w-4 h-4 text-blue-600" />
                30-Day Product Demand & Restock Plan ({demand.forecast_horizon_days}-Day Forecast)
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                All numbers are rounded to whole physical units — showing daily sales speed, expected 30-day demand, and clear restock actions
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-2">
              {forecasts.length > 0 && (
                <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5 text-[11px] font-semibold">
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('all');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'all' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    All ({forecasts.length})
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('alerts');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'alerts' ? 'bg-white text-rose-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Needs Reorder ({forecasts.filter(f => f.reorder_urgency !== 'healthy').length})
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setStatusFilter('healthy');
                      setPage(1);
                    }}
                    className={`px-2.5 py-1 rounded-md transition ${
                      statusFilter === 'healthy' ? 'bg-white text-emerald-700 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
                    }`}
                  >
                    Healthy ({forecasts.filter(f => f.reorder_urgency === 'healthy').length})
                  </button>
                </div>
              )}

              <span
                className={`text-[10px] font-bold px-2.5 py-1 rounded-full uppercase border ${
                  demand.data_sufficiency_status === 'sufficient'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                    : 'bg-amber-50 text-amber-800 border-amber-200'
                }`}
              >
                {demand.data_sufficiency_status === 'sufficient' ? 'Verified History' : demand.data_sufficiency_status}
              </span>
            </div>
          </div>

          {demand.limitations && demand.data_sufficiency_status !== 'sufficient' && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-900 flex items-start gap-2">
              <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Data Limitation: </span>
                {demand.limitations}
              </div>
            </div>
          )}

          {paginatedForecasts.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200 text-slate-700">
                    <th className="py-2.5 px-3 font-bold">
                      <div>Item Name</div>
                      <div className="text-[10px] font-normal text-slate-400">Product / Model</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>Current Stock</div>
                      <div className="text-[10px] font-normal text-slate-400">Available in warehouse</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>Daily Sales Speed</div>
                      <div className="text-[10px] font-normal text-slate-400">Average selling rate</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>30-Day Predicted Demand</div>
                      <div className="text-[10px] font-normal text-slate-400">Units needed next month</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>Expected Min – Max Range</div>
                      <div className="text-[10px] font-normal text-slate-400">Slow month to busy month</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>Stock Status</div>
                      <div className="text-[10px] font-normal text-slate-400">Health & days left</div>
                    </th>
                    <th className="py-2.5 px-3 font-bold">
                      <div>Recommended Action</div>
                      <div className="text-[10px] font-normal text-slate-400">What manager should do</div>
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {paginatedForecasts.map((fc, idx) => {
                    const stockUnits = Math.round(fc.current_stock);
                    const predUnits = Math.round(fc.predicted_demand);
                    const minUnits = Math.round(fc.lower_confidence_bound);
                    const maxUnits = Math.round(fc.upper_confidence_bound);
                    const velocityDisplay = formatDailySales(fc.historical_sales_velocity_daily, predUnits);
                    const daysSupply =
                      fc.projected_days_until_stockout !== undefined && fc.projected_days_until_stockout !== null
                        ? Math.round(fc.projected_days_until_stockout)
                        : null;

                    const statusBadge =
                      fc.reorder_urgency === 'critical'
                        ? {
                            label: 'Urgent Reorder',
                            cls: 'bg-rose-100 text-rose-800 border-rose-200',
                            sub: daysSupply !== null ? `Runs out in ~${daysSupply} days` : 'Immediate shortage'
                          }
                        : fc.reorder_urgency === 'medium'
                        ? {
                            label: 'Low Stock',
                            cls: 'bg-amber-100 text-amber-800 border-amber-200',
                            sub: daysSupply !== null ? `~${daysSupply} days supply left` : 'Below peak demand'
                          }
                        : {
                            label: 'Healthy Stock',
                            cls: 'bg-emerald-100 text-emerald-800 border-emerald-200',
                            sub:
                              daysSupply !== null
                                ? daysSupply > 90
                                  ? '90+ days supply'
                                  : `~${daysSupply} days supply`
                                : 'Covers 30+ days'
                          };

                    return (
                      <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                        <td className="py-3 px-3 font-bold text-slate-900">{fc.item_name}</td>
                        <td className="py-3 px-3 font-semibold text-slate-800">{formatUnits(stockUnits)}</td>
                        <td className="py-3 px-3">
                          <div className="font-semibold text-slate-800">{velocityDisplay.main}</div>
                          <div className="text-[10px] text-slate-400">{velocityDisplay.sub}</div>
                        </td>
                        <td className="py-3 px-3">
                          <span className="inline-flex items-center px-2 py-0.5 rounded-md bg-blue-50 text-blue-700 font-bold">
                            {formatUnits(predUnits)}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-slate-700">
                          <div className="font-semibold">
                            {minUnits.toLocaleString()} to {maxUnits.toLocaleString()} units
                          </div>
                          <div className="text-[10px] text-slate-400">
                            Min {minUnits.toLocaleString()} • Max {maxUnits.toLocaleString()}
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <span
                            className={`inline-block px-2 py-0.5 rounded-full text-[10px] font-bold border ${statusBadge.cls}`}
                          >
                            {statusBadge.label}
                          </span>
                          <div className="text-[10px] text-slate-500 mt-0.5">{statusBadge.sub}</div>
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-700 font-medium">
                          {formatActionText(
                            fc.reorder_urgency,
                            fc.recommended_reorder_quantity,
                            fc.projected_days_until_stockout,
                            fc.actionable_recommendation
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {/* Pagination Controls */}
              {filteredForecasts.length > PAGE_SIZE && (
                <div className="flex items-center justify-between pt-3 mt-3 border-t border-slate-100 text-xs text-slate-600">
                  <span>
                    Showing <strong>{(safePage - 1) * PAGE_SIZE + 1}</strong> to{' '}
                    <strong>{Math.min(safePage * PAGE_SIZE, filteredForecasts.length)}</strong> of{' '}
                    <strong>{filteredForecasts.length}</strong> products
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={safePage === 1}
                      className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                    >
                      <ChevronLeft className="w-3.5 h-3.5" />
                    </button>
                    <span className="px-2 font-semibold text-slate-800">
                      Page {safePage} of {totalPages}
                    </span>
                    <button
                      type="button"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={safePage === totalPages}
                      className="p-1.5 rounded border border-slate-200 bg-white hover:bg-slate-50 disabled:opacity-40"
                    >
                      <ChevronRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="p-6 text-center text-xs text-slate-500 bg-slate-50 rounded-lg border border-slate-100">
              No items match the selected filter.
            </div>
          )}
        </div>
      )}

      {/* Grid: Store Analytics & Top Spenders */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Store Analytics */}
        {store && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Store className="w-4 h-4 text-blue-600" />
              Store / Region Performance ({store.total_stores} Locations)
            </h3>
            <div className="space-y-2">
              {store.store_wise_metrics?.map((st, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-800">{st.store_name}</div>
                    <div className="text-[11px] text-slate-500">
                      ID: {st.store_id} • {st.transactions_count.toLocaleString()} orders
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-slate-900">{formatCurrency(st.total_sales)}</div>
                    <div className="text-[11px] text-slate-500 font-medium">
                      Stock: {Math.round(st.total_stock).toLocaleString()} units
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Customer Spending & Loyalty */}
        {cust && cust.total_customers > 0 && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 space-y-3">
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-1.5 pb-2 border-b border-slate-100">
              <Users className="w-4 h-4 text-indigo-600" />
              Top Customers & Lifetime Value ({cust.total_customers.toLocaleString()} Customers)
            </h3>
            <div className="space-y-2">
              {cust.top_customers_by_spend?.map((cu, idx) => (
                <div
                  key={idx}
                  className="p-3 bg-slate-50 rounded-lg border border-slate-200 flex items-center justify-between text-xs"
                >
                  <div>
                    <div className="font-bold text-slate-800">{cu.customer_name}</div>
                    <div className="text-[11px] text-slate-500">
                      ID: {cu.customer_id} • {cu.orders_count.toLocaleString()} purchase(s)
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-emerald-700">{formatCurrency(cu.total_spend)}</div>
                    <div className="text-[10px] text-slate-400">Total Spend</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
