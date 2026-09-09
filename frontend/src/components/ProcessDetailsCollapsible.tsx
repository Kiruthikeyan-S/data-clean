import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Activity, CheckCircle2, AlertTriangle, Clock } from 'lucide-react';
import { StepStatus, ProcessSummary } from '../types';

interface ProcessDetailsCollapsibleProps {
  steps: StepStatus[];
  summary: ProcessSummary;
}

export const ProcessDetailsCollapsible: React.FC<ProcessDetailsCollapsibleProps> = ({ steps, summary }) => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-5 py-3.5 flex items-center justify-between text-left hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-2.5">
          <Activity className="w-4 h-4 text-slate-500" />
          <span className="text-sm font-semibold text-slate-900">Processing Details</span>
          <span className="text-xs text-slate-500 font-normal flex items-center gap-1">
            <Clock className="w-3 h-3 text-slate-400" />
            {summary.processing_time_ms} ms
          </span>
        </div>
        {isOpen ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
      </button>

      {isOpen && (
        <div className="px-5 pb-5 pt-3 border-t border-slate-100">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {steps.map((step, idx) => (
              <div key={step.step_id || idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200/70 flex items-start gap-2.5">
                {step.status === 'failed' ? (
                  <AlertTriangle className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0 mt-0.5" />
                )}
                <div className="min-w-0">
                  <span className="font-semibold text-slate-800">{step.name}</span>
                  {step.message && (
                    <p className="text-[11px] text-slate-500 mt-0.5 truncate">{step.message}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
