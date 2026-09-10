import React from 'react';
import { Check, Loader2, AlertCircle, Circle } from 'lucide-react';
import { StepStatus } from '../types';

interface ProcessingStepsProps {
  steps: StepStatus[];
  currentStepIndex?: number;
}

const DEFAULT_STAGES = [
  { id: 'file_received', name: 'File received' },
  { id: 'file_type_detected', name: 'File type detected' },
  { id: 'data_classified', name: 'Data classified' },
  { id: 'data_extracted', name: 'Data extracted' },
  { id: 'data_cleaned', name: 'Data cleaned' },
  { id: 'data_normalized', name: 'Data normalized' },
  { id: 'fields_identified', name: 'Fields identified' },
  { id: 'data_validated', name: 'Data validated' },
];

export const ProcessingSteps: React.FC<ProcessingStepsProps> = ({ steps, currentStepIndex = 0 }) => {
  // Map or merge default stages with actual response steps
  const displaySteps = DEFAULT_STAGES.map((stage, idx) => {
    const existing = steps.find(s => s.step_id === stage.id);
    if (existing) {
      return existing;
    }
    
    // Fallback based on simulation/progress index
    if (idx < currentStepIndex) {
      return { step_id: stage.id, name: stage.name, status: 'completed' as const };
    } else if (idx === currentStepIndex) {
      return { step_id: stage.id, name: stage.name, status: 'in_progress' as const };
    } else {
      return { step_id: stage.id, name: stage.name, status: 'pending' as const };
    }
  });

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6 sm:p-8 max-w-lg mx-auto shadow-sm">
      <div className="mb-6">
        <h2 className="text-lg font-semibold text-slate-900">Processing Data</h2>
        <p className="text-xs text-slate-500 mt-0.5 font-medium">Executing standardized data cleansing pipeline</p>
      </div>

      <div className="space-y-4">
        {displaySteps.map((step, index) => {
          const isCompleted = step.status === 'completed';
          const isInProgress = step.status === 'in_progress';
          const isFailed = step.status === 'failed';
          const isPending = step.status === 'pending';

          return (
            <div key={step.step_id || index} className="flex items-start gap-3.5">
              {/* Status Indicator Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {isCompleted && (
                  <div className="w-5 h-5 rounded-full bg-emerald-50 text-emerald-600 border border-emerald-200 flex items-center justify-center">
                    <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                  </div>
                )}
                {isInProgress && (
                  <div className="w-5 h-5 rounded-full bg-blue-50 text-blue-600 border border-blue-200 flex items-center justify-center">
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
                    <Circle className="w-2.5 h-2.5" />
                  </div>
                )}
              </div>

              {/* Step Info */}
              <div className="min-w-0 flex-1">
                <p className={`text-sm font-medium ${
                  isCompleted ? 'text-slate-800' :
                  isInProgress ? 'text-blue-600 font-semibold' :
                  isFailed ? 'text-red-600 font-semibold' :
                  'text-slate-400'
                }`}>
                  {step.name}
                </p>
                {step.message && (
                  <p className="text-xs text-slate-500 mt-0.5 leading-normal">
                    {step.message}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
