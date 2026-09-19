import React, { useState, useMemo } from 'react';
import { 
  Network, 
  ShieldCheck, 
  Search, 
  FileSpreadsheet, 
  FileCode, 
  ArrowRight,
  Building2,
  Package,
  User,
  CreditCard,
  Car,
  GraduationCap,
  Briefcase,
  FileText,
  CheckCircle2,
  SlidersHorizontal,
  Layers
} from 'lucide-react';
import { RelationshipIndexData, RelationshipEdge } from '../types';
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
  const [confidenceFilter, setConfidenceFilter] = useState<'all' | 'high' | 'medium' | 'review'>('all');
  const [methodFilter, setMethodFilter] = useState<string>('all');

  const relationships: RelationshipEdge[] = relationshipIndex?.relationships || [];
  const summary = relationshipIndex?.summary || {
    files_uploaded: 0,
    records_scanned: 0,
    relationships_found: 0,
    records_connected: 0,
    average_confidence: 0.95
  };

  const getRelationshipTypeLabel = (rel: RelationshipEdge) => {
    const src = rel.source.entity_type;
    const tgt = rel.target.entity_type;
    return `${src.charAt(0).toUpperCase() + src.slice(1)} ↔ ${tgt.charAt(0).toUpperCase() + tgt.slice(1)}`;
  };

  const availableRelTypes = useMemo(() => {
    const types = new Set<string>();
    relationships.forEach(r => {
      types.add(getRelationshipTypeLabel(r));
    });
    return Array.from(types);
  }, [relationships]);

  const filteredRelationships = useMemo(() => {
    return relationships.filter(rel => {
      // 1. Filter by relationship type
      const relTypeLabel = getRelationshipTypeLabel(rel);
      if (selectedType !== 'all' && relTypeLabel !== selectedType) return false;

      // 2. Filter by confidence
      if (confidenceFilter === 'high' && rel.confidence < 0.90) return false;
      if (confidenceFilter === 'medium' && (rel.confidence < 0.75 || rel.confidence >= 0.90)) return false;
      if (confidenceFilter === 'review' && rel.confidence >= 0.75) return false;

      // 3. Filter by match method
      if (methodFilter !== 'all') {
        const m = rel.match_method.toLowerCase();
        if (methodFilter === 'exact' && !m.includes('exact')) return false;
        if (methodFilter === 'normalized' && !m.includes('normalized')) return false;
        if (methodFilter === 'fuzzy' && !m.includes('fuzzy') && !m.includes('similarity')) return false;
      }

      // 4. Search query
      if (!searchTerm.trim()) return true;
      const term = searchTerm.toLowerCase();

      const inId = rel.relationship_id.toLowerCase().includes(term);
      const inSrc = rel.source.name.toLowerCase().includes(term) || rel.source.entity_id.toLowerCase().includes(term);
      const inTgt = rel.target.name.toLowerCase().includes(term) || rel.target.entity_id.toLowerCase().includes(term);
      const inType = rel.relationship_type.toLowerCase().includes(term);
      const inFiles = rel.source_files.some(f => f.toLowerCase().includes(term));
      const inEvidence = (rel.evidence || []).some(e => e.toLowerCase().includes(term));

      return inId || inSrc || inTgt || inType || inFiles || inEvidence;
    });
  }, [relationships, selectedType, confidenceFilter, methodFilter, searchTerm]);

  const getEntityIcon = (type: string) => {
    switch (type?.toLowerCase()) {
      case 'customer':
        return <User className="w-4 h-4 text-blue-600" />;
      case 'store':
        return <Building2 className="w-4 h-4 text-emerald-600" />;
      case 'product':
      case 'item':
        return <Package className="w-4 h-4 text-violet-600" />;
      case 'transaction':
        return <CreditCard className="w-4 h-4 text-amber-600" />;
      case 'car':
        return <Car className="w-4 h-4 text-amber-600" />;
      case 'student':
        return <GraduationCap className="w-4 h-4 text-indigo-600" />;
      case 'employee':
        return <Briefcase className="w-4 h-4 text-slate-600" />;
      default:
        return <FileText className="w-4 h-4 text-slate-500" />;
    }
  };

  const getConfidenceBadge = (score: number) => {
    const percent = Math.round(score * 100);
    if (score >= 0.90) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
          <ShieldCheck className="w-3 h-3 text-emerald-600" />
          {percent}% High Confidence
        </span>
      );
    } else if (score >= 0.75) {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
          <ShieldCheck className="w-3 h-3 text-blue-600" />
          {percent}% Medium Confidence
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-amber-50 text-amber-700 border border-amber-200">
          <ShieldCheck className="w-3 h-3 text-amber-600" />
          {percent}% Review
        </span>
      );
    }
  };

  const getVerbBadge = (relType: string) => {
    const v = relType.toUpperCase().replace(/_/g, ' ');
    return (
      <div className="flex flex-col items-center justify-center gap-1 px-3 py-1 bg-slate-100/90 rounded-lg border border-slate-200 text-slate-700 shadow-2xs">
        <span className="text-[10px] font-black tracking-wider text-slate-800 flex items-center gap-1">
          {v}
        </span>
        <ArrowRight className="w-3.5 h-3.5 text-blue-600" />
      </div>
    );
  };

  if (!relationshipIndex || relationships.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-3 shadow-xs">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <Network className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">No Cross-Entity Relationships Detected</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          The uploaded datasets do not contain common transaction bridges or shared identity keys between different entities.
          Upload related Customer, Store, Product, or Transaction files to discover relationship edges.
        </p>
      </div>
    );
  }

  const avgConfidence = Math.round((summary.average_confidence || 0.95) * 100);

  return (
    <div className="space-y-6">
      {/* Top Banner: Metrics & Batch Export (Clean Light Theme) */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-1.5">
            <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2.5">
              <Network className="w-6 h-6 text-blue-600" />
              <span>Cross-Entity Relationship Network</span>
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
              Discovered distinct business relationship edges linking Customer, Store, Product, and Transaction entities 
              without merging different domains into a single cluster.
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

        {/* 5 Metric Cards Ribbon */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 mt-6 pt-5 border-t border-slate-100">
          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Files Uploaded</span>
            <div className="text-2xl font-black text-slate-900 mt-1 flex items-baseline gap-1.5">
              <span>{summary.files_uploaded}</span>
              <span className="text-[10px] font-normal text-slate-500">datasets</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Records Scanned</span>
            <div className="text-2xl font-black text-slate-900 mt-1 flex items-baseline gap-1.5">
              <span>{summary.records_scanned}</span>
              <span className="text-[10px] font-normal text-slate-500">rows</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Relationships Found</span>
            <div className="text-2xl font-black text-blue-600 mt-1 flex items-baseline gap-1.5">
              <span>{summary.relationships_found}</span>
              <span className="text-[10px] font-normal text-blue-600 font-bold">edges</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Records Connected</span>
            <div className="text-2xl font-black text-emerald-700 mt-1 flex items-baseline gap-1.5">
              <span>{summary.records_connected}</span>
              <span className="text-[10px] font-normal text-emerald-600 font-bold">entities</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Average Confidence</span>
            <div className="text-2xl font-black text-indigo-700 mt-1 flex items-baseline gap-1.5">
              <span>{avgConfidence}%</span>
              <span className="text-[10px] font-normal text-indigo-600 font-bold">accuracy</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-4">
        {/* Search Input */}
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by ID, Name, Action, File, or Evidence..."
            className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-slate-800"
          />
        </div>

        {/* Filter Controls Grid */}
        <div className="space-y-3 pt-2 border-t border-slate-100 text-xs">
          {/* 1. Relationship Type Filter */}
          <div className="flex items-center gap-1.5 flex-wrap">
            <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-blue-600" /> Relationship Type:
            </span>
            <button
              onClick={() => setSelectedType('all')}
              className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
                selectedType === 'all'
                  ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                  : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
              }`}
            >
              All Types ({relationships.length})
            </button>
            {availableRelTypes.map(t => {
              const count = relationships.filter(r => getRelationshipTypeLabel(r) === t).length;
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
                  <span>{t}</span>
                  <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-600'}`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>

          {/* 2. Confidence & Match Method Filters */}
          <div className="flex items-center justify-between flex-wrap gap-3 pt-2 border-t border-slate-100">
            {/* Confidence Filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> Confidence:
              </span>
              <button
                onClick={() => setConfidenceFilter('all')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  confidenceFilter === 'all' ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setConfidenceFilter('high')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  confidenceFilter === 'high' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                High (90%+)
              </button>
              <button
                onClick={() => setConfidenceFilter('medium')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  confidenceFilter === 'medium' ? 'bg-blue-600 text-white border-blue-600' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                Medium (75–89%)
              </button>
              <button
                onClick={() => setConfidenceFilter('review')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  confidenceFilter === 'review' ? 'bg-amber-600 text-white border-amber-600' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                Review (&lt;75%)
              </button>
            </div>

            {/* Match Method Filter */}
            <div className="flex items-center gap-1.5 flex-wrap">
              <span className="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1">
                <SlidersHorizontal className="w-3.5 h-3.5 text-slate-500" /> Match Method:
              </span>
              <button
                onClick={() => setMethodFilter('all')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  methodFilter === 'all' ? 'bg-slate-800 text-white border-slate-800' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setMethodFilter('exact')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  methodFilter === 'exact' ? 'bg-slate-800 text-white border-slate-800' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                Exact
              </button>
              <button
                onClick={() => setMethodFilter('normalized')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  methodFilter === 'normalized' ? 'bg-slate-800 text-white border-slate-800' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                Normalized
              </button>
              <button
                onClick={() => setMethodFilter('fuzzy')}
                className={`px-2.5 py-0.5 rounded-md text-[11px] font-semibold border transition-all ${
                  methodFilter === 'fuzzy' ? 'bg-slate-800 text-white border-slate-800' : 'bg-slate-50 text-slate-700 border-slate-200'
                }`}
              >
                Fuzzy
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Individual Relationship Cards Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filteredRelationships.map((rel) => {
          const srcIcon = getEntityIcon(rel.source.entity_type);
          const tgtIcon = getEntityIcon(rel.target.entity_type);

          return (
            <div
              key={rel.relationship_id}
              className="bg-white rounded-xl border border-slate-200 hover:border-blue-300 hover:shadow-xs transition-all p-4 sm:p-5 space-y-3.5"
            >
              {/* Header: ID, Badge, Method */}
              <div className="flex items-center justify-between pb-2.5 border-b border-slate-100 flex-wrap gap-2">
                <div className="flex items-center gap-2">
                  <span className="w-8 h-8 rounded-lg bg-blue-50 text-blue-700 font-mono font-bold text-xs flex items-center justify-center border border-blue-200">
                    {rel.relationship_id.replace('REL-', '#')}
                  </span>
                  <span className="text-xs font-bold text-slate-800 font-mono">
                    {rel.relationship_id}
                  </span>
                  <span className="text-[11px] px-2 py-0.5 rounded bg-slate-100 text-slate-700 font-medium">
                    {rel.match_method}
                  </span>
                </div>

                {getConfidenceBadge(rel.confidence)}
              </div>

              {/* Edge Visualizer: Source Entity ──[ Action ]──→ Target Entity */}
              <div className="grid grid-cols-1 md:grid-cols-11 items-center gap-3 bg-slate-50/70 p-3.5 rounded-xl border border-slate-200/70">
                {/* Source Entity Node */}
                <div className="md:col-span-5 flex items-center gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <div className="w-9 h-9 rounded-lg bg-blue-50 flex items-center justify-center shrink-0">
                    {srcIcon}
                  </div>
                  <div className="space-y-0.5 min-w-0">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                      {rel.source.entity_type}
                    </span>
                    <h4 className="text-xs sm:text-sm font-bold text-slate-900 truncate" title={rel.source.name}>
                      {rel.source.name}
                    </h4>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded inline-block">
                      {rel.source.entity_id}
                    </span>
                  </div>
                </div>

                {/* Directed Verb / Action */}
                <div className="md:col-span-1 flex justify-center py-1 md:py-0">
                  {getVerbBadge(rel.relationship_type)}
                </div>

                {/* Target Entity Node */}
                <div className="md:col-span-5 flex items-center gap-3 bg-white p-3 rounded-lg border border-slate-200 shadow-2xs">
                  <div className="w-9 h-9 rounded-lg bg-indigo-50 flex items-center justify-center shrink-0">
                    {tgtIcon}
                  </div>
                  <div className="space-y-0.5 min-w-0">
                    <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">
                      {rel.target.entity_type}
                    </span>
                    <h4 className="text-xs sm:text-sm font-bold text-slate-900 truncate" title={rel.target.name}>
                      {rel.target.name}
                    </h4>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-100 px-1.5 py-0.2 rounded inline-block">
                      {rel.target.entity_id}
                    </span>
                  </div>
                </div>
              </div>

              {/* Evidence and Files Footer */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-1 text-xs">
                {/* Evidence Badges */}
                <div className="flex items-center gap-1.5 flex-wrap">
                  <span className="font-bold text-slate-600 text-[11px] mr-1">Evidence:</span>
                  {rel.evidence && rel.evidence.map((ev, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 text-[11px] font-medium border border-emerald-200"
                    >
                      <CheckCircle2 className="w-3 h-3 text-emerald-600 shrink-0" />
                      <span>{ev.replace('✓ ', '')}</span>
                    </span>
                  ))}
                </div>

                {/* Source Files */}
                <div className="flex items-center gap-1.5 flex-wrap justify-end">
                  <span className="text-slate-500 text-[11px]">Files:</span>
                  {rel.source_files.map((fname, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 text-slate-700 text-[11px] font-medium border border-slate-200 max-w-[150px] truncate"
                      title={fname}
                    >
                      <FileText className="w-3 h-3 text-slate-500 shrink-0" />
                      <span className="truncate">{fname}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          );
        })}

        {filteredRelationships.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-8 text-center text-xs text-slate-500">
            No relationships match your current filters or search query "{searchTerm}".
          </div>
        )}
      </div>
    </div>
  );
};
