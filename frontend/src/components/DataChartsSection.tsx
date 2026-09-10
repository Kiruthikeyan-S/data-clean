import React, { useState, useRef, useEffect } from 'react';
import {
  BarChart3,
  ChevronDown,
  ChevronUp,
  LayoutGrid,
  Filter,
  Download,
  Maximize2,
  X,
  Binary,
  PieChart as PieIcon,
  Check,
  CircleDot,
  BarChart2,
  Columns
} from 'lucide-react';
import { DataVisualizations, DatasetChart, MatplotlibPlot } from '../types';

interface DataChartsSectionProps {
  visualizations?: DataVisualizations;
}

type ChartDisplayType = 'donut' | 'pie' | 'bar' | 'column';
type TabViewMode = 'all' | 'interactive' | 'matplotlib';

const CHART_TYPE_OPTIONS: { id: ChartDisplayType | 'auto'; label: string; desc: string; icon: React.FC<{ className?: string }> }[] = [
  { id: 'auto', label: 'Auto (Recommended)', desc: 'Optimal visual based on data distribution', icon: LayoutGrid },
  { id: 'donut', label: 'Donut Chart', desc: 'Ring chart with center summary metric', icon: CircleDot },
  { id: 'pie', label: 'Pie Chart', desc: 'Solid proportional circular slices', icon: PieIcon },
  { id: 'bar', label: 'Horizontal Bar', desc: 'Linear progress bars with value badges', icon: BarChart2 },
  { id: 'column', label: 'Vertical Column', desc: 'Categorical distribution bar columns', icon: Columns },
];

export const DataChartsSection: React.FC<DataChartsSectionProps> = ({ visualizations }) => {
  const [isOpen, setIsOpen] = useState<boolean>(true);
  const [selectedColumn, setSelectedColumn] = useState<string>('all');
  const [chartTypeOverrides, setChartTypeOverrides] = useState<Record<string, ChartDisplayType>>({});
  const [globalType, setGlobalType] = useState<ChartDisplayType | 'auto'>('auto');
  const [activeTab, setActiveTab] = useState<TabViewMode>('all');
  const [previewPlot, setPreviewPlot] = useState<MatplotlibPlot | null>(null);

  // Dropdown states
  const [isGlobalTypeDropdownOpen, setIsGlobalTypeDropdownOpen] = useState<boolean>(false);
  const [isColumnDropdownOpen, setIsColumnDropdownOpen] = useState<boolean>(false);

  const globalTypeDropdownRef = useRef<HTMLDivElement>(null);
  const columnDropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (globalTypeDropdownRef.current && !globalTypeDropdownRef.current.contains(event.target as Node)) {
        setIsGlobalTypeDropdownOpen(false);
      }
      if (columnDropdownRef.current && !columnDropdownRef.current.contains(event.target as Node)) {
        setIsColumnDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (!visualizations || !visualizations.has_charts) {
    return null;
  }

  const charts = visualizations.charts || [];
  const matplotlibPlots = visualizations.matplotlib_plots || [];

  if (charts.length === 0 && matplotlibPlots.length === 0) {
    return null;
  }

  const filteredCharts = selectedColumn === 'all'
    ? charts
    : charts.filter((c) => c.column_name === selectedColumn);

  const handleGlobalTypeChange = (type: ChartDisplayType | 'auto') => {
    setGlobalType(type);
    setIsGlobalTypeDropdownOpen(false);
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

  const totalVisualItems = charts.length + matplotlibPlots.length;
  const currentGlobalOption = CHART_TYPE_OPTIONS.find((opt) => opt.id === globalType) || CHART_TYPE_OPTIONS[0];
  const CurrentGlobalIcon = currentGlobalOption.icon;

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
                Data Visualizations & Statistical Plots
              </h2>
              <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
                {totalVisualItems} {totalVisualItems === 1 ? 'Plot' : 'Plots'} Available
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Interactive distribution diagrams & Python Matplotlib scientific statistical plots
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
                <span>Hide Visualizations</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
                <span>Show Visualizations ({totalVisualItems})</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-5 space-y-6">
          {/* Top Section View Tabs & Dropdown Controls */}
          <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-100 text-xs">
            {/* View Mode Tabs */}
            <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg border border-slate-200">
              <button
                type="button"
                onClick={() => setActiveTab('all')}
                className={`px-3 py-1 rounded text-xs font-medium transition-all ${
                  activeTab === 'all'
                    ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                All Visuals ({totalVisualItems})
              </button>
              {charts.length > 0 && (
                <button
                  type="button"
                  onClick={() => setActiveTab('interactive')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${
                    activeTab === 'interactive'
                      ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <PieIcon className="w-3 h-3 text-blue-500" />
                  <span>Interactive Diagrams ({charts.length})</span>
                </button>
              )}
              {matplotlibPlots.length > 0 && (
                <button
                  type="button"
                  onClick={() => setActiveTab('matplotlib')}
                  className={`inline-flex items-center gap-1.5 px-3 py-1 rounded text-xs font-medium transition-all ${
                    activeTab === 'matplotlib'
                      ? 'bg-white text-slate-900 shadow-2xs font-semibold'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  <Binary className="w-3 h-3 text-indigo-500" />
                  <span>Matplotlib Plots ({matplotlibPlots.length})</span>
                </button>
              )}
            </div>

            {/* Dropdown Filters and Selectors */}
            <div className="flex items-center gap-2.5 flex-wrap">
              {/* Column Filter Dropdown */}
              {(activeTab === 'all' || activeTab === 'interactive') && charts.length > 1 && (
                <div className="relative" ref={columnDropdownRef}>
                  <button
                    type="button"
                    onClick={() => {
                      setIsColumnDropdownOpen(!isColumnDropdownOpen);
                      setIsGlobalTypeDropdownOpen(false);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs"
                  >
                    <Filter className="w-3.5 h-3.5 text-slate-400" />
                    <span>Column:</span>
                    <span className="font-semibold text-blue-600">
                      {selectedColumn === 'all' ? `All Columns (${charts.length})` : selectedColumn}
                    </span>
                    <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isColumnDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {/* Dropdown Menu */}
                  {isColumnDropdownOpen && (
                    <div className="absolute right-0 mt-1.5 w-52 bg-white border border-slate-200 rounded-lg shadow-lg z-30 py-1 text-xs">
                      <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                        Filter By Column
                      </div>
                      <button
                        type="button"
                        onClick={() => {
                          setSelectedColumn('all');
                          setIsColumnDropdownOpen(false);
                        }}
                        className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-slate-50 transition-colors ${
                          selectedColumn === 'all' ? 'bg-blue-50/50 text-blue-700 font-semibold' : 'text-slate-700'
                        }`}
                      >
                        <span>All Columns ({charts.length})</span>
                        {selectedColumn === 'all' && <Check className="w-3.5 h-3.5 text-blue-600" />}
                      </button>
                      {charts.map((c) => (
                        <button
                          key={c.id}
                          type="button"
                          onClick={() => {
                            setSelectedColumn(c.column_name);
                            setIsColumnDropdownOpen(false);
                          }}
                          className={`w-full text-left px-3 py-2 flex items-center justify-between hover:bg-slate-50 transition-colors ${
                            selectedColumn === c.column_name ? 'bg-blue-50/50 text-blue-700 font-semibold' : 'text-slate-700'
                          }`}
                        >
                          <span className="truncate">{c.column_name}</span>
                          {selectedColumn === c.column_name && <Check className="w-3.5 h-3.5 text-blue-600" />}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Chart View Dropdown Button */}
              {(activeTab === 'all' || activeTab === 'interactive') && charts.length > 0 && (
                <div className="relative" ref={globalTypeDropdownRef}>
                  <button
                    type="button"
                    onClick={() => {
                      setIsGlobalTypeDropdownOpen(!isGlobalTypeDropdownOpen);
                      setIsColumnDropdownOpen(false);
                    }}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-300 rounded-md text-xs font-medium text-slate-700 hover:bg-slate-50 hover:text-slate-900 transition-colors shadow-2xs"
                  >
                    <CurrentGlobalIcon className="w-3.5 h-3.5 text-blue-600" />
                    <span>Chart View:</span>
                    <span className="font-semibold text-slate-900 capitalize">{currentGlobalOption.label.split(' ')[0]}</span>
                    <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isGlobalTypeDropdownOpen ? 'rotate-180' : ''}`} />
                  </button>

                  {/* Dropdown Menu */}
                  {isGlobalTypeDropdownOpen && (
                    <div className="absolute right-0 mt-1.5 w-64 bg-white border border-slate-200 rounded-lg shadow-xl z-30 py-1 text-xs">
                      <div className="px-3 py-1.5 text-[11px] font-semibold text-slate-400 uppercase tracking-wider border-b border-slate-100">
                        Select Diagram View Style
                      </div>
                      {CHART_TYPE_OPTIONS.map((opt) => {
                        const Icon = opt.icon;
                        const isSelected = globalType === opt.id;
                        return (
                          <button
                            key={opt.id}
                            type="button"
                            onClick={() => handleGlobalTypeChange(opt.id)}
                            className={`w-full text-left px-3 py-2 flex items-start gap-2.5 hover:bg-slate-50 transition-colors ${
                              isSelected ? 'bg-blue-50/60 text-blue-900' : 'text-slate-700'
                            }`}
                          >
                            <div className={`p-1 rounded mt-0.5 ${isSelected ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'}`}>
                              <Icon className="w-3.5 h-3.5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center justify-between">
                                <span className={`font-medium ${isSelected ? 'font-bold text-blue-700' : 'text-slate-900'}`}>
                                  {opt.label}
                                </span>
                                {isSelected && <Check className="w-3.5 h-3.5 text-blue-600 ml-1" />}
                              </div>
                              <p className="text-[11px] text-slate-400 truncate">{opt.desc}</p>
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>


          {/* 1. Interactive SVG Charts Section */}
          {(activeTab === 'all' || activeTab === 'interactive') && charts.length > 0 && (
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
          )}

          {/* 2. Matplotlib Statistical & Cluster Plots Section */}
          {(activeTab === 'all' || activeTab === 'matplotlib') && matplotlibPlots.length > 0 && (
            <div className="space-y-4 pt-2">
              <div className="flex items-center justify-between pb-1 border-b border-slate-100">
                <div className="flex items-center gap-2">
                  <Binary className="w-4 h-4 text-indigo-600" />
                  <h3 className="text-xs font-bold text-slate-900 tracking-tight">
                    Matplotlib Statistical & Cluster Plots
                  </h3>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200">
                    Scientific Python Engine
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {matplotlibPlots.map((plot) => (
                  <MatplotlibPlotCard
                    key={plot.id}
                    plot={plot}
                    onPreview={() => setPreviewPlot(plot)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Fullscreen Zoom Modal for Matplotlib Plots */}
      {previewPlot && (
        <div className="fixed inset-0 z-50 bg-slate-900/70 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl overflow-hidden border border-slate-200">
            <div className="px-5 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50">
              <div>
                <h3 className="text-sm font-bold text-slate-900">{previewPlot.title}</h3>
                <p className="text-xs text-slate-500">{previewPlot.description}</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={previewPlot.image_base64}
                  download={`${previewPlot.id}.png`}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 rounded-md transition-colors shadow-2xs"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download Plot</span>
                </a>
                <button
                  type="button"
                  onClick={() => setPreviewPlot(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>
            <div className="p-6 flex items-center justify-center bg-slate-100/50 overflow-auto">
              <img
                src={previewPlot.image_base64}
                alt={previewPlot.title}
                className="max-h-[70vh] object-contain rounded-lg border border-slate-200 bg-white shadow-sm"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Matplotlib Plot Card
interface MatplotlibPlotCardProps {
  plot: MatplotlibPlot;
  onPreview: () => void;
}

const MatplotlibPlotCard: React.FC<MatplotlibPlotCardProps> = ({ plot, onPreview }) => {
  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between hover:border-slate-300 transition-colors shadow-2xs group">
      <div>
        <div className="flex items-start justify-between gap-2 pb-2 mb-2 border-b border-slate-100">
          <div>
            <h4 className="text-xs font-bold text-slate-900">{plot.title}</h4>
            <p className="text-[11px] text-slate-500 line-clamp-1 mt-0.5">{plot.description}</p>
          </div>
          <span className="text-[10px] font-semibold uppercase px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-100 flex-shrink-0">
            {plot.plot_type}
          </span>
        </div>

        {/* Plot Image */}
        <div className="relative rounded-md overflow-hidden bg-slate-50 border border-slate-100 flex items-center justify-center my-2 cursor-pointer" onClick={onPreview}>
          <img
            src={plot.image_base64}
            alt={plot.title}
            className="w-full h-auto object-contain transition-transform group-hover:scale-[1.01]"
          />
          <div className="absolute inset-0 bg-slate-900/10 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-white/95 text-slate-800 text-xs font-semibold shadow-md backdrop-blur-xs">
              <Maximize2 className="w-3.5 h-3.5 text-blue-600" />
              <span>Click to Enlarge</span>
            </span>
          </div>
        </div>
      </div>

      {/* Footer Controls */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-100 text-xs">
        <div className="flex items-center gap-1 flex-wrap">
          {plot.columns_analyzed?.map((col, idx) => (
            <span key={idx} className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded font-mono">
              {col}
            </span>
          ))}
        </div>
        <a
          href={plot.image_base64}
          download={`${plot.id}.png`}
          className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 hover:text-blue-800 transition-colors p-1"
          title="Download high-resolution plot"
        >
          <Download className="w-3.5 h-3.5" />
          <span>Save PNG</span>
        </a>
      </div>
    </div>
  );
};

interface ChartCardProps {
  chart: DatasetChart;
  currentType: ChartDisplayType;
  onTypeChange: (type: ChartDisplayType) => void;
}

const ChartCard: React.FC<ChartCardProps> = ({ chart, currentType, onTypeChange }) => {
  const [isDropdownOpen, setIsDropdownOpen] = useState<boolean>(false);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const totalValue = chart.data.reduce((acc, curr) => acc + curr.value, 0);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsDropdownOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const typeOptions: { id: ChartDisplayType; label: string; icon: React.FC<{ className?: string }> }[] = [
    { id: 'donut', label: 'Donut Chart', icon: CircleDot },
    { id: 'pie', label: 'Pie Chart', icon: PieIcon },
    { id: 'bar', label: 'Horizontal Bar', icon: BarChart2 },
    { id: 'column', label: 'Vertical Column', icon: Columns },
  ];

  const currentOption = typeOptions.find((t) => t.id === currentType) || typeOptions[0];
  const CurrentIcon = currentOption.icon;

  return (
    <div className="border border-slate-200 rounded-lg p-4 bg-white flex flex-col justify-between hover:border-slate-300 transition-colors shadow-2xs">
      {/* Chart Header */}
      <div className="flex items-center justify-between gap-2 pb-3 mb-3 border-b border-slate-100">
        <div>
          <h3 className="text-xs font-bold text-slate-900">{chart.title}</h3>
          <span className="text-[10px] text-slate-400 font-mono">Column: {chart.column_name}</span>
        </div>

        {/* Diagram Dropdown Switcher */}
        <div className="relative" ref={dropdownRef}>
          <button
            type="button"
            onClick={() => setIsDropdownOpen(!isDropdownOpen)}
            className="inline-flex items-center gap-1.5 px-2 py-1 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-md text-[11px] font-semibold text-slate-700 transition-colors"
          >
            <CurrentIcon className="w-3 h-3 text-blue-600" />
            <span>{currentOption.label}</span>
            <ChevronDown className={`w-3 h-3 text-slate-400 transition-transform ${isDropdownOpen ? 'rotate-180' : ''}`} />
          </button>

          {isDropdownOpen && (
            <div className="absolute right-0 mt-1 w-44 bg-white border border-slate-200 rounded-lg shadow-lg z-20 py-1 text-xs">
              {typeOptions.map((opt) => {
                const Icon = opt.icon;
                const isSelected = currentType === opt.id;
                return (
                  <button
                    key={opt.id}
                    type="button"
                    onClick={() => {
                      onTypeChange(opt.id);
                      setIsDropdownOpen(false);
                    }}
                    className={`w-full text-left px-3 py-1.5 flex items-center justify-between hover:bg-slate-50 transition-colors ${
                      isSelected ? 'bg-blue-50/50 text-blue-700 font-semibold' : 'text-slate-700'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <Icon className="w-3 h-3 text-slate-500" />
                      <span>{opt.label}</span>
                    </div>
                    {isSelected && <Check className="w-3 h-3 text-blue-600" />}
                  </button>
                );
              })}
            </div>
          )}
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
