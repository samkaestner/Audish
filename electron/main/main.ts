import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import * as path from 'path';
import { spawn } from 'child_process';
import * as fs from 'fs/promises';
import { existsSync } from 'fs';
import * as security from './security';

let mainWindow: BrowserWindow | null = null;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

/**
 * Get the path to the audish CLI executable.
 * 
 * In packaged mode: Uses the bundled PyInstaller executable
 * In development mode: Falls back to system Python
 */
function getAudishExecutable(): { command: string; args: string[]; useBundled: boolean } {
  if (app.isPackaged) {
    // In packaged app, use the bundled PyInstaller executable
    const exeName = process.platform === 'win32' ? 'audish-cli.exe' : 'audish-cli';
    const bundledPath = path.join(process.resourcesPath, exeName);
    
    if (existsSync(bundledPath)) {
      console.log(`[audish] Using bundled executable: ${bundledPath}`);
      return { command: bundledPath, args: [], useBundled: true };
    } else {
      console.warn(`[audish] Bundled executable not found at: ${bundledPath}`);
      console.warn('[audish] Falling back to system Python');
    }
  }
  
  // Fall back to system Python (for development or if bundled exe not found)
  const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
  console.log(`[audish] Using system Python: ${pythonCmd}`);
  return { command: pythonCmd, args: ['-m', 'audish.cli'], useBundled: false };
}

/**
 * Get the path to configuration files (schools directory).
 * 
 * In packaged mode: Uses the bundled schools directory in resources
 * In development mode: Uses the project root schools directory
 */
function getSchoolsDir(): string {
  if (app.isPackaged) {
    const bundledSchools = path.join(process.resourcesPath, 'schools');
    if (existsSync(bundledSchools)) {
      return bundledSchools;
    }
  }
  // Fall back to project root
  return path.join(getProjectRoot(), 'schools');
}

/**
 * Get the project root directory.
 */
function getProjectRoot(): string {
  if (app.isPackaged) {
    return path.resolve(process.resourcesPath, '..');
  }
  return path.resolve(__dirname, '../../');
}

/**
 * Get a writable directory for temp files and output.
 * In packaged mode: Uses the app's user data directory
 * In development mode: Uses the project root
 */
function getUserDataDir(): string {
  if (app.isPackaged) {
    return app.getPath('userData');
  }
  return getProjectRoot();
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
    backgroundColor: '#0d0d0d',
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/dist/index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.whenReady().then(() => {
  // Register bundled/default config directories as allowed paths
  const schoolsDir = getSchoolsDir();
  security.registerUserSelectedFolder(schoolsDir);
  console.log(`[security] Registered schools directory: ${schoolsDir}`);
  
  // Register user data directory for temp files and output
  const userDataDir = getUserDataDir();
  security.registerUserSelectedFolder(userDataDir);
  console.log(`[security] Registered user data directory: ${userDataDir}`);

  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// IPC handlers
ipcMain.handle('select-file', async (_, options: { filters?: { name: string; extensions: string[] }[] }) => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openFile'],
    filters: options.filters || [{ name: 'All Files', extensions: ['*'] }],
  });
  if (!result.canceled && result.filePaths[0]) {
    // Register user-selected file for security validation
    security.registerUserSelectedFile(result.filePaths[0]);
    return result.filePaths[0];
  }
  return null;
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openDirectory'],
  });
  if (!result.canceled && result.filePaths[0]) {
    // Register user-selected folder for security validation
    security.registerUserSelectedFolder(result.filePaths[0]);
    return result.filePaths[0];
  }
  return null;
});

// Register a file from drag-drop (needs to be registered for security validation)
ipcMain.handle('register-dropped-file', async (_, filePath: string) => {
  if (filePath && typeof filePath === 'string') {
    security.registerUserSelectedFile(filePath);
    console.log(`[security] Registered dropped file: ${filePath}`);
    return true;
  }
  return false;
});

ipcMain.handle('run-scheduler', async (_, config: {
  applicantFile: string;
  facultyFile: string;
  mappingFile: string;
  rulesFile: string;
  outputDir: string;
}) => {
  return new Promise((resolve) => {
    // Security: Register the output directory
    if (config.outputDir) {
      security.registerUserSelectedFolder(config.outputDir);
    }
    
    // Get the audish executable (bundled or system Python)
    const audish = getAudishExecutable();
    const projectRoot = getProjectRoot();
    
    const outputSchedule = path.join(config.outputDir, 'FinalSchedule.xlsx');
    const outputConflicts = path.join(config.outputDir, 'Conflicts.xlsx');
    const outputMetrics = path.join(config.outputDir, 'Metrics.txt');

    // Ensure output directory exists
    fs.mkdir(config.outputDir, { recursive: true }).then(() => {
      // Build command arguments
      const args = [
        ...audish.args,
        'schedule',
        '--progress', // Enable machine-readable progress output
        '--app', config.applicantFile,
        '--fac', config.facultyFile,
        '--map', config.mappingFile,
        '--rules', config.rulesFile,
        '--out-schedule', outputSchedule,
        '--out-conflicts', outputConflicts,
        '--out-metrics', outputMetrics,
      ];

      console.log(`[run-scheduler] Command: ${audish.command}`);
      console.log(`[run-scheduler] Args: ${args.join(' ')}`);
      console.log(`[run-scheduler] CWD: ${projectRoot}`);

      const schedulerProcess = spawn(audish.command, args, {
        cwd: projectRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      schedulerProcess.stdout.on('data', (data) => {
        const text = data.toString();
        stdout += text;
        console.log(`[audish stdout] ${text.trim()}`);
        
        // Parse progress events and send to renderer
        const lines = text.split('\n');
        for (const line of lines) {
          if (line.startsWith('PROGRESS:')) {
            try {
              const progress = JSON.parse(line.substring(9));
              mainWindow?.webContents.send('scheduler-progress', progress);
            } catch (e) {
              // Ignore parse errors
            }
          }
        }
      });

      schedulerProcess.stderr.on('data', (data) => {
        stderr += data.toString();
        console.log(`[audish stderr] ${data.toString().trim()}`);
      });

      schedulerProcess.on('close', (code) => {
        if (code === 0) {
          resolve({
            success: true,
            stdout,
            stderr,
            outputFiles: {
              schedule: outputSchedule,
              conflicts: outputConflicts,
              metrics: outputMetrics,
            },
          });
        } else {
          let errorMessage = stderr || stdout || `Process exited with code ${code}`;
          
          if (!audish.useBundled && (stderr.includes('No module named') || stderr.includes('ModuleNotFoundError'))) {
            if (stderr.includes('audish')) {
              errorMessage = `Python module 'audish' not found.\n\nPlease install it by running:\n\n  pip install -e .\n\nfrom the project root directory.\n\nError details:\n${stderr || stdout}`;
            } else {
              errorMessage = `Python module not found.\n\nError details:\n${stderr || stdout}`;
            }
          }
          
          resolve({
            success: false,
            code,
            stdout,
            stderr,
            error: security.sanitizeErrorMessage(errorMessage),
          });
        }
      });

      schedulerProcess.on('error', (error: any) => {
        let errorMessage = error.message || String(error);
        
        if (error.code === 'ENOENT') {
          if (audish.useBundled) {
            errorMessage = `Bundled scheduler executable not found.\n\nThis is an internal error. Please reinstall the application.`;
          } else {
            errorMessage = `Python not found. Please install Python 3.8+ and ensure it's in your PATH.\n\nTried: ${audish.command}`;
          }
        }
        
        resolve({
          success: false,
          error: security.sanitizeErrorMessage(errorMessage),
          stdout,
          stderr,
        });
      });
    }).catch((error) => {
      resolve({
        success: false,
        error: security.sanitizeErrorMessage(error),
      });
    });
  });
});

ipcMain.handle('read-file', async (_, filePath: string) => {
  try {
    // Security: Validate file path
    const validation = security.validateFilePath(filePath, {
      allowUserSelected: true,
      allowOutputFolder: true,
      allowedExtensions: ['.xlsx', '.xls', '.yaml', '.yml', '.txt'],
      resourcesPath: process.resourcesPath,
    });
    
    if (!validation.valid) {
      console.warn(`[security] Blocked read-file attempt: ${validation.reason}`);
      return { success: false, error: 'Access denied: ' + validation.reason };
    }
    
    const content = await fs.readFile(filePath, 'utf-8');
    return { success: true, content };
  } catch (error: any) {
    return { success: false, error: security.sanitizeErrorMessage(error) };
  }
});

ipcMain.handle('file-exists', async (_, filePath: string) => {
  try {
    // Security: Validate file path before checking existence
    const validation = security.validateFilePath(filePath, {
      allowUserSelected: true,
      allowOutputFolder: true,
      resourcesPath: process.resourcesPath,
    });
    
    if (!validation.valid) {
      return false;
    }
    
    return existsSync(filePath);
  } catch {
    return false;
  }
});

ipcMain.handle('read-excel-preview', async (_, filePath: string, maxRows: number = 100) => {
  // Security: Validate file path
  const validation = security.validateFilePath(filePath, {
    allowUserSelected: true,
    allowOutputFolder: true,
    allowedExtensions: ['.xlsx', '.xls'],
  });
  
  if (!validation.valid) {
    console.warn(`[security] Blocked read-excel-preview attempt: ${validation.reason}`);
    return { success: false, error: 'Access denied: ' + validation.reason, data: [], headers: [] };
  }

  return new Promise((resolve) => {
    const audish = getAudishExecutable();
    const projectRoot = getProjectRoot();
    
    let command: string;
    let args: string[];
    
    if (audish.useBundled) {
      command = audish.command;
      args = ['excel-preview', filePath, '--max-rows', maxRows.toString()];
      console.log('[excel-preview] Using bundled CLI');
    } else {
      command = audish.command;
      args = [...audish.args, 'excel-preview', filePath, '--max-rows', maxRows.toString()];
      console.log('[excel-preview] Using system Python');
    }
    
    console.log(`[excel-preview] Command: ${command} ${args.join(' ')}`);
    
    const excelProcess = spawn(command, args, {
      cwd: projectRoot,
    });
    
    let stdout = '';
    let stderr = '';
    
    excelProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    excelProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    excelProcess.on('close', (code) => {
      if (code === 0 && stdout) {
        try {
          const result = JSON.parse(stdout);
          resolve(result);
        } catch (e) {
          console.error('Failed to parse Excel preview JSON:', e, 'stdout:', stdout);
          resolve({ success: false, error: 'Failed to parse Excel data', data: [], headers: [] });
        }
      } else {
        console.error('Excel preview failed:', { code, stderr, stdout, filePath });
        resolve({ success: false, error: security.sanitizeErrorMessage(stderr || stdout || 'Failed to read Excel file'), data: [], headers: [] });
      }
    });
    
    excelProcess.on('error', (error) => {
      resolve({ success: false, error: security.sanitizeErrorMessage(error), data: [], headers: [] });
    });
  });
});

ipcMain.handle('write-file', async (_, filePath: string, content: string) => {
  try {
    // Security: Validate file path before writing
    const validation = security.validateFilePath(filePath, {
      allowUserSelected: false, // Don't allow writing to input files
      allowOutputFolder: true,  // Only allow output folder
      allowedExtensions: ['.yaml', '.yml', '.txt'],
    });
    
    if (!validation.valid) {
      console.warn(`[security] Blocked write-file attempt: ${validation.reason}`);
      return { success: false, error: 'Access denied: ' + validation.reason };
    }
    
    await fs.writeFile(filePath, content, 'utf-8');
    return { success: true };
  } catch (error: any) {
    return { success: false, error: security.sanitizeErrorMessage(error) };
  }
});

ipcMain.handle('get-project-root', async () => {
  return getProjectRoot();
});

ipcMain.handle('get-schools-dir', async () => {
  return getSchoolsDir();
});

ipcMain.handle('get-user-data-dir', async () => {
  return getUserDataDir();
});

ipcMain.handle('download-file', async (_, filePath: string) => {
  try {
    // Security: Validate file path
    const validation = security.validateFilePath(filePath, {
      allowUserSelected: true,
      allowOutputFolder: true,
      allowedExtensions: ['.xlsx', '.txt'],
    });
    
    if (!validation.valid) {
      console.warn(`[security] Blocked download-file attempt: ${validation.reason}`);
      return { success: false, error: 'Access denied: ' + validation.reason };
    }
    
    if (existsSync(filePath)) {
      const result = await dialog.showSaveDialog(mainWindow!, {
        defaultPath: path.basename(filePath),
      });
      
      if (!result.canceled && result.filePath) {
        await fs.copyFile(filePath, result.filePath);
        return { success: true, path: result.filePath };
      }
    }
    return { success: false, error: 'File not found' };
  } catch (error: any) {
    return { success: false, error: security.sanitizeErrorMessage(error) };
  }
});

ipcMain.handle('open-file', async (_, filePath: string) => {
  try {
    // Security: Validate file path
    const validation = security.validateFilePath(filePath, {
      allowUserSelected: true,
      allowOutputFolder: true,
      allowedExtensions: ['.xlsx', '.txt'],
    });
    
    if (!validation.valid) {
      console.warn(`[security] Blocked open-file attempt: ${validation.reason}`);
      return { success: false, error: 'Access denied: ' + validation.reason };
    }
    
    if (existsSync(filePath)) {
      await shell.openPath(filePath);
      return { success: true };
    }
    return { success: false, error: 'File not found' };
  } catch (error: any) {
    return { success: false, error: security.sanitizeErrorMessage(error) };
  }
});

// Validate configuration without running the scheduler
ipcMain.handle('validate-config', async (_, config: {
  applicantFile: string;
  facultyFile: string;
  mappingFile: string;
  rulesFile: string;
}) => {
  return new Promise((resolve) => {
    const audish = getAudishExecutable();
    const projectRoot = getProjectRoot();
    
    const args = [
      ...audish.args,
      'validate',
      '--app', config.applicantFile,
      '--fac', config.facultyFile,
      '--map', config.mappingFile,
      '--rules', config.rulesFile,
    ];

    console.log(`[validate-config] Command: ${audish.command}`);
    console.log(`[validate-config] Args: ${args.join(' ')}`);

    const validateProcess = spawn(audish.command, args, {
      cwd: projectRoot,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let stdout = '';
    let stderr = '';

    validateProcess.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    validateProcess.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    validateProcess.on('close', (code) => {
      if (code === 0) {
        resolve({
          success: true,
          valid: true,
          message: stdout || 'All configuration checks passed!',
        });
      } else {
        const output = stdout || stderr;
        resolve({
          success: true,
          valid: false,
          message: output,
          errors: output,
        });
      }
    });

    validateProcess.on('error', (error: any) => {
      resolve({
        success: false,
        valid: false,
        error: security.sanitizeErrorMessage(error),
      });
    });
  });
});
