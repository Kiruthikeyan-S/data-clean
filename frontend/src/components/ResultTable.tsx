import React, { useState, useMemo } from 'react';
import {
  Search,
  ChevronLeft,
  ChevronRight,
  CheckCircle2,
  AlertCircle,
  Table,
  FileCode,
  GitMerge,
  ArrowRight,
  Sparkles,
  Info,
  ShieldCheck
} from 'lucide-react';
import { ProcessResponse } from '../types';

interface ResultTableProps {
  result: ProcessResponse;
}

const PAGE_SIZE = 10;

export const ResultTable: React.FC<ResultTableProps> = ({ result }) => {
  const [activeView, setActiveView] = useState<'processed' | 'raw' | 'mapping'>('processed');
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedEntityTab, setSelectedEntityTab] = useState<number>(-1); // -1 = Full Combined

  const isTabular = Array.isArray(result.structured_data);
  const hasRawData = Array.isArray(result.raw_structured_data) && result.raw_structured_data.length > 0;

  const splitTables = result.entity_info?.split_tables || [];
  const hasSplitTables = splitTables.length > 0;

  // Active split table if any selected
  const activeTable = selectedEntityTab >= 0 && selectedEntityTab < splitTables.length ? splitTables[selectedEntityTab] : null;

  // Active mapping report
  const activeSchemaReport = useMemo(() => {
    if (activeTable && activeTable.schema_mapping_report && activeTable.schema_mapping_report.length > 0) {
      return activeTable.schema_mapping_report;
    }
    return result.schema_mapping_report || [];
  }, [activeTable, result.schema_mapping_report]);

  // Tabular data for Processed View
  const processedRows: Array<Record<string, any>> = useMemo(() => {
    if (activeTable) {
      return activeTable.records || [];
    }
    if (isTabular) {
      return (result.structured_data as Array<Record<string, any>>) || [];
    }
    return [];
  }, [result.structured_data, isTabular, activeTable]);

  const processedColumns: string[] = useMemo(() => {
    if (activeTable) {
      return activeTable.columns || (activeTable.records.length > 0 ? Object.keys(activeTable.records[0]) : []);
    }
    if (isTabular) {
      const candidateCols = result.columns || (processedRows.length > 0 ? Object.keys(processedRows[0]) : []);
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
  }, [result.columns, isTabular, processedRows, activeTable]);

  // Raw data for Raw View
  const rawRows: Array<Record<string, any>> = useMemo(() => {
    if (hasRawData) {
      return result.raw_structured_data || [];
    }
    return processedRows;
  }, [hasRawData, result.raw_structured_data, processedRows]);

  const rawColumns: string[] = useMemo(() => {
    if (result.raw_columns && result.raw_columns.length > 0) {
      return result.raw_columns;
    }
    if (rawRows.length > 0) {
      return Object.keys(rawRows[0]);
    }
    return processedColumns;
  }, [result.raw_columns, rawRows, processedColumns]);

  // Current active dataset depending on active view
  const currentDatasetRows = activeView === 'raw' ? rawRows : processedRows;

  // Filter rows by search query
  const filteredRows = useMemo(() => {
    if (!isTabular && !activeTable) return [];
    if (!searchQuery.trim()) return currentDatasetRows;
    const q = searchQuery.toLowerCase();
    return currentDatasetRows.filter(row =>
      Object.values(row).some(val => val !== null && String(val).toLowerCase().includes(q))
    );
  }, [currentDatasetRows, searchQuery, isTabular, activeTable]);

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

  const getEntityBadge = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'store':
        return { label: 'Store Data', icon: '🏪', bg: 'bg-emerald-50 text-emerald-800 border-emerald-200' };
      case 'item':
        return { label: 'Item / Product', icon: '📦', bg: 'bg-indigo-50 text-indigo-800 border-indigo-200' };
      case 'customer':
        return { label: 'Customer Data', icon: '👤', bg: 'bg-purple-50 text-purple-800 border-purple-200' };
      case 'transaction':
        return { label: 'Transaction Data', icon: '🧾', bg: 'bg-amber-50 text-amber-800 border-amber-200' };
      case 'mixed':
        return { label: 'Mixed Dataset', icon: '🔀', bg: 'bg-blue-50 text-blue-800 border-blue-200' };
      default:
        return { label: 'General / Custom', icon: '📁', bg: 'bg-slate-50 text-slate-700 border-slate-200' };
    }
  };

  const entityBadge = getEntityBadge(result.entity_info?.entity_type);
  const confidencePercent = Math.round((result.entity_info?.confidence ?? 0.95) * 100);
  const coveragePercent = Math.round((result.schema_mapping_coverage ?? 1.0) * 100);
  const qualityPercent = Math.round((result.data_quality_score ?? 0.98) * 100);

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Table Top Header & Metrics Banner */}
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

          {/* 3 Metric Score Cards */}
          <div className="grid grid-cols-3 gap-2 sm:gap-3 shrink-0">
            <div className="px-3 py-2 bg-slate-50 rounded-lg border border-slate-200 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-center gap-1">
                <Sparkles className="w-3 h-3 text-amber-500" />
                <span>Entity Match</span>
              </div>
              <div className="text-sm font-extrabold text-slate-800 mt-0.5">
                {confidencePercent}%
              </div>
            </div>

            <div className="px-3 py-2 bg-slate-50 rounded-lg border border-slate-200 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-center gap-1">
                <GitMerge className="w-3 h-3 text-blue-500" />
                <span>Schema Match</span>
              </div>
              <div className="text-sm font-extrabold text-blue-600 mt-0.5">
                {coveragePercent}%
              </div>
            </div>

            <div className="px-3 py-2 bg-slate-50 rounded-lg border border-slate-200 text-center">
              <div className="text-[10px] uppercase font-bold text-slate-400 flex items-center justify-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-500" />
                <span>Quality Score</span>
              </div>
              <div className="text-sm font-extrabold text-emerald-600 mt-0.5">
                {qualityPercent}%
              </div>
            </div>
          </div>
        </div>

        {/* View Switcher Tabs & Search Row */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-slate-100">
          {/* 3 Tab Switchers */}
          <div className="inline-flex p-1 bg-slate-100 rounded-lg border border-slate-200 self-start">
            <button
              onClick={() => { setActiveView('processed'); setCurrentPage(1); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeView === 'processed'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Table className="w-3.5 h-3.5" />
              <span>Processed Data</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                activeView === 'processed' ? 'bg-blue-100 text-blue-800' : 'bg-slate-200 text-slate-600'
              }`}>
                {processedRows.length}
              </span>
            </button>

            <button
              onClick={() => { setActiveView('raw'); setCurrentPage(1); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeView === 'raw'
                  ? 'bg-white text-blue-700 shadow-xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>Raw Data</span>
              <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                activeView === 'raw' ? 'bg-blue-100 text-blue-800' : 'bg-slate-200 text-slate-600'
              }`}>
                {rawRows.length}
              </span>
            </button>

            {activeSchemaReport.length > 0 && (
              <button
                onClick={() => setActiveView('mapping')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                  activeView === 'mapping'
                    ? 'bg-white text-blue-700 shadow-xs'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <GitMerge className="w-3.5 h-3.5" />
                <span>Schema Mapping</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${
                  activeView === 'mapping' ? 'bg-emerald-100 text-emerald-800 font-bold' : 'bg-slate-200 text-slate-600'
                }`}>
                  {activeSchemaReport.filter(m => m.is_mapped).length}/{activeSchemaReport.length}
                </span>
              </button>
            )}
          </div>

          {/* Search Box (for Processed and Raw views) */}
          {activeView !== 'mapping' && (isTabular || activeTable) && (
            <div className="relative min-w-[240px]">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={`Search ${activeView === 'raw' ? 'raw' : 'processed'} records...`}
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

      {/* Per-Entity Sub-Tabs (for Mixed datasets split into Store, Item, Customer, Transaction tables) */}
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
            🔀 Full Combined ({result.cleansing_report?.final_rows || (result.structured_data as any[])?.length || 0} rows)
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

      {/* VIEW 1: PROCESSED DATA TABLE */}
      {activeView === 'processed' && (
        isTabular ? (
          <div>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-700">
                <thead className="bg-slate-50/80 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
                  <tr>
                    <th className="px-5 py-3 w-12 text-center text-slate-400">#</th>
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
                      <td colSpan={processedColumns.length + 1} className="px-5 py-10 text-center text-slate-400 text-sm">
                        No matching records found.
                      </td>
                    </tr>
                  ) : (
                    paginatedRows.map((row, idx) => (
                      <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                        <td className="px-5 py-3 text-xs text-center text-slate-400 font-mono">
                          {(currentPage - 1) * PAGE_SIZE + idx + 1}
                        </td>
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
        )
      )}

      {/* VIEW 2: RAW DATA TABLE (Unmerged inconsistent columns) */}
      {activeView === 'raw' && (
        <div>
          <div className="bg-amber-50/60 border-b border-amber-200/60 px-6 py-3 text-xs text-amber-900 flex items-center gap-2">
            <Info className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              Showing original raw records before alias merging and standardization. Notice the inconsistent keys and duplicate-like columns.
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-500 border-b border-slate-200 tracking-wider">
                <tr>
                  <th className="px-5 py-3 w-12 text-center text-slate-400">#</th>
                  {rawColumns.map(col => (
                    <th key={col} className="px-5 py-3 font-mono text-slate-600 whitespace-nowrap">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {paginatedRows.length === 0 ? (
                  <tr>
                    <td colSpan={rawColumns.length + 1} className="px-5 py-10 text-center text-slate-400 text-sm">
                      No raw records available.
                    </td>
                  </tr>
                ) : (
                  paginatedRows.map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors font-mono text-xs">
                      <td className="px-5 py-3 text-center text-slate-400">
                        {(currentPage - 1) * PAGE_SIZE + idx + 1}
                      </td>
                      {rawColumns.map(col => {
                        const val = row[col];
                        return (
                          <td key={col} className="px-5 py-3 whitespace-nowrap text-slate-800">
                            {val === null || val === undefined ? (
                              <span className="text-rose-300 font-sans italic text-[11px]">null</span>
                            ) : (
                              String(val)
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

          {/* Raw Pagination */}
          <div className="p-4 border-t border-slate-200 bg-slate-50/50 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-slate-500">
            <div>
              Showing <span className="font-semibold text-slate-700">{filteredRows.length > 0 ? (currentPage - 1) * PAGE_SIZE + 1 : 0}</span> to{' '}
              <span className="font-semibold text-slate-700">
                {Math.min(currentPage * PAGE_SIZE, filteredRows.length)}
              </span>{' '}
              of <span className="font-semibold text-slate-700">{filteredRows.length}</span> raw records
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
      )}

      {/* VIEW 3: SCHEMA MAPPING VISUAL INSPECTOR */}
      {activeView === 'mapping' && (
        <div className="p-6 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <GitMerge className="w-4 h-4 text-blue-600" />
                Canonical Schema Mapping Breakdown
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                Shows how raw inconsistent aliases were coalesced row-by-row into canonical enterprise fields.
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-medium text-slate-500">Mapping Coverage:</span>
              <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-emerald-50 text-emerald-700 border border-emerald-200">
                {coveragePercent}% Covered
              </span>
            </div>
          </div>

          <div className="border border-slate-200 rounded-xl overflow-hidden shadow-2xs">
            <table className="w-full text-left text-sm text-slate-700">
              <thead className="bg-slate-50 text-xs font-semibold text-slate-600 border-b border-slate-200 uppercase tracking-wider">
                <tr>
                  <th className="px-6 py-3 w-1/4">Canonical Standard Field</th>
                  <th className="px-6 py-3 w-1/3">Raw Source Aliases Coalesced</th>
                  <th className="px-6 py-3 w-1/6 text-center">Data Type</th>
                  <th className="px-6 py-3 w-1/6 text-center">Populated Rows</th>
                  <th className="px-6 py-3 w-1/6 text-right">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activeSchemaReport.map((item, idx) => (
                  <tr key={idx} className="hover:bg-slate-50/70 transition-colors">
                    {/* Canonical Field */}
                    <td className="px-6 py-4">
                      <div className="font-bold font-mono text-slate-900 text-xs">
                        {item.canonical_field}
                      </div>
                      {item.description && (
                        <div className="text-[11px] text-slate-500 mt-0.5">
                          {item.description}
                        </div>
                      )}
                    </td>

                    {/* Source Aliases */}
                    <td className="px-6 py-4">
                      {item.source_aliases && item.source_aliases.length > 0 ? (
                        <div className="flex flex-wrap items-center gap-1.5">
                          {item.source_aliases.map((alias, aIdx) => (
                            <span
                              key={aIdx}
                              className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 border border-blue-200 font-mono text-xs"
                            >
                              {alias}
                            </span>
                          ))}
                          <ArrowRight className="w-3.5 h-3.5 text-slate-400 mx-1 shrink-0" />
                          <span className="font-bold text-slate-800 text-xs font-mono">
                            {item.canonical_field}
                          </span>
                        </div>
                      ) : (
                        <span className="text-slate-400 italic text-xs">No matching raw column</span>
                      )}
                    </td>

                    {/* Field Type */}
                    <td className="px-6 py-4 text-center">
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-mono font-medium bg-slate-100 text-slate-700">
                        {item.field_type}
                      </span>
                    </td>

                    {/* Rows Populated */}
                    <td className="px-6 py-4 text-center">
                      <span className="font-semibold text-slate-800 text-xs font-mono">
                        {item.rows_populated} / {processedRows.length}
                      </span>
                    </td>

                    {/* Status Badge */}
                    <td className="px-6 py-4 text-right">
                      {item.is_mapped ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3 h-3" />
                          Mapped
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-500">
                          Optional / Absent
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
