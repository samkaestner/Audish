export interface ElectronAPI {
  selectFile: (options?: { filters?: Array<{ name: string; extensions: string[] }> }) => Promise<string | null>;
  selectFolder: () => Promise<string | null>;
  registerDroppedFile: (filePath: string) => Promise<boolean>;
  runScheduler: (options: {
    applicantFile: string;
    facultyFile: string;
    mappingFile: string;
    rulesFile: string;
    outputDir: string;
  }) => Promise<{
    success: boolean;
    error?: string;
    stdout?: string;
    stderr?: string;
    code?: number;
    outputFiles?: {
      schedule: string;
      conflicts: string;
      metrics: string;
    };
  }>;
  validateConfig: (options: {
    applicantFile: string;
    facultyFile: string;
    mappingFile: string;
    rulesFile: string;
  }) => Promise<{
    success: boolean;
    valid: boolean;
    message?: string;
    errors?: string;
    error?: string;
  }>;
  readFile: (filePath: string) => Promise<{ success: boolean; content?: string; error?: string }>;
  fileExists: (filePath: string) => Promise<boolean>;
  readExcelPreview: (filePath: string, maxRows: number) => Promise<{
    success: boolean;
    headers?: string[];
    data?: string[][];
    total_rows?: number;
    error?: string;
  }>;
  writeFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>;
  getProjectRoot: () => Promise<string>;
  getSchoolsDir: () => Promise<string>;
  getUserDataDir: () => Promise<string>;
  downloadFile: (filePath: string) => Promise<{ success: boolean; path?: string; error?: string }>;
  openFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
  onSchedulerProgress: (callback: (progress: any) => void) => () => void;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
