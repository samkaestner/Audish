import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: (options?: { filters?: { name: string; extensions: string[] }[] }) =>
    ipcRenderer.invoke('select-file', options),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  runScheduler: (config: {
    applicantFile: string;
    facultyFile: string;
    mappingFile: string;
    rulesFile: string;
    outputDir: string;
  }) => ipcRenderer.invoke('run-scheduler', config),
  validateConfig: (config: {
    applicantFile: string;
    facultyFile: string;
    mappingFile: string;
    rulesFile: string;
  }) => ipcRenderer.invoke('validate-config', config),
  readFile: (filePath: string) => ipcRenderer.invoke('read-file', filePath),
  fileExists: (filePath: string) => ipcRenderer.invoke('file-exists', filePath),
  readExcelPreview: (filePath: string, maxRows?: number) =>
    ipcRenderer.invoke('read-excel-preview', filePath, maxRows),
  writeFile: (filePath: string, content: string) =>
    ipcRenderer.invoke('write-file', filePath, content),
  getProjectRoot: () => ipcRenderer.invoke('get-project-root'),
  getSchoolsDir: () => ipcRenderer.invoke('get-schools-dir'),
  downloadFile: (filePath: string) => ipcRenderer.invoke('download-file', filePath),
});

export type ElectronAPI = {
  selectFile: (options?: { filters?: { name: string; extensions: string[] }[] }) => Promise<string | null>;
  selectFolder: () => Promise<string | null>;
  runScheduler: (config: {
    applicantFile: string;
    facultyFile: string;
    mappingFile: string;
    rulesFile: string;
    outputDir: string;
  }) => Promise<any>;
  validateConfig: (config: {
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
  readExcelPreview: (filePath: string, maxRows?: number) => Promise<any>;
  writeFile: (filePath: string, content: string) => Promise<{ success: boolean; error?: string }>;
  getProjectRoot: () => Promise<string>;
  getSchoolsDir: () => Promise<string>;
  downloadFile: (filePath: string) => Promise<{ success: boolean; path?: string; error?: string }>;
};

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}

