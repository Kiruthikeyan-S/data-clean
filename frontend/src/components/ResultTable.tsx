import React, { useState, useMemo } from 'react';
import {
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Table
} from 'lucide-react';
import { ProcessResponse } from '../types';

interface ResultTableProps {
  result: ProcessResponse;
}

const PAGE_SIZE = 10;

export const ResultTable: React.FC<ResultTableProps> = ({ result }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedEntityTab, setSelectedEntityTab] = useState<number>(-1); // -1 = Full Combined

  const isTabular = Array.isArray(result.structured_data);
  const splitTables = result.entity_info?.split_tables || [];
  const hasSplitTables = splitTables.length > 0;

  // Active split table if any selected
  const activeTable = selectedEntityTab >= 0 && selectedEntityTab < splitTables.length ? splitTables[selectedEntityTab] : null;

  const isFullCombined = hasSplitTables && selectedEntityTab === -1;

  // Tabular data for Processed View
  const processedRows: Array<Record<string, any>> = useMemo(() => {
    if (activeTable) {
      return activeTable.records || [];
    }
    if (isTabular) {
      if (isFullCombined) {
        const combined = splitTables.flatMap(t =>
          (t.records || []).map(r => ({
            ...r,
            _entity_display: t.display_name,
            _entity_icon: t.icon,
            _entity_type: t.entity_type
          }))
        );
        if (combined.length > 0) return combined;
      }
      return (result.structured_data as Array<Record<string, any>>) || [];
    }
    return [];
  }, [result.structured_data, isTabular, activeTable, isFullCombined, splitTables]);

  const processedColumns: string[] = useMemo(() => {
    if (activeTable) {
      const cols = activeTable.columns || (activeTable.records.length > 0 ? Object.keys(activeTable.records[0]) : []);
      return cols.filter(c => !c.startsWith('_'));
    }
    if (isTabular) {
      let candidateCols: string[] = [];
      if (isFullCombined) {
        const colSet = new Set<string>();
        splitTables.forEach(t => {
          (t.columns || []).forEach(c => {
            if (!c.startsWith('_')) colSet.add(c);
          });
        });
        if (colSet.size > 0) {
          candidateCols = Array.from(colSet);
        }
      } else {
        candidateCols = (result.columns || []).filter(c => !c.startsWith('_'));
      }
      if (candidateCols.length === 0 && processedRows.length > 0) {
        candidateCols = Object.keys(processedRows[0]).filter(c => !c.startsWith('_'));
      }
      const populatedCols = candidateCols.filter(col => {
        return processedRows.some(row => {
          const val = row[col];
          if (val === null || val === undefined) return false;
          const str = String(val).trim().toLowerCase();
          return str !== '' && str !== 'null' && str !== 'none' && str !== 'n/a' && str !== '-' && str !== 'nan';
        });
      });
      return populatedCols.length > 0 ? populatedCols : candidateCols;
    }
    return ['Field', 'Standardized Value', 'Raw Extracted Value'];
  }, [result.columns, isTabular, processedRows, activeTable, isFullCombined, splitTables]);

  // Filter rows by search query
  const filteredRows = useMemo(() => {
    if (!isTabular && !activeTable) return [];
    if (!searchQuery.trim()) return processedRows;
    const q = searchQuery.toLowerCase();
    return processedRows.filter(row =>
      Object.values(row).some(val => val !== null && String(val).toLowerCase().includes(q))
    );
  }, [processedRows, searchQuery, isTabular, activeTable]);

  // Pagination
  const totalPages = Math.ceil(filteredRows.length / PAGE_SIZE) || 1;
  const paginatedRows = useMemo(() => {
    if (!isTabular && !activeTable) return [];
    const start = (currentPage - 1) * PAGE_SIZE;
    return filteredRows.slice(start, start + PAGE_SIZE);
  }, [filteredRows, currentPage, isTabular, activeTable]);

  const formatHeader = (col: string) => {
    return col.replace(/_/g, ' ').toUpperCase();
  };

  const getEntityBadge = (type?: string, customDisplayName?: string) => {
    switch (type?.toLowerCase()) {
      case 'car':
        return { label: customDisplayName || 'Vehicle / Automotive', icon: '🚗', bg: 'bg-orange-50 text-orange-800 border-orange-200' };
      case 'invoice':
        return { label: customDisplayName || 'Invoice / Billing Document', icon: '🧾', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
      case 'employee':
        return { label: customDisplayName || 'Employee / HR Record', icon: '💼', bg: 'bg-cyan-50 text-cyan-800 border-cyan-200' };
      case 'student':
      case 'academic':
      case 'syllabus':
      case 'course':
        return { label: customDisplayName || 'Academic / Course Syllabus', icon: '🎓', bg: 'bg-blue-50 text-blue-800 border-blue-200' };
      case 'medical':
        return { label: customDisplayName || 'Medical / Patient Record', icon: '🏥', bg: 'bg-rose-50 text-rose-800 border-rose-200' };
      case 'store':
        return { label: customDisplayName || 'Store / Branch Data', icon: '🏪', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
      case 'item':
        return { label: customDisplayName || 'Item / Product', icon: '📦', bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' };
      case 'customer':
        return { label: customDisplayName || 'Customer Data', icon: '👤', bg: 'bg-purple-50 text-purple-800 border-purple-200' };
      case 'transaction':
        return { label: customDisplayName || 'Transaction Data', icon: '💳', bg: 'bg-amber-50 text-amber-800 border-amber-200' };
      case 'mixed':
        return { label: 'Multiple Entity', icon: '🔀', bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' };
      default:
        return { label: customDisplayName || 'General / Custom', icon: '📁', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
    }
  };

  const entityBadge = getEntityBadge(result.entity_info?.entity_type, result.entity_info?.display_name);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Table Top Header */}
      <div className="p-5 sm:p-6 border-b border-slate-200 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3">
              <h2 className="text-xl font-bold text-slate-900 tracking-tight">Dataset Inspector</h2>
              {result.entity_info && (
                <span className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold border ${entityBadge.bg}`}>
                  <span>{entityBadge.icon}</span>
                  <span>{entityBadge.label}</span>
                </span>
              )}
            </div>

            <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mt-1.5 text-xs text-slate-500 font-medium">
              <div>
                <span className="text-slate-400 mr-1">File:</span>
                <span className="text-slate-800 font-semibold">{result.filename}</span>
              </div>
              <div className="border-l border-slate-200 pl-4">
                <span className="text-slate-400 mr-1">Input Format:</span>
                <span className="text-slate-800 uppercase font-mono">{result.file_type}</span>
              </div>
              <div className="border-l border-slate-200 pl-4 flex items-center gap-1.5">
                <span className="text-slate-400 mr-1">Status:</span>
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-3 h-3" />
                  Cleaned & Standardized
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Header Controls: Record Counter & Search Box */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100">
          <div className="flex items-center gap-2">
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-200">
              <Table className="w-3.5 h-3.5" />
              <span>Processed Records</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-blue-200/70 text-blue-800 font-mono font-bold">
                {processedRows.length}
              </span>
            </span>
          </div>

          {/* Search Box */}
          {(isTabular || activeTable) && (
            <div className="relative min-w-[260px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search processed records..."
                value={searchQuery}
                onChange={e => {
                  setSearchQuery(e.target.value);
                  setCurrentPage(1);
                }}
                className="w-full pl-9 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:bg-white transition-all text-slate-800 placeholder-slate-400"
              />
            </div>
          )}
        </div>
      </div>

      {/* Per-Entity Sub-Tabs (for Mixed/Multiple Entity datasets split into Store, Item, Customer, Transaction tables) */}
      {hasSplitTables && (
        <div className="px-5 py-2.5 bg-slate-50/70 border-b border-slate-200 flex items-center gap-2 overflow-x-auto">
          <span className="text-[11px] font-semibold text-slate-500 mr-1 shrink-0">
            Split Entity Tables:
          </span>
          <button
            onClick={() => { setSelectedEntityTab(-1); setCurrentPage(1); }}
            className={`px-3 py-1 rounded-md text-xs font-medium border transition-colors shrink-0 ${
              selectedEntityTab === -1
                ? 'bg-blue-600 text-white border-blue-600 shadow-2xs'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
            }`}
          >
            🔀 Full Combined ({result.cleansing_report?.final_rows || processedRows.length || (result.structured_data as any[])?.length || 0} rows)
          </button>

          {splitTables.map((t, idx) => (
            <button
              key={idx}
              onClick={() => { setSelectedEntityTab(idx); setCurrentPage(1); }}
              className={`px-3 py-1 rounded-md text-xs font-medium border transition-colors flex items-center gap-1.5 shrink-0 ${
                selectedEntityTab === idx
                  ? 'bg-blue-600 text-white border-blue-600 shadow-2xs'
                  : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100'
              }`}
            >
              <span>{t.icon}</span>
              <span>{t.display_name}</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                selectedEntityTab === idx ? 'bg-blue-700 text-blue-100' : 'bg-slate-100 text-slate-600'
              }`}>
                {t.deduplicated_rows}
              </span>
            </button>
          ))}
        </div>
      )}

      {/* PROCESSED DATA TABLE */}
      {isTabular ? (
        <div>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50/80 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3 w-12 text-center text-slate-400">#</th>
                  {isFullCombined && (
                    <th className="px-4 py-3 font-bold text-slate-700 whitespace-nowrap">
                      ENTITY TYPE
                    </th>
                  )}
                  {processedColumns.map(col => (
                    <th key={col} className="px-5 py-3 font-bold text-slate-700 whitespace-nowrap">
                      {formatHeader(col)}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedRows.length === 0 ? (
                  <tr>
                    <td colSpan={processedColumns.length + (isFullCombined ? 2 : 1)} className="px-5 py-10 text-center text-slate-400 text-sm">
                      No matching records found.
                    </td>
                  </tr>
                ) : (
                  paginatedRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-4 py-3 text-xs text-center text-slate-400 font-mono">
                        {(currentPage - 1) * PAGE_SIZE + idx + 1}
                      </td>
                      {isFullCombined && (
                        <td className="px-4 py-3 whitespace-nowrap">
                          <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[11px] font-semibold bg-slate-100 text-slate-700 border border-slate-200 shadow-2xs">
                            <span>{row._entity_icon || '📁'}</span>
                            <span>{row._entity_display || 'Record'}</span>
                          </span>
                        </td>
                      )}
                      {processedColumns.map(col => {
                        const val = row[col];
                        return (
                          <td key={col} className="px-5 py-3 whitespace-nowrap text-xs text-slate-800">
                            {val === null || val === undefined ? (
                              <span className="text-slate-300 italic text-[11px]">null</span>
                            ) : typeof val === 'boolean' ? (
                              <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold ${
                                val ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-600'
                              }`}>
                                {val ? 'true' : 'false'}
                              </span>
                            ) : (
                              <span className="font-mono text-slate-900">{String(val)}</span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <span className="font-semibold text-slate-700">{filteredRows.length > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0}</span> to{' '}
              <span className="font-semibold text-slate-700">
                {Math.min(currentPage * PAGE_SIZE, filteredRows.length)}
              </span>{' '}
              of <span className="font-semibold text-slate-700">{filteredRows.length}</span> records
              {searchQuery && ` (filtered from ${processedRows.length} total)`}
            </div>

            {totalPages > 1 && (
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
                  disabled={currentPage === 1}
                  className="p-1 rounded border border-slate-200 bg-white text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                >
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <span className="px-2 font-medium text-slate-700">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  type="button"
                  onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
                  disabled={currentPage === totalPages}
                  className="p-1 rounded border border-slate-200 bg-white text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-50 transition-colors"
                >
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Unstructured Key-Value Entities Table */
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-700">
            <thead className="bg-slate-50/80 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3 w-1/4">Field</th>
                <th className="px-6 py-3 w-2/5">Standardized Value</th>
                <th className="px-6 py-3 w-1/3">Raw Extracted Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {(() => {
                const validFields = (result.fields || []).filter(
                  f => (f.value !== null && f.value !== undefined && String(f.value).trim() !== '' && String(f.value).toLowerCase() !== 'null') ||
                       (f.raw_value !== null && f.raw_value !== undefined && String(f.raw_value).trim() !== '' && String(f.raw_value).toLowerCase() !== 'null')
                );

                if (validFields.length === 0) {
                  return (
                    <tr>
                      <td colSpan={3} className="px-6 py-8 text-center text-slate-400 text-xs">
                        No specific structured fields detected in document. View raw extracted text below.
                      </td>
                    </tr>
                  );
                }

                return validFields.map(field => {
                  const hasValue = field.value !== null && field.value !== undefined;
                  const hasRaw = field.raw_value !== null && field.raw_value !== undefined;

                  return (
                    <tr key={field.key} className="hover:bg-slate-50/70 transition-colors">
                      <td className="px-6 py-3.5 text-xs font-semibold text-slate-900 flex items-center gap-2">
                        {field.label}
                        {!field.is_valid && (
                          <span title={field.error_message || 'Format warning'}>
                            <AlertCircle className="w-3.5 h-3.5 text-amber-500 inline" />
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-xs">
                        {hasValue ? (
                          <span className="font-medium text-slate-900 bg-blue-50/60 text-blue-900 px-2 py-0.5 rounded border border-blue-100 font-mono">
                            {String(field.value)}
                          </span>
                        ) : (
                          <span className="text-slate-300 italic text-xs">null</span>
                        )}
                      </td>
                      <td className="px-6 py-3.5 text-xs text-slate-500">
                        {hasRaw ? (
                          <span className="font-mono text-slate-600">{String(field.raw_value)}</span>
                        ) : (
                          <span className="text-slate-300 italic text-xs">—</span>
                        )}
                      </td>
                    </tr>
                  );
                });
              })()}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
