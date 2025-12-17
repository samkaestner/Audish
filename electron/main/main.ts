import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import * as path from 'path';
import { spawn, SpawnOptionsWithoutStdio } from 'child_process';
import * as fs from 'fs/promises';
import { existsSync } from 'fs';

let mainWindow: BrowserWindow | null = null;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

// #region agent log
function agentLog(hypothesisId: string, location: string, message: string, data: Record<string, any> = {}, runId: string = 'pre-fix') {
  // Avoid logging secrets/PII; paths + booleans only.
  (globalThis as any).fetch?.('http://127.0.0.1:7242/ingest/cb5411a4-8082-4f74-9a01-c0dea3aab458', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId: 'debug-session',
      runId,
      hypothesisId,
      location,
      message,
      data,
      timestamp: Date.now(),
    }),
  }).catch(() => {});
}
// #endregion

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
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('select-folder', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openDirectory'],
  });
  return result.canceled ? null : result.filePaths[0];
});

ipcMain.handle('run-scheduler', async (_, config: {
  applicantFile: string;
  facultyFile: string;
  mappingFile: string;
  rulesFile: string;
  outputDir: string;
}) => {
  return new Promise((resolve) => {
    // Get the audish executable (bundled or system Python)
    const audish = getAudishExecutable();
    const projectRoot = getProjectRoot();
    agentLog('A', 'electron/main/main.ts:run-scheduler', 'run-scheduler invoked', {
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      projectRoot,
      schoolsDir: getSchoolsDir(),
      mappingFile: config.mappingFile,
      rulesFile: config.rulesFile,
      mappingExists: existsSync(config.mappingFile),
      rulesExists: existsSync(config.rulesFile),
      bundledExeUsed: audish.useBundled,
      bundledExePath: audish.useBundled ? audish.command : undefined,
      bundledExeExists: audish.useBundled ? existsSync(audish.command) : undefined,
    });
    
    const outputSchedule = path.join(config.outputDir, 'FinalSchedule.xlsx');
    const outputConflicts = path.join(config.outputDir, 'Conflicts.xlsx');
    const outputMetrics = path.join(config.outputDir, 'Metrics.txt');

    // Ensure output directory exists
    fs.mkdir(config.outputDir, { recursive: true }).then(() => {
      // Build command arguments
      // For bundled executable: audish-cli schedule --app ... 
      // For system Python: python -m audish.cli schedule --app ...
      const args = [
        ...audish.args,  // Empty for bundled, ['-m', 'audish.cli'] for system Python
        'schedule',
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
        stdout += data.toString();
        console.log(`[audish stdout] ${data.toString().trim()}`);
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
          // Return error as result object instead of rejecting
          let errorMessage = stderr || stdout || `Process exited with code ${code}`;
          
          // Provide helpful error messages for common issues
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
            error: errorMessage,
          });
        }
      });

      schedulerProcess.on('error', (error: any) => {
        // Return error as result object instead of rejecting
        let errorMessage = error.message || String(error);
        
        // Provide helpful error messages for common issues
        if (error.code === 'ENOENT') {
          if (audish.useBundled) {
            errorMessage = `Bundled scheduler executable not found.\n\nThis is an internal error. Please reinstall the application.`;
          } else {
            errorMessage = `Python not found. Please install Python 3.8+ and ensure it's in your PATH.\n\nTried: ${audish.command}`;
          }
        } else if (!audish.useBundled && (stderr.includes('No module named') || stderr.includes('ModuleNotFoundError'))) {
          errorMessage = `Python module not found. Please install the audish package:\n\n  pip install -e .\n\n(from the project root directory)\n\nError details: ${stderr || errorMessage}`;
        }
        
        resolve({
          success: false,
          error: errorMessage,
          stdout,
          stderr,
        });
      });
    }).catch((error) => {
      // Return error as result object instead of rejecting
      resolve({
        success: false,
        error: error.message || String(error),
      });
    });
  });
});

ipcMain.handle('read-file', async (_, filePath: string) => {
  try {
    agentLog('A', 'electron/main/main.ts:read-file', 'read-file called', {
      isPackaged: app.isPackaged,
      resourcesPath: process.resourcesPath,
      filePath,
      exists: existsSync(filePath),
    });
    const content = await fs.readFile(filePath, 'utf-8');
    return { success: true, content };
  } catch (error: any) {
    agentLog('A', 'electron/main/main.ts:read-file', 'read-file failed', {
      filePath,
      error: error?.message || String(error),
    });
    return { success: false, error: error.message };
  }
});

ipcMain.handle('file-exists', async (_, filePath: string) => {
  return existsSync(filePath);
});

ipcMain.handle('read-excel-preview', async (_, filePath: string, maxRows: number = 100) => {
  return new Promise((resolve) => {
    const projectRoot = getProjectRoot();

    // For Excel preview we call the lightweight helper module directly:
    //   python -m audish.excel_reader <filePath> <maxRows>
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const args = ['-m', 'audish.excel_reader', filePath, maxRows.toString()];

    console.log(`[excel-preview] Command: ${pythonCmd} ${args.join(' ')}`);
    
    const excelProcess = spawn(pythonCmd, args, {
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
          resolve({ success: false, error: `Failed to parse Excel data: ${e}`, data: [], headers: [] });
        }
      } else {
        console.error('Excel preview failed:', { code, stderr, stdout, filePath });
        resolve({ success: false, error: stderr || stdout || 'Failed to read Excel file', data: [], headers: [] });
      }
    });
    
    excelProcess.on('error', (error) => {
      resolve({ success: false, error: error.message, data: [], headers: [] });
    });
  });
});

ipcMain.handle('write-file', async (_, filePath: string, content: string) => {
  try {
    await fs.writeFile(filePath, content, 'utf-8');
    return { success: true };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('get-project-root', async () => {
  const projectRoot = getProjectRoot();
  agentLog('A', 'electron/main/main.ts:get-project-root', 'get-project-root', {
    isPackaged: app.isPackaged,
    resourcesPath: process.resourcesPath,
    projectRoot,
    schoolsDir: getSchoolsDir(),
  });
  return getProjectRoot();
});

ipcMain.handle('get-schools-dir', async () => {
  return getSchoolsDir();
});

ipcMain.handle('download-file', async (_, filePath: string) => {
  try {
    if (existsSync(filePath)) {
      // Show save dialog
      const result = await dialog.showSaveDialog(mainWindow!, {
        defaultPath: path.basename(filePath),
      });
      
      if (!result.canceled && result.filePath) {
        // If destination file exists, delete it first to ensure clean overwrite
        // This handles cases where the file might be locked or have permission issues
        if (existsSync(result.filePath)) {
          try {
            await fs.unlink(result.filePath);
          } catch (unlinkError: any) {
            // If we can't delete it, try to overwrite anyway
            console.warn(`[download-file] Could not delete existing file: ${unlinkError.message}`);
          }
        }
        
        // Copy file to destination
        await fs.copyFile(filePath, result.filePath);
        return { success: true, path: result.filePath };
      }
    }
    return { success: false, error: 'File not found' };
  } catch (error: any) {
    return { success: false, error: error.message };
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
    
    // Build command arguments for validate command
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
        // Extract the error message from output
        const output = stdout || stderr;
        resolve({
          success: true,  // The process ran successfully, but validation found issues
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
        error: error.message || String(error),
      });
    });
  });
});

