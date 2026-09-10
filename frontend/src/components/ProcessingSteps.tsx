import React from 'react';
import {
  Check,
  Loader2,
  AlertCircle,
  Circle,
  Cpu
} from 'lucide-react';
import { StepStatus } from '../types';

interface ProcessingStepsProps {
  steps: StepStatus[];
  currentStepIndex?: number;
  progressPercent?: number;
  elapsedSeconds?: number;
}

export const PIPELINE_STAGES = [
  { id: 'file_received', name: 'File received & integrity check', desc: 'Verifying file size, encoding and mime headers' },
  { id: 'file_type_detected', name: 'File type detection & classification', desc: 'Detecting format (CSV, Excel, Image OCR, PDF, DOCX, TXT, Email)' },
  { id: 'data_extracted', name: 'OCR & raw content extraction', desc: 'Parsing structural content and running OCR text extraction' },
  { id: 'data_cleaned', name: 'Noise removal & text sanitization', desc: 'Stripping control characters, normalizing Unicode and whitespace' },
  { id: 'fields_identified', name: 'AI semantic schema & entity extraction', desc: 'Understanding document content with AI LLM intelligence' },
  { id: 'data_normalized', name: 'Data type & format standardization', desc: 'Standardizing dates to ISO 8601, names to Title Case, cleaning currency' },
  { id: 'quality_audited', name: '6-Dimension data quality diagnostic audit', desc: 'Auditing missing values, duplicates, wrong types, invalid syntax, outliers' },
  { id: 'visualizations_generated', name: 'Intelligent diagram & Matplotlib plotting', desc: 'Generating Pie/Donut charts, Bar distributions & scientific plots' },
  { id: 'data_validated', name: 'Final schema validation & delivery', desc: 'Assembling validated structured records for export' },
];

export const ProcessingSteps: React.FC<ProcessingStepsProps> = ({
  steps,
  currentStepIndex = 0,
  progressPercent = 0,
  elapsedSeconds = 0
}) => {
  const displaySteps = PIPELINE_STAGES.map((stage, idx) => {
    const existing = steps.find(s => s.step_id === stage.id);
    if (existing) {
      return { ...stage, ...existing };
    }
    
    if (idx < currentStepIndex) {
      return { ...stage, step_id: stage.id, status: 'completed' as const };
    } else if (idx === currentStepIndex) {
      return { ...stage, step_id: stage.id, status: 'in_progress' as const };
    } else {
      return { ...stage, step_id: stage.id, status: 'pending' as const };
    }
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 max-w-xl mx-auto shadow-sm">
      {/* Header with Progress Bar */}
      <div className="mb-6">
        <div className="flex items-center justify-between gap-2 mb-2">
          <div>
            <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <span>Deep Data Cleansing & Analysis</span>
              <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-100">
                <Cpu className="w-3 h-3 animate-pulse" />
                AI Engine Active
              </span>
            </h2>
            <p className="text-xs text-slate-500 mt-0.5 font-medium">
              Executing comprehensive 10-second data processing & auditing pipeline
            </p>
          </div>
          <div className="text-right flex-shrink-0">
            <span className="text-xs font-mono font-bold text-blue-600">
              {Math.min(100, Math.round(progressPercent))}%
            </span>
            <p className="text-[10px] text-slate-400 font-mono">
              {elapsedSeconds.toFixed(1)}s / 10.0s
            </p>
          </div>
        </div>

        {/* Progress Bar Track */}
        <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
          <div
            className="h-full bg-blue-600 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${Math.min(100, Math.max(progressPercent, 4))}%` }}
          />
        </div>
      </div>

      {/* Steps List */}
      <div className="space-y-3.5">
        {displaySteps.map((step, index) => {
          const isCompleted = step.status === 'completed';
          const isInProgress = step.status === 'in_progress';
          const isFailed = step.status === 'failed';
          const isPending = step.status === 'pending';

          return (
            <div
              key={step.id || index}
              className={`flex items-start gap-3 p-2.5 rounded-lg transition-all ${
                isInProgress
                  ? 'bg-blue-50/60 border border-blue-200/80 shadow-2xs'
                  : 'border border-transparent'
              }`}
            >
              {/* Status Indicator Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {isCompleted && (
                  <div className="w-5 h-5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                )}
                {isInProgress && (
                  <div className="w-5 h-5 rounded-full bg-blue-100 text-blue-600 border border-blue-300 flex items-center justify-center">
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  </div>
                )}
                {isFailed && (
                  <div className="w-5 h-5 rounded-full bg-red-50 text-red-600 border border-red-200 flex items-center justify-center">
                    <AlertCircle className="w-3.5 h-3.5" />
                  </div>
                )}
                {isPending && (
                  <div className="w-5 h-5 rounded-full bg-slate-100 text-slate-400 border border-slate-200 flex items-center justify-center">
                    <Circle className="w-2 h-2" />
                  </div>
                )}
              </div>

              {/* Step Info */}
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-2">
                  <p className={`text-xs font-semibold ${
                    isCompleted ? 'text-slate-800' :
                    isInProgress ? 'text-blue-700 font-bold' :
                    isFailed ? 'text-red-600' :
                    'text-slate-400'
                  }`}>
                    {step.name}
                  </p>
                  {isInProgress && (
                    <span className="text-[10px] uppercase font-bold text-blue-600 animate-pulse tracking-wide">
                      Processing...
                    </span>
                  )}
                  {isCompleted && (
                    <span className="text-[10px] font-semibold text-emerald-600">
                      Done
                    </span>
                  )}
                </div>
                <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">
                  {step.message || step.desc}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
