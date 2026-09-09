import React, { useState } from 'react';
import { 
  FileX2, 
  Trash2, 
  Binary, 
  AlertOctagon, 
  TrendingUp, 
  RefreshCw, 
  CheckCircle2, 
  ChevronRight, 
  Search,
  X,
  SlidersHorizontal,
  Info
} from 'lucide-react';
import { QualityAuditReport, QualityDimension } from '../types';

interface DataQualityInspectorProps {
  audit?: QualityAuditReport;
}

export const DataQualityInspector: React.FC<DataQualityInspectorProps> = ({ audit }) => {
  const [selectedDimensionId, setSelectedDimensionId] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');

  if (!audit || !audit.dimensions || audit.dimensions.length === 0) {
    return null;
  }

  const selectedDimension: QualityDimension | undefined = audit.dimensions.find(
    d => d.id === selectedDimensionId
  );

  const getDimensionIcon = (id: string, isSelected: boolean) => {
    const iconClass = `w-4 h-4 ${isSelected ? 'text-blue-600' : 'text-slate-500'}`;
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
      default:
        return <SlidersHorizontal className={iconClass} />;
    }
  };

  const getCountBadge = (dim: QualityDimension) => {
    if (dim.count > 0) {
      if (dim.id === 'duplicates' || dim.id === 'wrong_data_types' || dim.id === 'invalid_values') {
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-amber-100 text-amber-800 border border-amber-200">
            {dim.count} found
          </span>
        );
      }
      return (
        <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-blue-100 text-blue-800 border border-blue-200">
          {dim.count} items
        </span>
      );
    }
    return (
      <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center gap-1">
        <CheckCircle2 className="w-3 h-3" />
        0 Clean
      </span>
    );
  };

  // Filter items in selected dimension based on search
  const filteredItems = selectedDimension?.items.filter(item => {
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

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Title Header */}
      <div className="p-4 sm:p-5 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <SlidersHorizontal className="w-4 h-4 text-blue-600" />
            <h3 className="text-base font-bold text-slate-900 tracking-tight">Data Quality Audit & Diagnostics</h3>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            Click any quality dimension to inspect affected rows, original values, and exact treatments applied
          </p>
        </div>

        <div className="text-xs font-semibold px-2.5 py-1 bg-slate-100 text-slate-700 rounded-md border border-slate-200 self-start sm:self-auto">
          {audit.total_issues_handled} Data Quality Diagnostics Recorded
        </div>
      </div>

      {/* 6 Clickable Quality Dimensions Grid */}
      <div className="p-4 sm:p-5 bg-slate-50/60 border-b border-slate-200/80">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5 sm:gap-3">
          {audit.dimensions.map(dim => {
            const isSelected = selectedDimensionId === dim.id;

            return (
              <button
                key={dim.id}
                type="button"
                onClick={() => {
                  if (selectedDimensionId === dim.id) {
                    setSelectedDimensionId(null);
                  } else {
                    setSelectedDimensionId(dim.id);
                    setSearchFilter('');
                  }
                }}
                className={`p-3 rounded-xl text-left transition-all relative border flex flex-col justify-between ${
                  isSelected
                    ? 'bg-blue-50/90 border-blue-500 ring-2 ring-blue-500/20 shadow-xs'
                    : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-2xs'
                }`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className={`w-7 h-7 rounded-lg flex items-center justify-center border ${
                      isSelected ? 'bg-white border-blue-200' : 'bg-slate-50 border-slate-200'
                    }`}>
                      {getDimensionIcon(dim.id, isSelected)}
                    </div>
                    {isSelected && (
                      <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
                    )}
                  </div>
                  <div className="text-xs font-bold text-slate-900 leading-snug">
                    {dim.title}
                  </div>
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-100 flex items-center justify-between">
                  {getCountBadge(dim)}
                  <ChevronRight className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isSelected ? 'rotate-90 text-blue-600' : ''}`} />
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

            <div className="flex items-center gap-3">
              {/* Search box within dimension */}
              {selectedDimension.items.length > 0 && (
                <div className="relative min-w-[200px]">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    placeholder="Search issues in this tab..."
                    value={searchFilter}
                    onChange={e => setSearchFilter(e.target.value)}
                    className="w-full pl-8 pr-3 py-1 text-xs bg-slate-50 border border-slate-200 rounded-md focus:outline-none focus:ring-1 focus:ring-blue-500 focus:bg-white text-slate-800 placeholder-slate-400"
                  />
                </div>
              )}

              <button
                type="button"
                onClick={() => setSelectedDimensionId(null)}
                className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-md transition-colors"
                title="Close detail view"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* Affected Columns Badges if applicable */}
          {selectedDimension.affected_columns && selectedDimension.affected_columns.length > 0 && (
            <div className="py-3 flex flex-wrap items-center gap-1.5 text-xs border-b border-slate-100">
              <span className="font-semibold text-slate-500 mr-1">Affected Columns ({selectedDimension.affected_columns.length}):</span>
              {selectedDimension.affected_columns.map(col => (
                <span key={col} className="px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-mono text-[11px] border border-slate-200">
                  {col}
                </span>
              ))}
            </div>
          )}

          {/* Special Duplicate Full Records Table if Duplicates Tab with raw samples */}
          {selectedDimension.id === 'duplicates' && selectedDimension.raw_samples && selectedDimension.raw_samples.length > 0 && (
            <div className="mt-4 mb-4">
              <div className="text-xs font-semibold text-amber-900 mb-2 flex items-center gap-1.5">
                <Trash2 className="w-3.5 h-3.5 text-amber-700" />
                <span>Sample Full Duplicate Rows Removed from Output:</span>
              </div>
              <div className="overflow-x-auto border border-amber-200 rounded-lg bg-amber-50/30">
                <table className="w-full text-left text-xs">
                  <thead className="bg-amber-100/60 font-semibold text-amber-900 border-b border-amber-200 text-[11px]">
                    <tr>
                      <th className="px-3 py-2 w-10 text-center">#</th>
                      {Object.keys(selectedDimension.raw_samples[0]).map(k => (
                        <th key={k} className="px-3 py-2 whitespace-nowrap">{k}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-amber-100 font-mono text-[11px] text-slate-800">
                    {selectedDimension.raw_samples.map((row, idx) => (
                      <tr key={idx} className="hover:bg-amber-50">
                        <td className="px-3 py-2 text-center text-slate-400 font-sans">{idx + 1}</td>
                        {Object.values(row).map((v, cidx) => (
                          <td key={cidx} className="px-3 py-2 whitespace-nowrap">
                            {v === null ? <span className="text-slate-300 italic">null</span> : String(v)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Detailed Itemized Rows Table */}
          {selectedDimension.items.length > 0 ? (
            <div className="mt-4 overflow-x-auto rounded-lg border border-slate-200">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 font-semibold text-slate-700 border-b border-slate-200 uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="px-4 py-2.5 w-16 text-center">Row</th>
                    <th className="px-4 py-2.5 w-1/5">Column / Field</th>
                    <th className="px-4 py-2.5 w-1/4">Original Value</th>
                    <th className="px-4 py-2.5 w-1/4">Cleaned / Fixed Value</th>
                    <th className="px-4 py-2.5">Diagnosis & Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {filteredItems.length === 0 ? (
                    <tr>
                      <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                        No items match your search in this category.
                      </td>
                    </tr>
                  ) : (
                    filteredItems.map((item, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-4 py-2.5 text-center font-mono text-slate-400">
                          {item.row_index !== undefined ? `#${item.row_index}` : '—'}
                        </td>
                        <td className="px-4 py-2.5 font-semibold text-slate-900">
                          <span className="font-mono bg-slate-100 px-1.5 py-0.5 rounded text-[11px] text-slate-800 border border-slate-200/60">
                            {item.column}
                          </span>
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
                        <td className="px-4 py-2.5 text-slate-600 font-medium">
                          {item.issue_description}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
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

          {/* Footer of Detail view */}
          {selectedDimension.items.length > 0 && (
            <div className="mt-3 flex items-center justify-between text-[11px] text-slate-500">
              <span className="flex items-center gap-1">
                <Info className="w-3.5 h-3.5 text-slate-400" />
                Showing {filteredItems.length} of {selectedDimension.items.length} diagnostic items
              </span>
              <button
                type="button"
                onClick={() => setSelectedDimensionId(null)}
                className="font-semibold text-blue-600 hover:underline"
              >
                Close detail view
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
