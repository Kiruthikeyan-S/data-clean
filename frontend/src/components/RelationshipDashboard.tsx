import React, { useState, useMemo } from 'react';
import { 
  Network, 
  Link2, 
  ShieldCheck, 
  Layers, 
  Search, 
  ChevronDown, 
  ChevronUp, 
  FileSpreadsheet, 
  FileCode, 
  ArrowRightLeft,
  Building2,
  Package,
  User,
  CreditCard,
  Car,
  GraduationCap,
  Stethoscope,
  Briefcase,
  FileText
} from 'lucide-react';
import { RelationshipIndexData } from '../types';
import { getBatchExportUrl } from '../services/api';

interface RelationshipDashboardProps {
  batchId?: string;
  relationshipIndex?: RelationshipIndexData;
}

export const RelationshipDashboard: React.FC<RelationshipDashboardProps> = ({
  batchId,
  relationshipIndex
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [minRecordsFilter, setMinRecordsFilter] = useState<number>(3);
  const [expandedEntities, setExpandedEntities] = useState<Record<string, boolean>>({});

  const toggleExpand = (entityId: string) => {
    setExpandedEntities(prev => ({
      ...prev,
      [entityId]: !prev[entityId]
    }));
  };

  const expandAll = () => {
    if (!relationshipIndex) return;
    const allExpanded: Record<string, boolean> = {};
    relationshipIndex.entities.forEach(e => {
      allExpanded[e.entity_id] = true;
    });
    setExpandedEntities(allExpanded);
  };

  const collapseAll = () => {
    setExpandedEntities({});
  };

  const entities = relationshipIndex?.entities || [];

  // Distinct relationship types for filtering
  const availableTypes = useMemo(() => {
    const types = new Set<string>();
    entities.forEach(e => {
      if (e.relationship_type) types.add(e.relationship_type);
    });
    return Array.from(types);
  }, [entities]);

  // Filtered entities (requires min records threshold e.g. >= 3)
  const filteredEntities = useMemo(() => {
    return entities.filter(entity => {
      if (entity.records_count < minRecordsFilter) return false;

      const matchesType = selectedType === 'all' || entity.relationship_type === selectedType;
      if (!matchesType) return false;

      if (!searchTerm.trim()) return true;
      const term = searchTerm.toLowerCase();

      const inId = entity.entity_id.toLowerCase().includes(term);
      const inName = entity.display_name.toLowerCase().includes(term);
      const inKey = entity.primary_match_key.toLowerCase().includes(term);
      const inMethod = entity.match_method.toLowerCase().includes(term);
      const inFiles = entity.files_involved.some(f => f.toLowerCase().includes(term));
      const inRecords = entity.records.some(r => 
        Object.values(r.record).some(v => String(v).toLowerCase().includes(term))
      );

      return inId || inName || inKey || inMethod || inFiles || inRecords;
    });
  }, [entities, selectedType, searchTerm, minRecordsFilter]);

  const getDomainIcon = (domain?: string) => {
    switch (domain?.toLowerCase()) {
      case 'car':
      case 'vehicle':
        return <Car className="w-3.5 h-3.5 text-amber-600" />;
      case 'student':
      case 'academic':
        return <GraduationCap className="w-3.5 h-3.5 text-indigo-600" />;
      case 'medical':
        return <Stethoscope className="w-3.5 h-3.5 text-rose-600" />;
      case 'employee':
        return <Briefcase className="w-3.5 h-3.5 text-slate-600" />;
      case 'store':
        return <Building2 className="w-3.5 h-3.5 text-emerald-600" />;
      case 'item':
      case 'product':
        return <Package className="w-3.5 h-3.5 text-violet-600" />;
      case 'customer':
        return <User className="w-3.5 h-3.5 text-blue-600" />;
      case 'transaction':
      case 'invoice':
        return <CreditCard className="w-3.5 h-3.5 text-emerald-600" />;
      default:
        return <FileText className="w-3.5 h-3.5 text-slate-500" />;
    }
  };

  const getConfidenceBadge = (score: number) => {
    const percent = Math.round(score * 100);
    if (score >= 0.95) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          {percent}% High Confidence
        </span>
      );
    } else if (score >= 0.88) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
          <ShieldCheck className="w-3 h-3 text-blue-600" />
          {percent}% Strong Match
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <ShieldCheck className="w-3 h-3 text-amber-600" />
          {percent}% Probable Match
        </span>
      );
    }
  };

  if (!relationshipIndex || entities.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-3">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <Network className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">No Cross-File Relationships Detected</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The uploaded datasets do not contain shared entity keys (Phones, Emails, Customer IDs, Store IDs, or VINs).
          Upload multiple related files to discover cross-file relationship links.
        </p>
      </div>
    );
  }

  const crossFileCount = relationshipIndex.cross_file_entities_count || 0;
  const avgConfidence = Math.round((relationshipIndex.average_confidence || 0.95) * 100);

  return (
    <div className="space-y-6">
      {/* Top Banner: Metrics & Batch Export (Light Theme) */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2.5">
              <Network className="w-6 h-6 text-blue-600" />
              <span>Cross-File Entity & Relationship Network</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
              Discovered and unified records across all uploaded datasets into cohesive business entities using 
              deterministic phone/email/ID keys and fuzzy string alignment.
            </p>
          </div>

          {/* Export Actions for entire Batch */}
          {batchId && (
            <div className="flex flex-wrap items-center gap-3">
              <a
                href={getBatchExportUrl(batchId, 'excel')}
                download
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-emerald-600 hover:bg-emerald-700 text-white shadow-2xs transition-all hover:scale-102"
              >
                <FileSpreadsheet className="w-4 h-4" />
                <span>Download Multi-Sheet Excel</span>
              </a>
              <a
                href={getBatchExportUrl(batchId, 'json')}
                download
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold bg-white hover:bg-slate-50 text-slate-700 border border-slate-300 shadow-2xs transition-all hover:scale-102"
              >
                <FileCode className="w-4 h-4 text-slate-600" />
                <span>Export Linked JSON Graph</span>
              </a>
            </div>
          )}
        </div>

        {/* Metric Cards Ribbon (Light Theme) */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-6 pt-5 border-t border-slate-100">
          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Unified Entities</span>
            <div className="text-2xl font-black text-slate-900 mt-1 flex items-baseline gap-1.5">
              <span>{relationshipIndex.total_entities_linked}</span>
              <span className="text-[10px] font-normal text-blue-600 font-bold">clusters</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Cross-File Linkages</span>
            <div className="text-2xl font-black text-emerald-700 mt-1 flex items-baseline gap-1.5">
              <span>{crossFileCount}</span>
              <span className="text-[10px] font-normal text-emerald-600 font-bold">spanning files</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Avg Match Confidence</span>
            <div className="text-2xl font-black text-blue-700 mt-1 flex items-baseline gap-1.5">
              <span>{avgConfidence}%</span>
              <span className="text-[10px] font-normal text-blue-600 font-bold">accuracy</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Records Linked</span>
            <div className="text-2xl font-black text-indigo-700 mt-1 flex items-baseline gap-1.5">
              <span>{relationshipIndex.total_records_processed}</span>
              <span className="text-[10px] font-normal text-indigo-600 font-bold">rows indexed</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Search Box */}
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Entity ID, Name, Phone, Email, or File..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-slate-800"
            />
          </div>

          {/* Quick expand/collapse actions */}
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-600">
            <button
              onClick={expandAll}
              className="px-2.5 py-1.5 rounded-md hover:bg-slate-100 border border-slate-200 text-slate-700 transition-colors"
            >
              Expand All
            </button>
            <button
              onClick={collapseAll}
              className="px-2.5 py-1.5 rounded-md hover:bg-slate-100 border border-slate-200 text-slate-700 transition-colors"
            >
              Collapse All
            </button>
          </div>
        </div>

        {/* Match Count Threshold Pills */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
            <Link2 className="w-3.5 h-3.5 text-blue-600" /> Matches Count:
          </span>
          <button
            onClick={() => setMinRecordsFilter(3)}
            className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              minRecordsFilter === 3
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            3+ Records Matched (Default)
          </button>
          <button
            onClick={() => setMinRecordsFilter(2)}
            className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              minRecordsFilter === 2
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            2+ Records Matched
          </button>
          <button
            onClick={() => setMinRecordsFilter(4)}
            className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              minRecordsFilter === 4
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            4+ Records Matched
          </button>
        </div>

        {/* Relationship Type Badges */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
            <Layers className="w-3.5 h-3.5" /> Filter Type:
          </span>
          <button
            onClick={() => setSelectedType('all')}
            className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              selectedType === 'all'
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            All Relationships ({entities.length})
          </button>
          {availableTypes.map(t => {
            const count = entities.filter(e => e.relationship_type === t).length;
            const isSelected = selectedType === t;
            return (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                <ArrowRightLeft className="w-3 h-3" />
                <span>{t}</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Entity Cards List */}
      <div className="space-y-4">
        {filteredEntities.map((entity) => {
          const isExpanded = expandedEntities[entity.entity_id] !== false; // Default expanded
          
          return (
            <div 
              key={entity.entity_id}
              className={`bg-white rounded-xl border transition-all shadow-xs overflow-hidden ${
                entity.is_cross_file ? 'border-blue-200 hover:border-blue-300 ring-1 ring-blue-500/10' : 'border-slate-200'
              }`}
            >
              {/* Entity Header */}
              <div 
                onClick={() => toggleExpand(entity.entity_id)}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/70 transition-colors"
              >
                <div className="flex items-start sm:items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xs flex items-center justify-center shadow-xs shrink-0">
                    {entity.entity_id}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm sm:text-base font-bold text-slate-900">
                        {entity.display_name}
                      </h4>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-indigo-50 text-indigo-700 border border-indigo-200">
                        <ArrowRightLeft className="w-3 h-3 text-indigo-600" />
                        {entity.relationship_type}
                      </span>
                      {getConfidenceBadge(entity.confidence_score)}
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500 flex-wrap">
                      <span className="font-semibold text-slate-700">Primary Key:</span>
                      <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-slate-800 border border-slate-200">
                        {entity.primary_match_key}
                      </span>
                      <span>•</span>
                      <span className="text-slate-600">{entity.match_method}</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-4 self-end sm:self-center shrink-0">
                  {/* File tags */}
                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    {entity.files_involved.map((fname, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 max-w-[150px] truncate"
                        title={fname}
                      >
                        <FileText className="w-3 h-3 text-slate-500 shrink-0" />
                        <span className="truncate">{fname}</span>
                      </span>
                    ))}
                    <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                      {entity.records_count} records
                    </span>
                  </div>

                  <button 
                    type="button"
                    className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100"
                  >
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Collapsible Records Breakdown Table / Cards */}
              {isExpanded && (
                <div className="border-t border-slate-100 bg-slate-50/50 p-4 sm:p-5 space-y-3">
                  {/* Connected Records Grid */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {entity.records.map((rec, rIdx) => {
                      const domain = rec.entity_domain || 'dataset';
                      const entries = Object.entries(rec.record).filter(([k]) => k !== 'entity_id');
                      
                      return (
                        <div key={rIdx} className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-2xs space-y-2">
                          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 truncate">
                              {getDomainIcon(domain)}
                              <span className="truncate max-w-[140px]" title={rec.filename}>{rec.filename}</span>
                            </div>
                            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                              Row #{rec.row_index}
                            </span>
                          </div>

                          <div className="space-y-1 text-xs max-h-48 overflow-y-auto pr-1">
                            {entries.slice(0, 8).map(([k, v]) => (
                              <div key={k} className="flex items-baseline justify-between gap-2">
                                <span className="text-slate-500 font-medium capitalize truncate max-w-[110px]">
                                  {k.replace(/_/g, ' ')}:
                                </span>
                                <span className="text-slate-900 font-mono text-[11px] font-semibold text-right truncate max-w-[150px]" title={String(v)}>
                                  {String(v)}
                                </span>
                              </div>
                            ))}
                            {entries.length > 8 && (
                              <div className="text-[10px] text-slate-400 italic pt-1 text-right">
                                + {entries.length - 8} more fields
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}

        {filteredEntities.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-xs text-slate-500">
            No entities match your current search query "{searchTerm}".
          </div>
        )}
      </div>
    </div>
  );
};
