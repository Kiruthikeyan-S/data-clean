import React from 'react';
import { ProcessingSteps } from '../components/ProcessingSteps';
import { StepStatus } from '../types';

interface ProcessingPageProps {
  filename: string;
  steps: StepStatus[];
  currentStepIndex: number;
  progressPercent?: number;
  elapsedSeconds?: number;
}

export const ProcessingPage: React.FC<ProcessingPageProps> = ({
  filename,
  steps,
  currentStepIndex,
  progressPercent = 0,
  elapsedSeconds = 0
}) => {
  return (
    <div className="py-10 sm:py-14 px-4">
      <div className="max-w-xl mx-auto mb-6 text-center">
        <p className="text-xs font-semibold uppercase tracking-wider text-blue-600 mb-1">
          Automated Pipeline
        </p>
        <h1 className="text-lg font-bold text-slate-900 truncate">
          {filename}
        </h1>
      </div>

      <ProcessingSteps
        steps={steps}
        currentStepIndex={currentStepIndex}
        progressPercent={progressPercent}
        elapsedSeconds={elapsedSeconds}
      />
    </div>
  );
};
