import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import * as path from 'path';
import { spawn } from 'child_process';
import * as fs from 'fs/promises';
import { existsSync } from 'fs';

let mainWindow: BrowserWindow | null = null;
const isDev = process.env.NODE_ENV === 'development' || !app.isPackaged;

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
  return new Promise((resolve, reject) => {
    // Get the Python executable path
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    
    // Get the project root (go up from electron/main to project root)
    const projectRoot = path.resolve(__dirname, '../../');
    const outputSchedule = path.join(config.outputDir, 'FinalSchedule.xlsx');
    const outputConflicts = path.join(config.outputDir, 'Conflicts.xlsx');
    const outputMetrics = path.join(config.outputDir, 'Metrics.txt');

    // Ensure output directory exists
    fs.mkdir(config.outputDir, { recursive: true }).then(() => {
      const args = [
        '-m', 'audish.cli', 'schedule',
        '--app', config.applicantFile,
        '--fac', config.facultyFile,
        '--map', config.mappingFile,
        '--rules', config.rulesFile,
        '--out-schedule', outputSchedule,
        '--out-conflicts', outputConflicts,
        '--out-metrics', outputMetrics,
      ];

      const schedulerProcess = spawn(pythonCmd, args, {
        cwd: projectRoot,
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      let stdout = '';
      let stderr = '';

      schedulerProcess.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      schedulerProcess.stderr.on('data', (data) => {
        stderr += data.toString();
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
          reject({
            success: false,
            code,
            stdout,
            stderr,
            error: stderr || stdout,
          });
        }
      });

      schedulerProcess.on('error', (error) => {
        reject({
          success: false,
          error: error.message,
          stdout,
          stderr,
        });
      });
    }).catch(reject);
  });
});

ipcMain.handle('read-file', async (_, filePath: string) => {
  try {
    const content = await fs.readFile(filePath, 'utf-8');
    return { success: true, content };
  } catch (error: any) {
    return { success: false, error: error.message };
  }
});

ipcMain.handle('file-exists', async (_, filePath: string) => {
  return existsSync(filePath);
});

ipcMain.handle('read-excel-preview', async (_, filePath: string, maxRows: number = 100) => {
  return new Promise((resolve) => {
    const pythonCmd = process.platform === 'win32' ? 'python' : 'python3';
    const projectRoot = path.resolve(__dirname, '../../');
    const scriptPath = path.join(projectRoot, 'audish', 'excel_reader.py');
    
    const excelProcess = spawn(pythonCmd, [scriptPath, filePath, maxRows.toString()], {
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
          resolve({ success: false, error: 'Failed to parse Excel data', data: [], headers: [] });
        }
      } else {
        resolve({ success: false, error: stderr || 'Failed to read Excel file', data: [], headers: [] });
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
  return path.resolve(__dirname, '../../');
});

ipcMain.handle('download-file', async (_, filePath: string) => {
  try {
    if (existsSync(filePath)) {
      // Show save dialog
      const result = await dialog.showSaveDialog(mainWindow!, {
        defaultPath: path.basename(filePath),
      });
      
      if (!result.canceled && result.filePath) {
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

