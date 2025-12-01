/**
 * Security utilities for file path validation.
 * 
 * These utilities ensure the app only accesses files that:
 * 1. Are explicitly selected by the user through native dialogs
 * 2. Are within allowed directories (output folders, app resources)
 * 3. Do not contain path traversal patterns
 */

import * as path from 'path';
import * as os from 'os';

// Track files selected by user through native dialogs
const userSelectedFiles = new Set<string>();
const userSelectedFolders = new Set<string>();

interface ValidateOptions {
    allowUserSelected?: boolean;
    allowOutputFolder?: boolean;
    allowedExtensions?: string[] | null;
    resourcesPath?: string | null;
}

interface ValidationResult {
    valid: boolean;
    reason?: string;
}

/**
 * Register a file path as user-selected (from native dialog).
 */
export function registerUserSelectedFile(filePath: string): void {
    if (filePath) {
        userSelectedFiles.add(path.resolve(filePath));
    }
}

/**
 * Register a folder path as user-selected (from native dialog).
 */
export function registerUserSelectedFolder(folderPath: string): void {
    if (folderPath) {
        userSelectedFolders.add(path.resolve(folderPath));
    }
}

/**
 * Check if a path contains path traversal patterns.
 */
export function containsPathTraversal(filePath: string): boolean {
    if (!filePath) return true;
    
    // Normalize the path
    const normalized = path.normalize(filePath);
    
    // Check for common path traversal patterns
    const dangerousPatterns = [
        '..', // Parent directory traversal
        '\0', // Null byte injection
    ];
    
    for (const pattern of dangerousPatterns) {
        if (normalized.includes(pattern)) {
            return true;
        }
    }
    
    return false;
}

/**
 * Validate that a file path is safe to access.
 */
export function validateFilePath(filePath: string, options: ValidateOptions = {}): ValidationResult {
    const {
        allowUserSelected = true,
        allowOutputFolder = true,
        allowedExtensions = null,
        resourcesPath = null,
    } = options;
    
    if (!filePath || typeof filePath !== 'string') {
        return { valid: false, reason: 'Invalid file path' };
    }
    
    // Check for path traversal
    if (containsPathTraversal(filePath)) {
        return { valid: false, reason: 'Path contains traversal patterns' };
    }
    
    const resolvedPath = path.resolve(filePath);
    
    // Check file extension if restrictions are specified
    if (allowedExtensions && allowedExtensions.length > 0) {
        const ext = path.extname(resolvedPath).toLowerCase();
        if (!allowedExtensions.includes(ext)) {
            return { valid: false, reason: `File extension '${ext}' not allowed` };
        }
    }
    
    // Check if file was user-selected
    if (allowUserSelected && userSelectedFiles.has(resolvedPath)) {
        return { valid: true };
    }
    
    // Check if file is within a user-selected output folder
    if (allowOutputFolder) {
        for (const folder of userSelectedFolders) {
            if (resolvedPath.startsWith(folder + path.sep) || resolvedPath === folder) {
                return { valid: true };
            }
        }
    }
    
    // Check if file is within app resources (for bundled config files)
    if (resourcesPath) {
        const resolvedResources = path.resolve(resourcesPath);
        if (resolvedPath.startsWith(resolvedResources + path.sep)) {
            return { valid: true };
        }
    }
    
    return { valid: false, reason: 'File path not in allowed locations' };
}

/**
 * Sanitize error messages to avoid leaking sensitive path information.
 */
export function sanitizeErrorMessage(error: Error | string): string {
    const message = error instanceof Error ? error.message : String(error);
    
    // Remove full paths, keep only filename
    const homeDir = os.homedir();
    let sanitized = message;
    
    // Replace home directory with ~
    if (homeDir) {
        sanitized = sanitized.split(homeDir).join('~');
    }
    
    // Don't expose internal file structure
    sanitized = sanitized.replace(/\/Users\/[^/]+/g, '~');
    sanitized = sanitized.replace(/C:\\Users\\[^\\]+/gi, '~');
    
    return sanitized;
}

/**
 * Clear all tracked user selections (useful for testing or session reset).
 */
export function clearUserSelections(): void {
    userSelectedFiles.clear();
    userSelectedFolders.clear();
}

