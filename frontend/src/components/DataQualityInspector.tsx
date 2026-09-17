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
  Info,
  Link2,
  GitMerge,
  Sparkles,
  Check
} from 'lucide-react';
import { QualityAuditReport, QualityDimension } from '../types';

interface DataQualityInspectorProps {
  audit?: QualityAuditReport;
}

export const DataQualityInspector: React.FC<DataQualityInspectorProps> = ({ audit }) => {
  const [selectedDimensionId, setSelectedDimensionId] = useState<string | null>(null);
  const [searchFilter, setSearchFilter] = useState('');
  const [matchingSubTab, setMatchingSubTab] = useState<'candidates' | 'merged'>('candidates');
  const [candidateActions, setCandidateActions] = useState<Record<string, 'merged' | 'separate' | 'review'>>({});

  if (!audit || !audit.dimensions || audit.dimensions.length === 0) {
    return null;
  }

  const selectedDimension: QualityDimension | undefined = audit.dimensions.find(
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
    const denom = dim.total_denominator || (dim.id === 'duplicates' || dim.id === 'record_matching' ? audit.total_rows : audit.total_cells);
    const ratioText = denom ? `${dim.count} / ${denom}` : `${dim.count} items`;

    if (dim.count > 0) {
      if (dim.id === 'record_matching') {
        const report = dim.record_matching || audit.record_matching;
        const candCount = report ? report.merge_candidates_count : dim.count;
        return (
          <span className="px-2 py-0.5 text-[11px] font-semibold rounded-full bg-blue-100 text-blue-900 border border-blue-300 shadow-2xs">
            {candCount > 0 ? `${candCount} Candidates` : `${dim.count} / ${denom || audit.total_rows || 0}`}
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

  const recordMatchingReport = selectedDimension?.record_matching || audit.record_matching;

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
                  } else {
                    setSelectedDimensionId(dim.id);
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

            <div className="flex items-center gap-3">
              {/* Search box within dimension */}
              {selectedDimension.id !== 'record_matching' && selectedDimension.items.length > 0 && (
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

          {/* ========================================================================= */}
          {/* SPECIAL RECORD MATCHING 3-SECTION INTERACTIVE INSPECTOR */}
          {/* ========================================================================= */}
          {selectedDimension.id === 'record_matching' && recordMatchingReport ? (
            <div className="mt-4 space-y-5">
              {/* Record Matching Summary Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5 p-3.5 bg-slate-50/80 rounded-xl border border-slate-200">
                <div className="bg-white p-2.5 rounded-lg border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] text-slate-500 font-medium">Total Records</div>
                  <div className="text-base font-bold text-slate-900 font-mono mt-0.5">{recordMatchingReport.total_records}</div>
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-blue-200 shadow-2xs">
                  <div className="text-[11px] text-blue-600 font-medium">Merge Candidates</div>
                  <div className="text-base font-bold text-blue-700 font-mono mt-0.5">{recordMatchingReport.merge_candidates_count}</div>
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-emerald-200 shadow-2xs">
                  <div className="text-[11px] text-emerald-600 font-medium">Successfully Merged</div>
                  <div className="text-base font-bold text-emerald-700 font-mono mt-0.5">{recordMatchingReport.merged_count}</div>
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-slate-200/80 shadow-2xs">
                  <div className="text-[11px] text-slate-500 font-medium">Kept Separate</div>
                  <div className="text-base font-bold text-slate-700 font-mono mt-0.5">{recordMatchingReport.kept_separate_count}</div>
                </div>
                <div className="bg-white p-2.5 rounded-lg border border-indigo-200 shadow-2xs">
                  <div className="text-[11px] text-indigo-600 font-medium">Final Records</div>
                  <div className="text-base font-bold text-indigo-700 font-mono mt-0.5">{recordMatchingReport.final_records_count}</div>
                </div>
              </div>

              {/* Sub-Tabs: Merge Candidates & Merged Records */}
              <div className="flex items-center gap-2 border-b border-slate-200 pb-2">
                <button
                  type="button"
                  onClick={() => setMatchingSubTab('candidates')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    matchingSubTab === 'candidates'
                      ? 'bg-blue-600 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>1. Merge Candidates</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                    matchingSubTab === 'candidates' ? 'bg-blue-700 text-blue-100' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {recordMatchingReport.candidate_pairs.length}
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setMatchingSubTab('merged')}
                  className={`px-3.5 py-1.5 rounded-lg text-xs font-semibold transition-all flex items-center gap-1.5 ${
                    matchingSubTab === 'merged'
                      ? 'bg-emerald-600 text-white shadow-2xs'
                      : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                  }`}
                >
                  <span>2. Merged Records</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono font-bold ${
                    matchingSubTab === 'merged' ? 'bg-emerald-700 text-emerald-100' : 'bg-slate-200 text-slate-700'
                  }`}>
                    {recordMatchingReport.merged_records.length}
                  </span>
                </button>
              </div>

              {/* SECTION 1: MERGE CANDIDATES */}
              {matchingSubTab === 'candidates' && (
                <div className="space-y-4">
                  {recordMatchingReport.candidate_pairs.length === 0 ? (
                    <div className="py-8 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                      <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-slate-700">No Merge Candidates Found</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">All records in your dataset have unique, non-overlapping identity attributes.</p>
                    </div>
                  ) : (
                    recordMatchingReport.candidate_pairs.map((candidate, cIdx) => {
                      const action = candidateActions[candidate.candidate_id];
                      const allKeys = Array.from(new Set([...Object.keys(candidate.record_a), ...Object.keys(candidate.record_b)]))
                        .filter(k => !k.startsWith('_'));

                      return (
                        <div key={candidate.candidate_id || cIdx} className="bg-slate-50/60 rounded-xl border border-slate-200 p-4 space-y-3">
                          {/* Candidate Header */}
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-slate-200">
                            <div className="flex items-center gap-2">
                              <span className="w-5 h-5 rounded-full bg-blue-600 text-white text-[10px] font-bold flex items-center justify-center">
                                {cIdx + 1}
                              </span>
                              <span className="text-xs font-bold text-slate-900">
                                Row #{candidate.record_a_index} & Row #{candidate.record_b_index}
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-semibold border border-blue-200">
                                Matched Fields: {candidate.matched_field_count} ({candidate.matched_fields.join(', ')})
                              </span>
                              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-200">
                                Match Confidence: {Math.round(candidate.match_confidence * 100)}%
                              </span>
                            </div>

                            {/* Action Buttons */}
                            <div className="flex items-center gap-1.5 self-end sm:self-auto">
                              {action ? (
                                <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-md text-xs font-semibold border ${
                                  action === 'merged'
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                                    : action === 'separate'
                                    ? 'bg-slate-100 text-slate-700 border-slate-300'
                                    : 'bg-blue-50 text-blue-700 border-blue-300'
                                }`}>
                                  <Check className="w-3.5 h-3.5" />
                                  <span>{action === 'merged' ? 'Merged' : action === 'separate' ? 'Kept Separate' : 'Under Review'}</span>
                                </span>
                              ) : (
                                <>
                                  <button
                                    type="button"
                                    onClick={() => setCandidateActions(prev => ({ ...prev, [candidate.candidate_id]: 'merged' }))}
                                    className="px-2.5 py-1 text-xs font-semibold rounded-md bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs transition-colors flex items-center gap-1"
                                  >
                                    <GitMerge className="w-3 h-3" />
                                    <span>Merge</span>
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setCandidateActions(prev => ({ ...prev, [candidate.candidate_id]: 'separate' }))}
                                    className="px-2.5 py-1 text-xs font-semibold rounded-md bg-white hover:bg-slate-100 text-slate-700 border border-slate-200 shadow-2xs transition-colors"
                                  >
                                    Keep Separate
                                  </button>
                                  <button
                                    type="button"
                                    onClick={() => setCandidateActions(prev => ({ ...prev, [candidate.candidate_id]: 'review' }))}
                                    className="px-2.5 py-1 text-xs font-semibold rounded-md bg-blue-50 hover:bg-blue-100 text-blue-700 border border-blue-200 shadow-2xs transition-colors"
                                  >
                                    Review
                                  </button>
                                </>
                              )}
                            </div>
                          </div>

                          {/* Side-by-Side Comparison Table */}
                          <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white">
                            <table className="w-full text-left text-xs">
                              <thead className="bg-slate-50 font-semibold text-slate-700 border-b border-slate-200 text-[11px]">
                                <tr>
                                  <th className="px-3.5 py-2 w-1/4">Field</th>
                                  <th className="px-3.5 py-2 w-1/3">Record A (Row #{candidate.record_a_index})</th>
                                  <th className="px-3.5 py-2 w-1/3">Record B (Row #{candidate.record_b_index})</th>
                                  <th className="px-3.5 py-2 text-center">Status</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-slate-100 font-mono text-[11px]">
                                {allKeys.map(key => {
                                  const valA = candidate.record_a[key];
                                  const valB = candidate.record_b[key];
                                  const isMatched = candidate.matched_fields.includes(key);
                                  const isEmptyA = valA === null || valA === undefined || String(valA).trim() === '';
                                  const isEmptyB = valB === null || valB === undefined || String(valB).trim() === '';

                                  return (
                                    <tr key={key} className={isMatched ? 'bg-emerald-50/40' : (isEmptyA || isEmptyB) ? 'bg-amber-50/20' : ''}>
                                      <td className="px-3.5 py-2 font-semibold text-slate-800 font-sans">{key}</td>
                                      <td className="px-3.5 py-2 text-slate-700">
                                        {isEmptyA ? (
                                          <span className="text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 text-[10px] italic">Missing</span>
                                        ) : isMatched ? (
                                          <span className="text-emerald-900 font-semibold">{String(valA)}</span>
                                        ) : (
                                          String(valA)
                                        )}
                                      </td>
                                      <td className="px-3.5 py-2 text-slate-700">
                                        {isEmptyB ? (
                                          <span className="text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded border border-amber-200 text-[10px] italic">Missing</span>
                                        ) : isMatched ? (
                                          <span className="text-emerald-900 font-semibold">{String(valB)} ✓</span>
                                        ) : (
                                          String(valB)
                                        )}
                                      </td>
                                      <td className="px-3.5 py-2 text-center">
                                        {isMatched ? (
                                          <span className="inline-flex items-center gap-0.5 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-300">
                                            <Check className="w-3 h-3" /> Matched
                                          </span>
                                        ) : (isEmptyA && !isEmptyB) || (!isEmptyA && isEmptyB) ? (
                                          <span className="text-[10px] font-medium text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded border border-amber-200">
                                            Fillable
                                          </span>
                                        ) : (
                                          <span className="text-slate-400 text-[10px]">—</span>
                                        )}
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      );
                    })
                  )}
                </div>
              )}

              {/* SECTION 2: MERGED RECORDS */}
              {matchingSubTab === 'merged' && (
                <div className="space-y-4">
                  {recordMatchingReport.merged_records.length === 0 ? (
                    <div className="py-8 text-center bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
                      <Info className="w-8 h-8 text-slate-400 mx-auto mb-2" />
                      <p className="text-xs font-semibold text-slate-700">No Automatically Merged Records</p>
                      <p className="text-[11px] text-slate-500 mt-0.5">Records are merged when complementary non-conflicting fields match 2+ identifiers.</p>
                    </div>
                  ) : (
                    recordMatchingReport.merged_records.map((mergedItem, mIdx) => (
                      <div key={mergedItem.merge_id || mIdx} className="bg-emerald-50/30 rounded-xl border border-emerald-200 p-4 space-y-3">
                        {/* Header */}
                        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-2 border-b border-emerald-200">
                          <div className="flex items-center gap-2">
                            <span className="w-5 h-5 rounded-full bg-emerald-600 text-white text-[10px] font-bold flex items-center justify-center">
                              {mIdx + 1}
                            </span>
                            <span className="text-xs font-bold text-emerald-950">
                              Original Row #{mergedItem.record_a_index} + Original Row #{mergedItem.record_b_index} ➔ Unified Entity
                            </span>
                            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-semibold border border-emerald-300">
                              ✓ {mergedItem.status}
                            </span>
                          </div>
                          <div className="flex items-center gap-2 text-[11px] text-slate-600">
                            <span>Matched Using: <strong>{mergedItem.matched_using_fields.join(', ')}</strong></span>
                          </div>
                        </div>

                        {/* Merged Record Key-Values */}
                        <div className="bg-white rounded-lg border border-emerald-200/80 p-3">
                          <div className="text-[11px] font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                            <Sparkles className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Complete Merged Entity Representation:</span>
                          </div>
                          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
                            {Object.entries(mergedItem.merged_record)
                              .filter(([k]) => !k.startsWith('_'))
                              .map(([k, v]) => {
                                const isFilled = mergedItem.filled_fields.includes(k);
                                return (
                                  <div key={k} className={`p-2 rounded-md border text-xs ${
                                    isFilled
                                      ? 'bg-emerald-50/80 border-emerald-300 text-emerald-950 font-semibold'
                                      : 'bg-slate-50 border-slate-200 text-slate-800'
                                  }`}>
                                    <div className="text-[10px] text-slate-500 font-sans flex items-center justify-between">
                                      <span>{k}</span>
                                      {isFilled && <span className="text-emerald-700 font-bold">Filled</span>}
                                    </div>
                                    <div className="font-mono mt-0.5 truncate">{v === null ? <span className="text-slate-300 italic">null</span> : String(v)}</div>
                                  </div>
                                );
                              })}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          ) : (
            /* Standard Quality Dimensions Inspector Table for Dimensions 1 to 6 */
            <div>
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
      )}
    </div>
  );
};
