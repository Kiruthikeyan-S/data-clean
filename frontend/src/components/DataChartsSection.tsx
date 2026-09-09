import React from 'react';
import { BarChart3, PieChart, Sparkles } from 'lucide-react';
import { DataVisualizations, DatasetChart } from '../types';

interface DataChartsSectionProps {
  visualizations?: DataVisualizations;
}

export const DataChartsSection: React.FC<DataChartsSectionProps> = ({ visualizations }) => {
  if (!visualizations || !visualizations.has_charts || !visualizations.charts || visualizations.charts.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-md bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Data Distribution & Analytics</span>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                {visualizations.charts.length} {visualizations.charts.length === 1 ? 'Chart' : 'Charts'}
              </span>
            </h2>
            <p className="text-xs text-slate-500">
              Categorical breakdowns and distribution metrics derived from cleaned dataset
            </p>
          </div>
        </div>
      </div>

      {/* AI Automated Insights */}
      {visualizations.summary_insights && visualizations.summary_insights.length > 0 && (
        <div className="mx-5 mt-4 p-3.5 bg-blue-50/40 border border-blue-100 rounded-lg">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 mb-1.5">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Key Data Insights</span>
          </div>
          <ul className="space-y-1">
            {visualizations.summary_insights.map((insight, idx) => (
              <li key={idx} className="text-xs text-slate-700 flex items-start gap-2">
                <span className="text-blue-500 font-bold">•</span>
                <span>{insight}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Charts Grid */}
      <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-6">
        {visualizations.charts.map((chart) => (
          <ChartCard key={chart.id} chart={chart} />
        ))}
      </div>
    </div>
  );
};

interface ChartCardProps {
  chart: DatasetChart;
}

const ChartCard: React.FC<ChartCardProps> = ({ chart }) => {
  const isDonut = chart.chart_type === 'donut' || chart.chart_type === 'pie';
  const totalValue = chart.data.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between hover:border-slate-300 transition-colors shadow-2xs">
      {/* Chart Header */}
      <div className="flex items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-100">
        <div>
          <h3 className="text-xs font-semibold text-slate-900">{chart.title}</h3>
          <span className="text-[10px] text-slate-400 font-mono">Column: {chart.column_name}</span>
        </div>
        <div className="flex items-center gap-1 text-[11px] text-slate-500 bg-slate-100 px-2 py-0.5 rounded font-medium capitalize">
          {isDonut ? <PieChart className="w-3 h-3 text-slate-500" /> : <BarChart3 className="w-3 h-3 text-slate-500" />}
          <span>{chart.chart_type}</span>
        </div>
      </div>

      {/* Chart Body */}
      {isDonut ? (
        <DonutChartView chart={chart} totalValue={totalValue} />
      ) : (
        <BarChartView chart={chart} totalValue={totalValue} />
      )}
    </div>
  );
};

interface ChartViewProps {
  chart: DatasetChart;
  totalValue: number;
}

const DonutChartView: React.FC<ChartViewProps> = ({ chart, totalValue }) => {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  let accumulatedOffset = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 py-2">
      {/* Donut Graphic */}
      <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          <circle
            cx="50"
            cy="50"
            r={radius}
            fill="transparent"
            stroke="#f1f5f9"
            strokeWidth="14"
          />
          {chart.data.map((item, idx) => {
            const pct = item.percentage ?? (totalValue > 0 ? (item.value / totalValue) * 100 : 0);
            const strokeDasharray = `${(pct / 100) * circumference} ${circumference}`;
            const strokeDashoffset = -accumulatedOffset;
            accumulatedOffset += (pct / 100) * circumference;

            return (
              <circle
                key={idx}
                cx="50"
                cy="50"
                r={radius}
                fill="transparent"
                stroke={item.color || '#3b82f6'}
                strokeWidth="14"
                strokeDasharray={strokeDasharray}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-300 hover:opacity-90"
              />
            );
          })}
        </svg>
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="text-xs font-bold text-slate-800">{totalValue}</span>
          <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Total</span>
        </div>
      </div>

      {/* Legend & Breakdown */}
      <div className="flex-1 w-full space-y-2">
        {chart.data.map((item, idx) => {
          const pct = item.percentage ?? (totalValue > 0 ? Math.round((item.value / totalValue) * 100) : 0);
          return (
            <div key={idx} className="flex items-center justify-between text-xs gap-2">
              <div className="flex items-center gap-2 min-w-0">
                <span
                  className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                  style={{ backgroundColor: item.color || '#3b82f6' }}
                />
                <span className="text-slate-700 truncate font-medium" title={item.label}>
                  {item.label}
                </span>
              </div>
              <div className="flex items-center gap-2 flex-shrink-0 font-mono text-[11px]">
                <span className="text-slate-500">{item.value}</span>
                <span className="px-1.5 py-0.5 rounded bg-slate-100 text-slate-700 font-semibold text-[10px]">
                  {pct}%
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const BarChartView: React.FC<ChartViewProps> = ({ chart, totalValue }) => {
  const maxVal = Math.max(...chart.data.map((d) => d.value), 1);

  return (
    <div className="space-y-3 py-2">
      {chart.data.map((item, idx) => {
        const pctOfMax = Math.round((item.value / maxVal) * 100);
        const actualPct = item.percentage ?? (totalValue > 0 ? Math.round((item.value / totalValue) * 100) : 0);

        return (
          <div key={idx} className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-700 font-medium truncate max-w-[200px]" title={item.label}>
                {item.label}
              </span>
              <div className="flex items-center gap-2 font-mono text-[11px] text-slate-500">
                <span>{item.value}</span>
                <span className="text-slate-400 font-normal">({actualPct}%)</span>
              </div>
            </div>
            {/* Progress Track */}
            <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500"
                style={{
                  width: `${pctOfMax}%`,
                  backgroundColor: item.color || '#3b82f6',
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
};
