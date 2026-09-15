import React from 'react';
import { 
  TrendingUp, 
  Receipt, 
  DollarSign, 
  Package, 
  Users, 
  Store, 
  MapPin, 
  Mail, 
  Tag, 
  Warehouse, 
  Building2, 
  Sparkles, 
  CheckCircle2, 
  AlertTriangle, 
  Info,
  Layers,
  BarChart3
} from 'lucide-react';
import { BusinessAnalysisReport } from '../types';

interface BusinessAnalysisInspectorProps {
  analysis?: BusinessAnalysisReport;
}

export const BusinessAnalysisInspector: React.FC<BusinessAnalysisInspectorProps> = ({ analysis }) => {
  if (!analysis || (!analysis.metrics.length && !analysis.insights.length)) {
    return null;
  }

  const getMetricIcon = (iconName: string) => {
    switch (iconName.toLowerCase()) {
      case 'dollar':
        return <DollarSign className="w-5 h-5 text-emerald-600" />;
      case 'receipt':
        return <Receipt className="w-5 h-5 text-amber-600" />;
      case 'package':
      case 'inventory':
        return <Package className="w-5 h-5 text-indigo-600" />;
      case 'users':
        return <Users className="w-5 h-5 text-purple-600" />;
      case 'store':
        return <Store className="w-5 h-5 text-blue-600" />;
      case 'map_pin':
        return <MapPin className="w-5 h-5 text-rose-600" />;
      case 'mail':
        return <Mail className="w-5 h-5 text-sky-600" />;
      case 'tag':
        return <Tag className="w-5 h-5 text-teal-600" />;
      case 'warehouse':
        return <Warehouse className="w-5 h-5 text-orange-600" />;
      case 'building':
        return <Building2 className="w-5 h-5 text-slate-600" />;
      default:
        return <TrendingUp className="w-5 h-5 text-blue-600" />;
    }
  };

  const getInsightBadgeStyle = (type?: string) => {
    switch (type) {
      case 'positive':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'warning':
        return 'bg-amber-50 text-amber-800 border-amber-200';
      default:
        return 'bg-blue-50 text-blue-800 border-blue-200';
    }
  };

  const getInsightIcon = (type?: string) => {
    switch (type) {
      case 'positive':
        return <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />;
      case 'warning':
        return <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />;
      default:
        return <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden space-y-5 p-5 sm:p-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-600">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Business Analysis & Intelligence</span>
              <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-200 capitalize">
                {analysis.entity_type} Intelligence
              </span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">{analysis.headline}</p>
          </div>
        </div>

        <div className="flex items-center gap-1.5 text-xs text-slate-500 font-medium bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200 w-fit">
          <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
          <span>Automated KPI & Pattern Extraction</span>
        </div>
      </div>

      {/* KPI Cards Grid */}
      {analysis.metrics && analysis.metrics.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3.5">
          {analysis.metrics.map((metric, idx) => (
            <div 
              key={idx}
              className="p-4 rounded-xl bg-slate-50/70 border border-slate-200/80 hover:bg-white hover:border-slate-300 hover:shadow-2xs transition-all flex flex-col justify-between"
            >
              <div className="flex items-center justify-between gap-2 mb-2">
                <span className="text-xs font-semibold text-slate-600 truncate">{metric.label}</span>
                <div className="p-1.5 rounded-md bg-white border border-slate-200/60 shadow-2xs">
                  {getMetricIcon(metric.icon)}
                </div>
              </div>
              <div>
                <div className="text-xl font-extrabold text-slate-900 tracking-tight">{metric.value}</div>
                {metric.subtext && (
                  <div className="text-[11px] text-slate-500 font-medium mt-1 truncate">{metric.subtext}</div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Actionable Executive Insights */}
      {analysis.insights && analysis.insights.length > 0 && (
        <div className="space-y-3 pt-2">
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-slate-500" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-slate-600">
              Key Business Insights & Patterns ({analysis.insights.length})
            </h3>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {analysis.insights.map((insight, idx) => (
              <div 
                key={idx}
                className="p-3.5 rounded-lg border border-slate-200/80 bg-white hover:border-slate-300 transition-all flex items-start gap-3"
              >
                {getInsightIcon(insight.type)}
                <div className="space-y-1 flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="text-xs font-bold text-slate-800">{insight.title}</span>
                    {insight.badge && (
                      <span className={`text-[10px] font-semibold px-2 py-0.2 rounded-full border ${getInsightBadgeStyle(insight.type)}`}>
                        {insight.badge}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-600 leading-relaxed">{insight.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
