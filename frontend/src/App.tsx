import React, { useState } from 'react';
import { Header } from './components/Header';
import { UploadPage } from './pages/UploadPage';
import { ProcessingPage } from './pages/ProcessingPage';
import { ResultPage } from './pages/ResultPage';
import { ErrorMessage } from './components/ErrorMessage';
import { ProcessResponse, StepStatus } from './types';
import { processFile, processBatchFiles } from './services/api';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState<'upload' | 'processing' | 'result'>('upload');
  
  const [currentFileName, setCurrentFileName] = useState<string>('Files');
  const [steps, setSteps] = useState<StepStatus[]>([]);
  const [currentStepIndex, setCurrentStepIndex] = useState<number>(0);
  const [results, setResults] = useState<ProcessResponse[]>([]);
  const [activeResultIndex, setActiveResultIndex] = useState<number>(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const handleStartProcess = async (files: File[]) => {
    if (files.length === 0) return;

    setCurrentFileName(files.length > 1 ? `${files.length} Files (${files.map(f => f.name).join(', ')})` : files[0].name);
    setErrorMessage(null);
    setCurrentPage('processing');
    setSteps([]);
    setCurrentStepIndex(0);
    setActiveResultIndex(0);

    const stageTimer1 = setTimeout(() => setCurrentStepIndex(1), 250);
    const stageTimer2 = setTimeout(() => setCurrentStepIndex(2), 500);
    const stageTimer3 = setTimeout(() => setCurrentStepIndex(3), 800);

    try {
      if (files.length === 1) {
        const response = await processFile(files[0]);
        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);
        clearTimeout(stageTimer3);

        setSteps(response.steps);
        setCurrentStepIndex(response.steps.length);
        setResults([response]);
      } else {
        const batchResponse = await processBatchFiles(files);
        clearTimeout(stageTimer1);
        clearTimeout(stageTimer2);
        clearTimeout(stageTimer3);

        if (batchResponse.results.length > 0) {
          setSteps(batchResponse.results[0].steps);
          setCurrentStepIndex(batchResponse.results[0].steps.length);
          setResults(batchResponse.results);
        }
      }

      setTimeout(() => {
        setCurrentPage('result');
      }, 400);

    } catch (err: any) {
      clearTimeout(stageTimer1);
      clearTimeout(stageTimer2);
      clearTimeout(stageTimer3);

      setErrorMessage(err.message || 'An unexpected error occurred during processing.');
      setCurrentPage('upload');
    }
  };

  const handleReset = () => {
    setResults([]);
    setActiveResultIndex(0);
    setErrorMessage(null);
    setCurrentPage('upload');
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#f8fafc]">
      {/* Header Navigation */}
      <Header onNavigateUpload={handleReset} />

      {/* Global Error Banner if on upload page */}
      {errorMessage && currentPage === 'upload' && (
        <div className="max-w-2xl mx-auto px-4 mt-6 w-full">
          <ErrorMessage message={errorMessage} onDismiss={() => setErrorMessage(null)} />
        </div>
      )}

      {/* Main Content Area */}
      <main className="flex-1">
        {currentPage === 'upload' && (
          <UploadPage onProcess={handleStartProcess} />
        )}

        {currentPage === 'processing' && (
          <ProcessingPage
            filename={currentFileName}
            steps={steps}
            currentStepIndex={currentStepIndex}
          />
        )}

        {currentPage === 'result' && results.length > 0 && (
          <ResultPage
            results={results}
            activeIndex={activeResultIndex}
            onSelectIndex={(idx) => setActiveResultIndex(idx)}
            onReset={handleReset}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 text-center text-xs text-slate-400">
        <div className="max-w-6xl mx-auto px-4">
          DataFlow Enterprise Data Processing Pipeline • Standardized Data Normalization & Validation
        </div>
      </footer>
    </div>
  );
};

export default App;
