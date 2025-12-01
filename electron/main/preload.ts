import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('electronAPI', {
  selectFile: (options?: { filters?: { name: string; extensions: string[] }[] }) =>
    ipcRenderer.invoke('select-file', options),
  selectFolder: () => ipcRenderer.invoke('select-folder'),
  registerDroppedFile: (filePath: string) => ipcRenderer.invoke('register-dropped-file', filePath),
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
  getUserDataDir: () => ipcRenderer.invoke('get-user-data-dir'),
  downloadFile: (filePath: string) => ipcRenderer.invoke('download-file', filePath),
  openFile: (filePath: string) => ipcRenderer.invoke('open-file', filePath),
  // Progress event listener
  onSchedulerProgress: (callback: (progress: any) => void) => {
    const handler = (_event: any, progress: any) => callback(progress);
    ipcRenderer.on('scheduler-progress', handler);
    // Return unsubscribe function
    return () => ipcRenderer.removeListener('scheduler-progress', handler);
  },
});

export type ElectronAPI = {
  selectFile: (options?: { filters?: { name: string; extensions: string[] }[] }) => Promise<string | null>;
  selectFolder: () => Promise<string | null>;
  registerDroppedFile: (filePath: string) => Promise<boolean>;
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
  getUserDataDir: () => Promise<string>;
  downloadFile: (filePath: string) => Promise<{ success: boolean; path?: string; error?: string }>;
  openFile: (filePath: string) => Promise<{ success: boolean; error?: string }>;
  onSchedulerProgress: (callback: (progress: any) => void) => () => void;
};

declare global {
  interface Window {
    electronAPI: ElectronAPI;
  }
}
