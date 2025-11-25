import { useState, useCallback } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Upload, X, FileSpreadsheet } from 'lucide-react';

export default function FileUpload() {
  const { applicantFile, facultyFile, setApplicantFile, setFacultyFile } = useSchedulerStore();
  const [dragging, setDragging] = useState<'applicant' | 'faculty' | null>(null);

  const handleFileSelect = useCallback(async (type: 'applicant' | 'faculty') => {
    if (!window.electronAPI) return;
    
    const file = await window.electronAPI.selectFile({
      filters: [{ name: 'Excel Files', extensions: ['xlsx', 'xls'] }],
    });
    
    if (file) {
      if (type === 'applicant') {
        setApplicantFile(file);
      } else {
        setFacultyFile(file);
      }
    }
  }, [setApplicantFile, setFacultyFile]);

  const handleDrop = useCallback(
    async (e: React.DragEvent, type: 'applicant' | 'faculty') => {
      e.preventDefault();
      setDragging(null);

      const files = Array.from(e.dataTransfer.files);
      const excelFile = files.find(
        (f) => f.name.endsWith('.xlsx') || f.name.endsWith('.xls')
      );

      if (excelFile) {
        // In Electron, we need to use the file path
        // For now, we'll use the file name and let user select via dialog
        handleFileSelect(type);
      }
    },
    [handleFileSelect]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Upload Files</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Applicant File */}
        <div
          className={`neo-card cursor-pointer transition-all ${
            dragging === 'applicant' ? 'bg-accent/20' : ''
          }`}
          onDrop={(e) => handleDrop(e, 'applicant')}
          onDragOver={handleDragOver}
          onDragEnter={() => setDragging('applicant')}
          onDragLeave={() => setDragging(null)}
          onClick={() => handleFileSelect('applicant')}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">Applicant File</h3>
            {applicantFile && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setApplicantFile(null);
                }}
                className="text-red-500 hover:text-red-700"
              >
                <X size={20} />
              </button>
            )}
          </div>

          {applicantFile ? (
            <div className="flex items-center gap-2">
              <FileSpreadsheet size={24} />
              <span className="font-mono text-sm break-all">{applicantFile.split(/[/\\]/).pop()}</span>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <Upload size={48} />
              <p className="text-center">
                Click to browse or drag and drop
                <br />
                <span className="text-sm opacity-70">Excel file (.xlsx, .xls)</span>
              </p>
            </div>
          )}
        </div>

        {/* Faculty File */}
        <div
          className={`neo-card cursor-pointer transition-all hover:bg-accent/5 ${
            dragging === 'faculty' ? 'bg-accent/20 border-accent' : ''
          }`}
          onDrop={(e) => handleDrop(e, 'faculty')}
          onDragOver={handleDragOver}
          onDragEnter={() => setDragging('faculty')}
          onDragLeave={() => setDragging(null)}
          onClick={() => handleFileSelect('faculty')}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-bold">Faculty Availability File</h3>
            {facultyFile && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setFacultyFile(null);
                }}
                className="text-red-500 hover:text-red-700"
              >
                <X size={20} />
              </button>
            )}
          </div>

          {facultyFile ? (
            <div className="flex items-center gap-2">
              <FileSpreadsheet size={24} />
              <span className="font-mono text-sm break-all">{facultyFile.split(/[/\\]/).pop()}</span>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 gap-4">
              <Upload size={48} />
              <p className="text-center">
                Click to browse or drag and drop
                <br />
                <span className="text-sm opacity-70">Excel file (.xlsx, .xls)</span>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

