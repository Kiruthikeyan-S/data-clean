import React, { useState, useMemo } from 'react';
import { 
  Users, 
  ShieldCheck, 
  Search, 
  ChevronDown, 
  ChevronUp, 
  FileText, 
  Link2,
  Building2,
  Package,
  User,
  CreditCard,
  Car,
  GraduationCap,
  Briefcase
} from 'lucide-react';
import { SameEntityMatch } from '../types';

interface EntityMatchesViewProps {
  entityMatches: SameEntityMatch[];
}

export const EntityMatchesView: React.FC<EntityMatchesViewProps> = ({ entityMatches }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState<string>('all');
  const [expandedMatches, setExpandedMatches] = useState<Record<string, boolean>>({});

  const toggleExpand = (matchId: string) => {
    setExpandedMatches(prev => ({
      ...prev,
      [matchId]: !prev[matchId]
    }));
  };

  const expandAll = () => {
    const allExpanded: Record<string, boolean> = {};
    entityMatches.forEach(m => {
      allExpanded[m.match_id] = true;
    });
    setExpandedMatches(allExpanded);
  };

  const collapseAll = () => {
    setExpandedMatches({});
  };

  const availableTypes = useMemo(() => {
    const types = new Set<string>();
    entityMatches.forEach(m => {
      if (m.entity_type) types.add(m.entity_type);
    });
    return Array.from(types);
  }, [entityMatches]);

  const filteredMatches = useMemo(() => {
    return entityMatches.filter(m => {
      const matchesType = selectedType === 'all' || m.entity_type === selectedType;
      if (!matchesType) return false;

      if (!searchTerm.trim()) return true;
      const term = searchTerm.toLowerCase();

      const inId = m.match_id.toLowerCase().includes(term);
      const inName = m.display_name.toLowerCase().includes(term);
      const inKey = m.primary_key.toLowerCase().includes(term);
      const inFiles = m.files_involved.some(f => f.toLowerCase().includes(term));
      const inRecords = m.records.some(r =>
        Object.values(r.record).some(v => String(v).toLowerCase().includes(term))
      );

      return inId || inName || inKey || inFiles || inRecords;
    });
  }, [entityMatches, selectedType, searchTerm]);

  const getDomainIcon = (domain: string) => {
    switch (domain?.toLowerCase()) {
      case 'customer':
        return <User className="w-4 h-4 text-blue-600" />;
      case 'store':
        return <Building2 className="w-4 h-4 text-emerald-600" />;
      case 'product':
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

  if (!entityMatches || entityMatches.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 p-8 text-center space-y-3 shadow-xs">
        <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center justify-center mx-auto text-slate-400">
          <Users className="w-6 h-6" />
        </div>
        <h3 className="text-base font-bold text-slate-800">No Same-Entity Duplicates Detected</h3>
        <p className="text-xs text-slate-500 max-w-md mx-auto">
          All records within their respective entity types (Customer, Store, Product) appear to be unique without cross-file duplicate identity matches.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-white rounded-2xl p-6 border border-slate-200 shadow-xs">
        <div className="space-y-1.5">
          <h2 className="text-xl sm:text-2xl font-black tracking-tight text-slate-900 flex items-center gap-2.5">
            <Users className="w-6 h-6 text-blue-600" />
            <span>Same-Entity Resolution & Identity Matches</span>
          </h2>
          <p className="text-xs sm:text-sm text-slate-600 max-w-2xl leading-relaxed">
            Identifies when records from different files represent the <strong>exact same real-world entity</strong> (Customer ↔ Customer, Store ↔ Store, Product ↔ Product). Different entity types are never merged.
          </p>
        </div>

        {/* Metrics */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mt-6 pt-5 border-t border-slate-100">
          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Identity Clusters</span>
            <div className="text-2xl font-black text-slate-900 mt-1 flex items-baseline gap-1.5">
              <span>{entityMatches.length}</span>
              <span className="text-[10px] font-normal text-blue-600 font-bold">unique entities</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Total Duplicate Rows</span>
            <div className="text-2xl font-black text-emerald-700 mt-1 flex items-baseline gap-1.5">
              <span>{entityMatches.reduce((acc, m) => acc + m.records_count, 0)}</span>
              <span className="text-[10px] font-normal text-emerald-600 font-bold">matched rows</span>
            </div>
          </div>

          <div className="bg-slate-50/80 rounded-xl p-3.5 border border-slate-200/70">
            <span className="text-[11px] font-semibold text-slate-500 block">Entity Types</span>
            <div className="text-2xl font-black text-indigo-700 mt-1 flex items-baseline gap-1.5">
              <span>{availableTypes.length}</span>
              <span className="text-[10px] font-normal text-indigo-600 font-bold">domains resolved</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="relative flex-1 max-w-md">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by Identity ID, Name, Phone, Email, or File..."
              className="w-full pl-9 pr-4 py-2 text-xs rounded-lg border border-slate-300 bg-slate-50 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-600 transition-all text-slate-800"
            />
          </div>

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

        {/* Entity Type Filter */}
        <div className="flex items-center gap-1.5 flex-wrap pt-2 border-t border-slate-100">
          <span className="text-[11px] font-bold text-slate-500 mr-1">Entity Domain:</span>
          <button
            onClick={() => setSelectedType('all')}
            className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all ${
              selectedType === 'all'
                ? 'bg-blue-600 text-white border-blue-600 shadow-xs'
                : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
            }`}
          >
            All Entities ({entityMatches.length})
          </button>
          {availableTypes.map(t => {
            const count = entityMatches.filter(m => m.entity_type === t).length;
            const isSelected = selectedType === t;
            return (
              <button
                key={t}
                onClick={() => setSelectedType(t)}
                className={`px-3 py-1 rounded-full text-xs font-semibold border transition-all flex items-center gap-1.5 capitalize ${
                  isSelected
                    ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs'
                    : 'bg-slate-50 hover:bg-slate-100 text-slate-700 border-slate-200'
                }`}
              >
                {getDomainIcon(t)}
                <span>{t} Matches</span>
                <span className={`text-[10px] px-1.5 py-0.2 rounded-full ${isSelected ? 'bg-white/20 text-white' : 'bg-slate-200 text-slate-600'}`}>
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* Matches List */}
      <div className="space-y-4">
        {filteredMatches.map(m => {
          const isExpanded = expandedMatches[m.match_id] !== false;

          return (
            <div
              key={m.match_id}
              className="bg-white rounded-xl border border-slate-200 hover:border-blue-300 transition-all shadow-xs overflow-hidden"
            >
              <div
                onClick={() => toggleExpand(m.match_id)}
                className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4 cursor-pointer hover:bg-slate-50/70 transition-colors"
              >
                <div className="flex items-start sm:items-center gap-3.5">
                  <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-700 text-white font-black text-xs flex items-center justify-center shadow-xs shrink-0">
                    {m.match_id.split('-').pop() || '001'}
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 flex-wrap">
                      <h4 className="text-sm sm:text-base font-bold text-slate-900">
                        {m.display_name}
                      </h4>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-blue-50 text-blue-700 border border-blue-200 capitalize">
                        {getDomainIcon(m.entity_type)}
                        {m.entity_type} Entity
                      </span>
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <ShieldCheck className="w-3 h-3 text-emerald-600" />
                        {m.confidence_percent} Match
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-xs text-slate-500 flex-wrap">
                      <span className="font-semibold text-slate-700">Identity Key:</span>
                      <span className="px-2 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-slate-800 border border-slate-200">
                        {m.primary_key}
                      </span>
                      <span>•</span>
                      <span>{m.records_count} matching records</span>
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <div className="flex items-center gap-1.5 flex-wrap justify-end">
                    {m.files_involved.map((fname, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200 max-w-[150px] truncate"
                        title={fname}
                      >
                        <FileText className="w-3 h-3 text-slate-500 shrink-0" />
                        <span className="truncate">{fname}</span>
                      </span>
                    ))}
                  </div>
                  <button type="button" className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100">
                    {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="border-t border-slate-100 bg-slate-50/50 p-4 sm:p-5 space-y-4">
                  {m.matched_keys && m.matched_keys.length > 0 && (
                    <div className="flex items-center gap-2 flex-wrap text-xs bg-white p-2.5 rounded-lg border border-slate-200">
                      <span className="font-bold text-slate-700 flex items-center gap-1">
                        <Link2 className="w-3.5 h-3.5 text-blue-600" /> Shared Keys:
                      </span>
                      {m.matched_keys.map((mk, idx) => (
                        <span key={idx} className="px-2 py-0.5 rounded bg-blue-50 text-blue-800 font-mono text-[11px] font-medium border border-blue-200">
                          {mk}
                        </span>
                      ))}
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {m.records.map((rec, rIdx) => {
                      const entries = Object.entries(rec.record).filter(([k]) => k !== 'entity_id');
                      return (
                        <div key={rIdx} className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-2xs space-y-2">
                          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                            <div className="flex items-center gap-1.5 text-xs font-bold text-slate-800 truncate">
                              <FileText className="w-3.5 h-3.5 text-slate-500" />
                              <span className="truncate max-w-[140px]" title={rec.filename}>{rec.filename}</span>
                            </div>
                            <span className="text-[10px] font-semibold text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded">
                              Row #{rec.row_index}
                            </span>
                          </div>

                          <div className="space-y-1 text-xs max-h-44 overflow-y-auto pr-1">
                            {entries.slice(0, 7).map(([k, v]) => (
                              <div key={k} className="flex items-baseline justify-between gap-2">
                                <span className="text-slate-500 font-medium capitalize truncate max-w-[110px]">
                                  {k.replace(/_/g, ' ')}:
                                </span>
                                <span className="text-slate-900 font-mono text-[11px] font-semibold text-right truncate max-w-[150px]" title={String(v)}>
                                  {String(v)}
                                </span>
                              </div>
                            ))}
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

        {filteredMatches.length === 0 && (
          <div className="bg-white rounded-xl border border-slate-200 p-6 text-center text-xs text-slate-500">
            No identity matches found for search query "{searchTerm}".
          </div>
        )}
      </div>
    </div>
  );
};
