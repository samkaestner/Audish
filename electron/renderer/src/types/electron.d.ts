export interface ElectronAPI {
  selectFile: (options?: { filters?: Array<{ name: string; extensions: string[] }> }) => Promise<string | null>;
  selectFolder: () => Promise<string | null>;
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
  downloadFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
}

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

