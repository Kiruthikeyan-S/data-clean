import React from 'react';
import { FileUpload } from '../components/FileUpload';

interface UploadPageProps {
  onProcess: (files: File[]) => void;
  isProcessing?: boolean;
}

export const UploadPage: React.FC<UploadPageProps> = ({ onProcess, isProcessing }) => {
  return (
    <div className="py-12 sm:py-16 px-4">
      <FileUpload onProcess={onProcess} isProcessing={isProcessing} />
    </div>
  );
};
