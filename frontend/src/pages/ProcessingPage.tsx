import React from 'react';
import { ProcessingSteps } from '../components/ProcessingSteps';
import { StepStatus } from '../types';

interface ProcessingPageProps {
  filename: string;
  steps: StepStatus[];
  currentStepIndex: number;
}

export const ProcessingPage: React.FC<ProcessingPageProps> = ({ filename, steps, currentStepIndex }) => {
  return (
    <div className="py-12 sm:py-16 px-4">
      <div className="max-w-lg mx-auto mb-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 mb-1">Processing Pipeline</p>
        <h1 className="text-xl font-bold text-slate-900 truncate">
          {filename}
        </h1>
      </div>

      <ProcessingSteps steps={steps} currentStepIndex={currentStepIndex} />
    </div>
  );
};
