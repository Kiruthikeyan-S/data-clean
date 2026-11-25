import React, { useState, useEffect } from 'react';
import { 
  FileX2, 
  Trash2, 
  Binary, 
  AlertOctagon, 
  TrendingUp, 
  RefreshCw, 
  CheckCircle2, 
  ChevronLeft,
  ChevronRight, 
  Search, 
  X, 
  SlidersHorizontal, 
  Info, 
  Link2, 
  Filter, 
  BarChart3, 
  History 
} from 'lucide-react';
import { 
  QualityAuditReport, 
  QualityDimension, 
  CleansingReport
} from '../types';

interface DataQualityInspectorProps {
  audit?: QualityAuditReport;
  cleansingReport?: CleansingReport;
}

export const DataQualityInspector: React.FC<DataQualityInspectorProps> = ({ 
  audit: directAudit, 
  cleansingReport 
}) => {
  const audit = directAudit || cleansingReport?.quality_audit;
  const fundamentalsReport = cleansingReport?.fundamentals_report;
  const preProfile = cleansingReport?.pre_cleaning_profile;
  const postProfile = cleansingReport?.post_cleaning_profile;
  const provenanceLog = cleansingReport?.provenance_log || [];

  const [activeTab, setActiveTab] = useState<'profile' | 'dimensions' | 'provenance'>('dimensions');
  const [selectedDimensionId, setSelectedDimensionId] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [selectedColumnFilter, setSelectedColumnFilter] = useState<string | null>(null);
  const [profileViewMode, setProfileViewMode] = useState<'pre' | 'post' | 'comparison'>('comparison');
  const [provenanceFilter, setProvenanceFilter] = useState<string>('all');
  const [dimPage, setDimPage] = useState(1);
  const [provenancePage, setProvenancePage] = useState(1);
  const DIM_PAGE_SIZE = 15;
  const PROV_PAGE_SIZE = 15;

  useEffect(() => {
    setDimPage(1);
  }, [selectedDimensionId, searchFilter, selectedColumnFilter]);

  useEffect(() => {
    setProvenancePage(1);
  }, [provenanceFilter, searchFilter]);

  if (!audit && !fundamentalsReport && !preProfile) {
    return null;
  }

  const selectedDimension: QualityDimension | undefined = audit?.dimensions?.find(
    d => d.id === selectedDimensionId
  );

  const getDimensionIcon = (id: string, isSelected: boolean, isClean: boolean) => {
    const iconClass = `w-4 h-4 ${
      isClean ? 'text-emerald-700' : isSelected ? 'text-blue-600' : 'text-slate-500'
    }`;
    switch (id) {
      case 'missing_values':
        return <FileX2 className={iconClass} />;
      case 'duplicates':
        return <Trash2 className={iconClass} />;
      case 'wrong_data_types':
        return <Binary className={iconClass} />;
      case 'invalid_values':
        return <AlertOctagon className={iconClass} />;
      case 'outliers':
        return <TrendingUp className={iconClass} />;
      case 'format_differences':
        return <RefreshCw className={iconClass} />;
      case 'record_matching':
        return <Link2 className={iconClass} />;
      default:
        return <SlidersHorizontal className={iconClass} />;
    }
  };

  const getCountBadge = (dim: QualityDimension) => {
    const denom = dim.total_denominator || (dim.id === 'duplicates' || dim.id === 'record_matching' ? audit?.total_rows : audit?.total_cells);
    const ratioText = denom ? `${dim.count} / ${denom}` : `${dim.count} items`;

    if (dim.count > 0) {
      if (dim.id === 'record_matching') {
        const report = dim.record_matching || audit?.record_matching;
        const candCount = report ? report.merge_candidates_count : dim.count;
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-blue-100 text-blue-900 border border-blue-300 shadow-2xs">
            {candCount > 0 ? `${candCount} Candidates` : `${dim.count} / ${denom || audit?.total_rows || 0}`}
          </span>
        );
      }
      if (dim.id === 'duplicates' || dim.id === 'wrong_data_types' || dim.id === 'invalid_values') {
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs">
            {ratioText}
          </span>
        );
      }
      return (
        <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-blue-100 text-blue-900 border border-blue-300 shadow-2xs">
          {ratioText}
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1 shadow-2xs">
        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
        {ratioText}
      </span>
    );
  };

  // Filter items in selected dimension based on search and selected column filter
  const filteredItems = selectedDimension?.items?.filter(item => {
    if (selectedColumnFilter && item.column.toLowerCase() !== selectedColumnFilter.toLowerCase()) {
      return false;
    }
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      item.column.toLowerCase().includes(q) ||
      String(item.original_value || '').toLowerCase().includes(q) ||
      String(item.cleaned_value || '').toLowerCase().includes(q) ||
      item.issue_description.toLowerCase().includes(q) ||
      (item.row_index && String(item.row_index).includes(q))
    );
  }) || [];

  // Filter provenance items
  const filteredProvenance = provenanceLog.filter(item => {
    if (provenanceFilter !== 'all' && item.operation !== provenanceFilter) return false;
    if (!searchFilter.trim()) return true;
    const q = searchFilter.toLowerCase();
    return (
      item.column.toLowerCase().includes(q) ||
      String(item.original_value || '').toLowerCase().includes(q) ||
      String(item.cleaned_value || '').toLowerCase().includes(q) ||
      item.reason.toLowerCase().includes(q) ||
      String(item.provenance || '').toLowerCase().includes(q) ||
      String(item.row_index).includes(q)
    );
  });

  const totalDimPages = Math.ceil(filteredItems.length / DIM_PAGE_SIZE) || 1;
  const paginatedItems = filteredItems.slice((dimPage - 1) * DIM_PAGE_SIZE, dimPage * DIM_PAGE_SIZE);

  const totalProvPages = Math.ceil(filteredProvenance.length / PROV_PAGE_SIZE) || 1;
  const paginatedProvenance = filteredProvenance.slice((provenancePage - 1) * PROV_PAGE_SIZE, provenancePage * PROV_PAGE_SIZE);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Top Header & Sub-Navigation Ribbon */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col md:flex-row md:items-center justify-between gap-4 bg-white">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-5 h-5 text-blue-600" />
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Data Quality & Profiling Inspector</h3>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Complete verification of statistical profiles, quality dimensions, and data health.
          </p>
        </div>

        {/* View Switcher Tabs */}
        <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200/80 self-start md:self-auto flex-wrap">
          {audit && (
            <button
              onClick={() => setActiveTab('dimensions')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                activeTab === 'dimensions'
                  ? 'bg-white text-blue-700 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
              <span>Quality Dimensions</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700 font-bold">
                {audit.dimensions.length}
              </span>
            </button>
          )}

          {(preProfile || postProfile) && (
            <button
              onClick={() => setActiveTab('profile')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                activeTab === 'profile'
                  ? 'bg-white text-blue-700 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <BarChart3 className="w-3.5 h-3.5" />
              <span>Data Profiling</span>
            </button>
          )}

          {provenanceLog.length > 0 && (
            <button
              onClick={() => setActiveTab('provenance')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-bold transition-all ${
                activeTab === 'provenance'
                  ? 'bg-white text-blue-700 shadow-xs border border-slate-200'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Audit Provenance</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-slate-200 text-slate-700 font-bold">
                {provenanceLog.length}
              </span>
            </button>
          )}
        </div>
      </div>

      {/* ─────────────────────────────────────────────────────────────
          TAB 1: DATA PROFILING (PRE VS POST STATISTICS)
         ───────────────────────────────────────────────────────────── */}
      {activeTab === 'profile' && (preProfile || postProfile) && (
        <div className="p-5 sm:p-6 space-y-5">
          {/* View Mode Toggle & Mode Indicator Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-slate-200">
            <div>
              <div className="flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-blue-600" />
                <h4 className="text-sm font-bold text-slate-900">
                  {profileViewMode === 'comparison' && 'Side-by-Side Comparison (Before vs After Cleaning)'}
                  {profileViewMode === 'pre' && 'Pre-Cleaning Profile (Raw Untouched Data)'}
                  {profileViewMode === 'post' && 'Post-Cleaning Profile (Clean Normalized Data)'}
                </h4>
                <span className={`px-2 py-0.5 rounded text-[11px] font-bold uppercase tracking-wider ${
                  profileViewMode === 'pre'
                    ? 'bg-amber-100 text-amber-800 border border-amber-300'
                    : profileViewMode === 'post'
                    ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                    : 'bg-blue-100 text-blue-800 border border-blue-300'
                }`}>
                  {profileViewMode === 'pre' ? 'Raw / Before' : profileViewMode === 'post' ? 'Clean / After' : 'Comparison'}
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                {profileViewMode === 'pre' && 'Displaying metrics for the raw dataset before any deduplication or formatting.'}
                {profileViewMode === 'post' && 'Displaying metrics for the final sanitized, deduplicated, and validated dataset.'}
                {profileViewMode === 'comparison' && 'Displaying side-by-side verification comparing baseline raw values against clean outputs.'}
              </p>
            </div>

            {/* View Mode Toggle Buttons */}
            <div className="flex items-center gap-1.5 p-1 bg-slate-100 rounded-lg border border-slate-200 self-start sm:self-auto text-xs font-semibold">
              <button
                type="button"
                onClick={() => setProfileViewMode('comparison')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                  profileViewMode === 'comparison'
                    ? 'bg-blue-600 text-white shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <span>Side-by-Side</span>
              </button>
              <button
                type="button"
                onClick={() => setProfileViewMode('pre')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                  profileViewMode === 'pre'
                    ? 'bg-amber-600 text-white shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <span>Pre-Cleaning (Before)</span>
              </button>
              <button
                type="button"
                onClick={() => setProfileViewMode('post')}
                className={`px-3 py-1.5 rounded-md transition-all flex items-center gap-1.5 ${
                  profileViewMode === 'post'
                    ? 'bg-emerald-600 text-white shadow-xs font-bold'
                    : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
                }`}
              >
                <span>Post-Cleaning (After)</span>
              </button>
            </div>
          </div>

          {/* Quick Stats Ribbon */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">Total Rows Profiled</span>
              <div className="text-xl font-bold text-slate-900 mt-0.5 flex items-center gap-2">
                <span>
                  {profileViewMode === 'pre'
                    ? (preProfile?.total_rows ?? 0)
                    : profileViewMode === 'post'
                    ? (postProfile?.total_rows ?? 0)
                    : (preProfile?.total_rows || postProfile?.total_rows || 0)}
                </span>
                {profileViewMode === 'comparison' && preProfile && postProfile && preProfile.total_rows !== postProfile.total_rows && (
                  <span className="text-xs font-normal text-emerald-700 bg-emerald-100 px-1.5 py-0.2 rounded">
                    → {postProfile.total_rows}
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">Total Columns</span>
              <div className="text-xl font-bold text-slate-900 mt-0.5">
                {profileViewMode === 'pre'
                  ? (preProfile?.total_columns ?? 0)
                  : profileViewMode === 'post'
                  ? (postProfile?.total_columns ?? 0)
                  : (postProfile?.total_columns || preProfile?.total_columns || 0)}
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">Duplicates (Exact / Approx)</span>
              <div className="text-xl font-bold text-slate-900 mt-0.5 flex items-center gap-1.5">
                <span className="text-amber-700">
                  {profileViewMode === 'post'
                    ? (postProfile?.exact_duplicates_count ?? 0)
                    : (preProfile?.exact_duplicates_count ?? 0)}
                </span>
                <span className="text-slate-400 font-normal text-xs">/</span>
                <span className="text-blue-700">
                  {profileViewMode === 'post'
                    ? (postProfile?.approximate_duplicates_count ?? 0)
                    : (preProfile?.approximate_duplicates_count ?? 0)}
                </span>
              </div>
            </div>

            <div className="bg-slate-50 rounded-xl p-3 border border-slate-200">
              <span className="text-[11px] font-semibold text-slate-500 block">Completeness Score</span>
              <div className="text-xl font-bold text-emerald-700 mt-0.5">
                {profileViewMode === 'pre'
                  ? (preProfile?.overall_completeness_percentage ?? 100)
                  : (postProfile?.overall_completeness_percentage ?? preProfile?.overall_completeness_percentage ?? 100)}%
              </div>
            </div>
          </div>

          {/* Profile Columns Table */}
          <div className="border border-slate-200 rounded-xl overflow-x-auto shadow-2xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-100/90 text-slate-700 border-b border-slate-200 font-semibold">
                  <th className="px-4 py-3">Column Name</th>
                  <th className="px-4 py-3">Detected Type</th>
                  <th className="px-4 py-3">Missing (Null %)</th>
                  <th className="px-4 py-3">Unique Values</th>
                  <th className="px-4 py-3">Min / Max</th>
                  <th className="px-4 py-3">Quartiles (Q1, Q2, Q3)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {Object.entries(
                  (profileViewMode === 'pre'
                    ? preProfile?.column_stats
                    : profileViewMode === 'post'
                    ? (postProfile?.column_stats || preProfile?.column_stats)
                    : (postProfile?.column_stats || preProfile?.column_stats)) || {}
                ).map(([colName, colStat]) => {
                  const preStat = preProfile?.column_stats?.[colName];
                  const postStat = postProfile?.column_stats?.[colName];

                  return (
                    <tr key={colName} className="hover:bg-slate-50/80 transition-colors">
                      <td className="px-4 py-2.5 font-bold text-slate-900 font-mono">
                        {colName}
                      </td>
                      <td className="px-4 py-2.5">
                        <span className={`px-2 py-0.5 rounded-full text-[11px] font-semibold border ${
                          profileViewMode === 'pre'
                            ? 'bg-amber-50 text-amber-800 border-amber-200'
                            : profileViewMode === 'post'
                            ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                            : 'bg-blue-50 text-blue-800 border-blue-200'
                        }`}>
                          {colStat.inferred_type}
                        </span>
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="flex items-center gap-1.5">
                          <span className={`font-semibold ${colStat.null_count > 0 ? 'text-amber-700' : 'text-emerald-700'}`}>
                            {colStat.null_count} ({colStat.null_percentage}%)
                          </span>
                          {profileViewMode === 'comparison' && preStat && postStat && preStat.null_count !== postStat.null_count && (
                            <span className="text-[10px] text-slate-400">
                              (was {preStat.null_count})
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="px-4 py-2.5 text-slate-700">
                        {colStat.unique_count} distinct
                        {profileViewMode === 'comparison' && preStat && postStat && preStat.unique_count !== postStat.unique_count && (
                          <span className="text-[10px] text-slate-400 ml-1">
                            (was {preStat.unique_count})
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-slate-700 font-mono text-[11px]">
                        {colStat.min_value != null && colStat.max_value != null ? (
                          `${colStat.min_value} → ${colStat.max_value}`
                        ) : (
                          <span className="text-slate-400 italic">—</span>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-slate-700 font-mono text-[11px]">
                        {colStat.quartiles && colStat.quartiles.length === 3 ? (
                          `[${colStat.quartiles[0]}, ${colStat.quartiles[1]}, ${colStat.quartiles[2]}]`
                        ) : (
                          <span className="text-slate-400 italic">—</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 3: QUALITY DIMENSIONS & DIAGNOSTIC DRILLDOWN
         ───────────────────────────────────────────────────────────── */}
      {activeTab === 'dimensions' && audit && (
        <>
          {/* 7 Clickable Quality Dimensions Grid */}
          <div className="p-4 sm:p-5 bg-slate-50/60 border-b border-slate-200/80">
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2 sm:gap-2.5">
              {audit.dimensions.map(dim => {
                const isSelected = selectedDimensionId === dim.id;
                const isClean = dim.count === 0;

                let cardBgClass = '';
                if (isSelected) {
                  cardBgClass = isClean
                    ? 'bg-emerald-100/90 border-emerald-500 ring-2 ring-emerald-500/20 shadow-xs'
                    : 'bg-blue-50/90 border-blue-500 ring-2 ring-blue-500/20 shadow-xs';
                } else if (isClean) {
                  cardBgClass = 'bg-emerald-50/70 border-emerald-200 hover:bg-emerald-100/60 hover:border-emerald-300 shadow-2xs';
                } else {
                  cardBgClass = 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-2xs';
                }

                return (
                  <button
                    key={dim.id}
                    type="button"
                    onClick={() => {
                      if (selectedDimensionId === dim.id) {
                        setSelectedDimensionId(null);
                        setSelectedColumnFilter(null);
                      } else {
                        setSelectedDimensionId(dim.id);
                        setSelectedColumnFilter(null);
                        setSearchFilter('');
                      }
                    }}
                    className={`p-3 rounded-xl text-left transition-all relative border flex flex-col justify-between ${cardBgClass}`}
                  >
                    <div>
                      <div className="flex items-center justify-between mb-2">
                        <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                          isClean
                            ? 'bg-emerald-100 border-emerald-300'
                            : isSelected
                            ? 'bg-white border-blue-200'
                            : 'bg-slate-50 border-slate-200'
                        }`}>
                          {getDimensionIcon(dim.id, isSelected, isClean)}
                        </div>
                        {isSelected && (
                          <span className={`w-2 h-2 rounded-full ${isClean ? 'bg-emerald-600' : 'bg-blue-600'} animate-pulse`} />
                        )}
                      </div>
                      <div className={`text-xs font-bold leading-snug ${isClean ? 'text-emerald-950' : 'text-slate-900'}`}>
                        {dim.title}
                      </div>
                    </div>

                    <div className={`mt-2.5 pt-2 border-t flex items-center justify-between ${
                      isClean ? 'border-emerald-200/70' : 'border-slate-100'
                    }`}>
                      {getCountBadge(dim)}
                      <ChevronRight className={`w-3.5 h-3.5 transition-transform ${
                        isSelected
                          ? isClean ? 'rotate-90 text-emerald-700' : 'rotate-90 text-blue-600'
                          : isClean ? 'text-emerald-600' : 'text-slate-400'
                      }`} />
                    </div>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Selected Dimension Detail Inspector Panel */}
          {selectedDimension && (
            <div className="p-5 sm:p-6 bg-white animate-in fade-in duration-200">
              {/* Header of selected dimension */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-slate-200">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-bold text-slate-900">{selectedDimension.title} Details</span>
                    {getCountBadge(selectedDimension)}
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed max-w-2xl">
                    {selectedDimension.summary}
                  </p>
                </div>

                {/* Filters */}
                {selectedDimension.items && selectedDimension.items.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2">
                    {/* Search box */}
                    <div className="relative">
                      <Search className="w-3.5 h-3.5 absolute left-2.5 top-2.5 text-slate-400" />
                      <input
                        type="text"
                        placeholder="Search diagnostics..."
                        value={searchFilter}
                        onChange={e => setSearchFilter(e.target.value)}
                        className="pl-8 pr-7 py-1.5 text-xs bg-slate-50 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 w-44 sm:w-56 text-slate-800"
                      />
                      {searchFilter && (
                        <button
                          type="button"
                          onClick={() => setSearchFilter('')}
                          className="absolute right-2 top-2 text-slate-400 hover:text-slate-600"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      )}
                    </div>

                    {/* Column dropdown filter */}
                    {selectedDimension.affected_columns && selectedDimension.affected_columns.length > 1 && (
                      <div className="flex items-center gap-1.5 text-xs">
                        <Filter className="w-3.5 h-3.5 text-slate-400" />
                        <select
                          value={selectedColumnFilter || ''}
                          onChange={e => setSelectedColumnFilter(e.target.value || null)}
                          className="py-1.5 px-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium text-slate-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        >
                          <option value="">All Columns ({selectedDimension.affected_columns.length})</option>
                          {selectedDimension.affected_columns.map(col => (
                            <option key={col} value={col}>{col}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Items Table */}
              {selectedDimension.items && selectedDimension.items.length > 0 ? (
                <div className="mt-4 border border-slate-200 rounded-lg overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                        <th className="px-4 py-2.5 w-20">Row</th>
                        <th className="px-4 py-2.5 w-36">Column</th>
                        <th className="px-4 py-2.5">Original Value</th>
                        <th className="px-4 py-2.5">Standardized Treatment</th>
                        <th className="px-4 py-2.5">Diagnosis / Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 bg-white">
                      {filteredItems.length === 0 ? (
                        <tr>
                          <td colSpan={5} className="px-4 py-8 text-center text-slate-400 text-xs">
                            No diagnostic items matched your current filter
                          </td>
                        </tr>
                      ) : (
                        paginatedItems.map((item, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                            <td className="px-4 py-2.5 text-slate-500 font-mono text-[11px]">
                              {item.row_index !== undefined ? `#${item.row_index}` : '—'}
                            </td>
                            <td className="px-4 py-2.5 font-semibold text-slate-800 font-mono text-[11px]">
                              {item.column}
                            </td>
                            <td className="px-4 py-2.5 text-slate-600 font-mono">
                              {item.original_value === null || item.original_value === undefined ? (
                                <span className="text-slate-300 italic text-[11px]">empty / null</span>
                              ) : (
                                <span className="bg-red-50 text-red-700 px-1.5 py-0.5 rounded border border-red-100 text-[11px]">
                                  {String(item.original_value)}
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-2.5 font-mono">
                              {item.cleaned_value === null || item.cleaned_value === undefined ? (
                                <span className="text-slate-400 italic text-[11px]">null (standardized)</span>
                              ) : (
                                <span className="bg-emerald-50 text-emerald-800 px-1.5 py-0.5 rounded border border-emerald-100 font-semibold text-[11px]">
                                  {String(item.cleaned_value)}
                                </span>
                              )}
                            </td>
                            <td className="px-4 py-2.5 text-slate-800 font-medium">
                              <span className="text-slate-600 text-xs">{item.issue_description}</span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>

                  {/* Pagination Bar for Diagnostic Items */}
                  {filteredItems.length > DIM_PAGE_SIZE && (
                    <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
                      <span>
                        Showing <strong className="font-semibold text-slate-800">{(dimPage - 1) * DIM_PAGE_SIZE + 1}</strong> to{' '}
                        <strong className="font-semibold text-slate-800">
                          {Math.min(dimPage * DIM_PAGE_SIZE, filteredItems.length)}
                        </strong>{' '}
                        of <strong className="font-semibold text-slate-800">{filteredItems.length}</strong> issues
                      </span>
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => setDimPage(p => Math.max(p - 1, 1))}
                          disabled={dimPage <= 1}
                          className="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium"
                        >
                          <ChevronLeft className="w-3.5 h-3.5" />
                          <span>Prev</span>
                        </button>
                        <span className="px-2 py-1 font-semibold text-slate-700">
                          {dimPage} / {totalDimPages}
                        </span>
                        <button
                          type="button"
                          onClick={() => setDimPage(p => Math.min(p + 1, totalDimPages))}
                          disabled={dimPage >= totalDimPages}
                          className="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium"
                        >
                          <span>Next</span>
                          <ChevronRight className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ) : selectedDimension.count > 0 ? (
                <div className="py-6 px-4 bg-blue-50/40 rounded-lg border border-blue-100 mt-3 text-center">
                  <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mx-auto mb-2">
                    <Info className="w-4 h-4" />
                  </div>
                  <p className="text-xs font-bold text-blue-900">{selectedDimension.count} {selectedDimension.title} Processed</p>
                  <p className="text-xs text-slate-600 mt-1 max-w-lg mx-auto">{selectedDimension.summary}</p>
                </div>
              ) : (
                <div className="py-8 text-center bg-slate-50/50 rounded-lg border border-dashed border-slate-200 mt-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto mb-2 border border-emerald-100">
                    <CheckCircle2 className="w-4 h-4" />
                  </div>
                  <p className="text-xs font-semibold text-slate-800">No {selectedDimension.title} Issues Detected</p>
                  <p className="text-[11px] text-slate-500 mt-0.5">Your dataset is completely clean in this dimension.</p>
                </div>
              )}
            </div>
          )}
        </>
      )}

      {/* ─────────────────────────────────────────────────────────────
          TAB 4: CHANGE PROVENANCE AUDIT TRAIL
         ───────────────────────────────────────────────────────────── */}
      {activeTab === 'provenance' && provenanceLog.length > 0 && (
        <div className="p-5 sm:p-6 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-200">
            <div>
              <h4 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <History className="w-4 h-4 text-blue-600" />
                <span>Element-Level Change Provenance Log</span>
              </h4>
              <p className="text-xs text-slate-500 mt-0.5">
                Every value modification is recorded with original source data, resulting value, and audit rule provenance.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <select
                value={provenanceFilter}
                onChange={e => setProvenanceFilter(e.target.value)}
                className="py-1 px-2.5 bg-slate-50 border border-slate-300 rounded-lg text-xs font-medium text-slate-700"
              >
                <option value="all">All Operations ({provenanceLog.length})</option>
                <option value="whitespace_trimmed">Whitespace Trimmed</option>
                <option value="missing_normalization">Missing Value Normalized</option>
                <option value="type_correction">Type Corrected</option>
                <option value="format_standardization">Format Standardized</option>
              </select>
            </div>
          </div>

          <div className="border border-slate-200 rounded-lg overflow-x-auto shadow-2xs">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="bg-slate-50 text-slate-700 border-b border-slate-200 font-semibold">
                  <th className="px-4 py-2.5 w-16">Row</th>
                  <th className="px-4 py-2.5 w-32">Column</th>
                  <th className="px-4 py-2.5">Original Value</th>
                  <th className="px-4 py-2.5">Cleaned Value</th>
                  <th className="px-4 py-2.5">Operation</th>
                  <th className="px-4 py-2.5">Rule / Provenance</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 bg-white">
                {paginatedProvenance.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/80 transition-colors">
                    <td className="px-4 py-2 font-mono text-[11px] text-slate-500">
                      #{item.row_index}
                    </td>
                    <td className="px-4 py-2 font-mono text-[11px] font-semibold text-slate-800">
                      {item.column}
                    </td>
                    <td className="px-4 py-2 font-mono text-[11px]">
                      {item.original_value === null ? (
                        <span className="text-slate-300 italic">null</span>
                      ) : (
                        <span className="bg-red-50 text-red-700 px-1 py-0.5 rounded border border-red-100">
                          {String(item.original_value)}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2 font-mono text-[11px]">
                      {item.cleaned_value === null ? (
                        <span className="text-slate-400 italic">null</span>
                      ) : (
                        <span className="bg-emerald-50 text-emerald-800 px-1 py-0.5 rounded border border-emerald-100 font-semibold">
                          {String(item.cleaned_value)}
                        </span>
                      )}
                    </td>
                    <td className="px-4 py-2">
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200">
                        {item.operation.replace(/_/g, ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-2 text-slate-600 text-[11px]">
                      {item.provenance || item.reason}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            {/* Pagination Bar for Provenance Log */}
            {filteredProvenance.length > PROV_PAGE_SIZE && (
              <div className="flex items-center justify-between px-4 py-2.5 bg-slate-50 border-t border-slate-200 text-xs text-slate-600">
                <span>
                  Showing <strong className="font-semibold text-slate-800">{(provenancePage - 1) * PROV_PAGE_SIZE + 1}</strong> to{' '}
                  <strong className="font-semibold text-slate-800">
                    {Math.min(provenancePage * PROV_PAGE_SIZE, filteredProvenance.length)}
                  </strong>{' '}
                  of <strong className="font-semibold text-slate-800">{filteredProvenance.length}</strong> log entries
                </span>
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setProvenancePage(p => Math.max(p - 1, 1))}
                    disabled={provenancePage <= 1}
                    className="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium"
                  >
                    <ChevronLeft className="w-3.5 h-3.5" />
                    <span>Prev</span>
                  </button>
                  <span className="px-2 py-1 font-semibold text-slate-700">
                    {provenancePage} / {totalProvPages}
                  </span>
                  <button
                    type="button"
                    onClick={() => setProvenancePage(p => Math.min(p + 1, totalProvPages))}
                    disabled={provenancePage >= totalProvPages}
                    className="px-2 py-1 rounded border border-slate-300 bg-white hover:bg-slate-100 disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1 font-medium"
                  >
                    <span>Next</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
