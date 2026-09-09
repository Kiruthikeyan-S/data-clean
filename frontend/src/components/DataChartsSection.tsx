import React, { useState } from 'react';
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  Sparkles,
  LayoutGrid,
  Filter
} from 'lucide-react';
import { DataVisualizations, DatasetChart } from '../types';

interface DataChartsSectionProps {
  visualizations?: DataVisualizations;
}

type ChartDisplayType = 'donut' | 'pie' | 'bar' | 'column';

export const DataChartsSection: React.FC<DataChartsSectionProps> = ({ visualizations }) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);
  const [selectedColumn, setSelectedColumn] = useState<string>('all');
  const [chartTypeOverrides, setChartTypeOverrides] = useState<Record<string, ChartDisplayType>>({});
  const [globalType, setGlobalType] = useState<ChartDisplayType | 'auto'>('auto');

  if (!visualizations || !visualizations.has_charts || !visualizations.charts || visualizations.charts.length === 0) {
    return null;
  }

  const charts = visualizations.charts;
  const filteredCharts = selectedColumn === 'all'
    ? charts
    : charts.filter((c) => c.column_name === selectedColumn);

  const handleGlobalTypeChange = (type: ChartDisplayType | 'auto') => {
    setGlobalType(type);
    if (type !== 'auto') {
      const newOverrides: Record<string, ChartDisplayType> = {};
      charts.forEach((c) => {
        newOverrides[c.id] = type;
      });
      setChartTypeOverrides(newOverrides);
    } else {
      setChartTypeOverrides({});
    }
  };

  const handleChartTypeChange = (chartId: string, type: ChartDisplayType) => {
    setChartTypeOverrides((prev) => ({
      ...prev,
      [chartId]: type,
    }));
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-2xs overflow-hidden transition-all">
      {/* Collapsible Header Bar */}
      <div className="px-5 py-3.5 bg-slate-50/70 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-md bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 flex-shrink-0">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold text-slate-900 tracking-tight">
                Data Distribution & Analytics
              </h2>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                {charts.length} {charts.length === 1 ? 'Chart Available' : 'Charts Available'}
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Interactive visualizations and categorical distributions
            </p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-2 self-end sm:self-center">
          <button
            type="button"
            onClick={() => setIsOpen(!isOpen)}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-slate-700 bg-white border border-slate-300 rounded-md hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs"
          >
            {isOpen ? (
              <>
                <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
                <span>Hide Diagrams</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                <span>Show Diagrams ({charts.length})</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-5 space-y-5">
          {/* Options & Filter Bar */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 text-xs">
            {/* Column Selector Tabs */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-slate-400 font-medium flex items-center gap-1 mr-1">
                <Filter className="w-3 h-3" />
                <span>Filter:</span>
              </span>
              <button
                type="button"
                onClick={() => setSelectedColumn('all')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  selectedColumn === 'all'
                    ? 'bg-blue-600 text-white shadow-2xs'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                All Columns ({charts.length})
              </button>
              {charts.map((c) => (
                <button
                  key={c.id}
                  type="button"
                  onClick={() => setSelectedColumn(c.column_name)}
                  className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                    selectedColumn === c.column_name
                      ? 'bg-blue-600 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {c.column_name}
                </button>
              ))}
            </div>

            {/* Global Chart Style Switcher */}
            <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-500 px-2 font-medium flex items-center gap-1">
                <LayoutGrid className="w-3 h-3 text-slate-400" />
                <span>View:</span>
              </span>
              {(['auto', 'donut', 'pie', 'bar', 'column'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => handleGlobalTypeChange(mode)}
                  className={`px-2 py-0.5 rounded text-[11px] font-medium capitalize transition-all ${
                    globalType === mode
                      ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                      : 'text-slate-500 hover:text-slate-800'
                  }`}
                >
                  {mode}
                </button>
              ))}
            </div>
          </div>

          {/* AI Automated Insights */}
          {visualizations.summary_insights && visualizations.summary_insights.length > 0 && (
            <div className="p-3.5 bg-blue-50/40 border border-blue-100 rounded-lg">
              <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-900 mb-1.5">
                <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                <span>Automated Data Insights</span>
              </div>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-1.5">
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
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {filteredCharts.map((chart) => {
              const activeType = chartTypeOverrides[chart.id] || (chart.chart_type as ChartDisplayType) || 'donut';
              return (
                <ChartCard
                  key={chart.id}
                  chart={chart}
                  currentType={activeType}
                  onTypeChange={(type) => handleChartTypeChange(chart.id, type)}
                />
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

interface ChartCardProps {
  chart: DatasetChart;
  currentType: ChartDisplayType;
  onTypeChange: (type: ChartDisplayType) => void;
}

const ChartCard: React.FC<ChartCardProps> = ({ chart, currentType, onTypeChange }) => {
  const totalValue = chart.data.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between hover:border-slate-300 transition-colors shadow-2xs">
      {/* Chart Header */}
      <div className="flex items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-100">
        <div>
          <h3 className="text-xs font-bold text-slate-900">{chart.title}</h3>
          <span className="text-[10px] text-slate-400 font-mono">Column: {chart.column_name}</span>
        </div>

        {/* Diagram Option Switcher */}
        <div className="flex items-center gap-0.5 bg-slate-100 p-0.5 rounded-md border border-slate-200 text-[10px]">
          {(['donut', 'pie', 'bar', 'column'] as const).map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => onTypeChange(type)}
              className={`px-1.5 py-0.5 rounded capitalize font-medium transition-colors ${
                currentType === type
                  ? 'bg-white text-slate-900 shadow-2xs font-bold'
                  : 'text-slate-500 hover:text-slate-800'
              }`}
            >
              {type}
            </button>
          ))}
        </div>
      </div>

      {/* Dynamic Diagram Rendering */}
      {currentType === 'donut' && <DonutChartView chart={chart} totalValue={totalValue} />}
      {currentType === 'pie' && <PieChartView chart={chart} totalValue={totalValue} />}
      {currentType === 'bar' && <BarChartView chart={chart} totalValue={totalValue} />}
      {currentType === 'column' && <ColumnChartView chart={chart} totalValue={totalValue} />}
    </div>
  );
};

interface ChartViewProps {
  chart: DatasetChart;
  totalValue: number;
}

// 1. Donut Chart Component
const DonutChartView: React.FC<ChartViewProps> = ({ chart, totalValue }) => {
  const radius = 40;
  const circumference = 2 * Math.PI * radius;
  let accumulatedOffset = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 py-2">
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
        <div className="absolute flex flex-col items-center justify-center text-center pointer-events-none">
          <span className="text-xs font-bold text-slate-800">{totalValue}</span>
          <span className="text-[9px] text-slate-400 uppercase tracking-wider font-semibold">Total</span>
        </div>
      </div>

      <ChartLegend chart={chart} totalValue={totalValue} />
    </div>
  );
};

// 2. Pie Chart Component
const PieChartView: React.FC<ChartViewProps> = ({ chart, totalValue }) => {
  let cumulativeAngle = 0;

  return (
    <div className="flex flex-col sm:flex-row items-center gap-6 py-2">
      <div className="relative w-32 h-32 flex-shrink-0 flex items-center justify-center">
        <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
          {chart.data.map((item, idx) => {
            const pct = item.percentage ?? (totalValue > 0 ? (item.value / totalValue) * 100 : 0);
            const angle = (pct / 100) * 360;
            const startAngle = cumulativeAngle;
            cumulativeAngle += angle;

            const startRad = (startAngle * Math.PI) / 180;
            const endRad = ((startAngle + angle) * Math.PI) / 180;

            const x1 = 50 + 45 * Math.cos(startRad);
            const y1 = 50 + 45 * Math.sin(startRad);
            const x2 = 50 + 45 * Math.cos(endRad);
            const y2 = 50 + 45 * Math.sin(endRad);

            const largeArc = angle > 180 ? 1 : 0;
            const pathData = pct >= 99.9
              ? `M 50,50 m -45,0 a 45,45 0 1,0 90,0 a 45,45 0 1,0 -90,0`
              : `M 50,50 L ${x1},${y1} A 45,45 0 ${largeArc},1 ${x2},${y2} Z`;

            return (
              <path
                key={idx}
                d={pathData}
                fill={item.color || '#3b82f6'}
                stroke="#ffffff"
                strokeWidth="1.5"
                className="transition-all duration-300 hover:opacity-90"
              />
            );
          })}
        </svg>
      </div>

      <ChartLegend chart={chart} totalValue={totalValue} />
    </div>
  );
};

// 3. Horizontal Bar Chart Component
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

// 4. Vertical Column Chart Component
const ColumnChartView: React.FC<ChartViewProps> = ({ chart }) => {
  const maxVal = Math.max(...chart.data.map((d) => d.value), 1);

  return (
    <div className="pt-4 pb-2">
      <div className="flex items-end justify-around gap-2 h-36 border-b border-slate-200 px-2 pb-1">
        {chart.data.map((item, idx) => {
          const heightPct = Math.max(Math.round((item.value / maxVal) * 100), 8);

          return (
            <div key={idx} className="flex-1 flex flex-col items-center gap-1 group max-w-[48px]">
              <span className="text-[10px] font-mono text-slate-500 font-semibold opacity-0 group-hover:opacity-100 transition-opacity">
                {item.value}
              </span>
              <div className="w-full bg-slate-100 rounded-t-sm flex items-end justify-center h-28 overflow-hidden">
                <div
                  className="w-full rounded-t-sm transition-all duration-500"
                  style={{
                    height: `${heightPct}%`,
                    backgroundColor: item.color || '#3b82f6',
                  }}
                />
              </div>
              <span className="text-[10px] text-slate-600 truncate max-w-full font-medium" title={item.label}>
                {item.label}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// Shared Legend Component
const ChartLegend: React.FC<ChartViewProps> = ({ chart, totalValue }) => {
  return (
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
  );
};
