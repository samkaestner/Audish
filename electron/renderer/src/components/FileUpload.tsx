import { useState, useCallback } from 'react';
import { useSchedulerStore } from '../lib/store';
import { Upload, X, FileSpreadsheet, CheckCircle2 } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { cn } from '../lib/utils';

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
    (e: React.DragEvent, type: 'applicant' | 'faculty') => {
      e.preventDefault();
      e.stopPropagation();
      setDragging(null);

      const files = Array.from(e.dataTransfer.files);
      const excelFile = files.find(
        (f) => f.name.toLowerCase().endsWith('.xlsx') || f.name.toLowerCase().endsWith('.xls')
      );

      if (!excelFile) {
        return;
      }

      // In Electron, dropped files include a non-standard `path` property
      const fileWithPath = excelFile as File & { path?: string };
      const filePath = fileWithPath.path || fileWithPath.name;

      if (!filePath) {
        return;
      }

      if (type === 'applicant') {
        setApplicantFile(filePath);
      } else {
        setFacultyFile(filePath);
      }
    },
    [setApplicantFile, setFacultyFile]
  );

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  return (
    <Card className="border-none shadow-none bg-transparent p-0">
      <CardHeader className="px-0 pt-0">
        <CardTitle>Data Sources</CardTitle>
        <CardDescription>Upload the required Excel files to begin.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6 md:grid-cols-2 px-0">
        {/* Applicant File */}
        <div
          className={cn(
            "group relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 transition-all hover:bg-accent/50 cursor-pointer",
            dragging === 'applicant' ? 'border-primary bg-accent' : 'border-muted-foreground/25',
            applicantFile ? 'border-primary/50 bg-primary/5' : ''
          )}
          onDrop={(e) => handleDrop(e, 'applicant')}
          onDragOver={handleDragOver}
          onDragEnter={() => setDragging('applicant')}
          onDragLeave={() => setDragging(null)}
          onClick={() => handleFileSelect('applicant')}
        >
          {applicantFile ? (
            <>
              <div className="absolute right-2 top-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setApplicantFile(null);
                  }}
                  className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
                <CheckCircle2 size={24} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium leading-none text-primary mb-1">
                  Applicant File Loaded
                </p>
                <p className="text-xs text-muted-foreground break-all max-w-[200px]">
                  {applicantFile.split(/[/\\]/).pop()}
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground mb-3 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                <Upload size={24} />
              </div>
              <div className="text-center space-y-1">
                <p className="text-sm font-medium leading-none">
                  <span className="text-primary">Upload Applicant Info</span>
                </p>
                <p className="text-xs text-muted-foreground">
                  Drag and drop or click to browse
                </p>
              </div>
            </>
          )}
        </div>

        {/* Faculty File */}
        <div
          className={cn(
            "group relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed px-6 py-10 transition-all hover:bg-accent/50 cursor-pointer",
            dragging === 'faculty' ? 'border-primary bg-accent' : 'border-muted-foreground/25',
            facultyFile ? 'border-primary/50 bg-primary/5' : ''
          )}
          onDrop={(e) => handleDrop(e, 'faculty')}
          onDragOver={handleDragOver}
          onDragEnter={() => setDragging('faculty')}
          onDragLeave={() => setDragging(null)}
          onClick={() => handleFileSelect('faculty')}
        >
          {facultyFile ? (
            <>
              <div className="absolute right-2 top-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setFacultyFile(null);
                  }}
                  className="rounded-full p-1 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                >
                  <X size={16} />
                </button>
              </div>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mb-3">
                <CheckCircle2 size={24} />
              </div>
              <div className="text-center">
                <p className="text-sm font-medium leading-none text-primary mb-1">
                  Faculty Availability Loaded
                </p>
                <p className="text-xs text-muted-foreground break-all max-w-[200px]">
                  {facultyFile.split(/[/\\]/).pop()}
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-muted text-muted-foreground mb-3 group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                <FileSpreadsheet size={24} />
              </div>
              <div className="text-center space-y-1">
                <p className="text-sm font-medium leading-none">
                  <span className="text-primary">Upload Faculty Availability</span>
                </p>
                <p className="text-xs text-muted-foreground">
                  Drag and drop or click to browse
                </p>
              </div>
            </>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
