# Security Documentation

This document outlines the security measures implemented in the Audition Scheduler application.

## Overview

The application follows a defense-in-depth approach with security controls at multiple layers:
1. **Electron Main Process** - File access validation and path sanitization
2. **Python CLI** - Input validation and path traversal prevention
3. **Library Usage** - Safe configuration for openpyxl and PyYAML

---

## File Access Controls

### User-Selected Files Only

The application restricts file access to:
- Files explicitly selected by users through native OS file dialogs
- Files within user-selected output directories
- Bundled application resources

**Implementation:**
- `electron/main/security.ts` - Security validation module
- `electron/main/main.ts` - IPC handlers with path validation

### Path Traversal Prevention

All file paths are validated to prevent directory traversal attacks:
- Blocks paths containing `..` (parent directory references)
- Blocks null byte injection (`\0`)
- Resolves paths to absolute form before access

### Allowed File Extensions

File operations are restricted by extension:
- **Read:** `.xlsx`, `.xls`, `.yaml`, `.yml`, `.txt`
- **Write:** `.yaml`, `.yml`, `.txt`
- **Download/Open:** `.xlsx`, `.txt`

---

## openpyxl Security

### Version Requirements

```
openpyxl>=3.1.0,<4.0.0
```

The application requires openpyxl 3.1.0+ which is not affected by the XXE vulnerability (CVE-2017-5992) that existed in versions prior to 2.4.1.

### Safe Loading Options

All Excel files are loaded with security-conscious options:
- `data_only=True` - Prevents formula execution
- `read_only=True` (validation) - Limits capabilities for read operations

### No Macro Execution

The application only reads data values from Excel files. Macros and formulas are not executed.

---

## YAML Security

All YAML files are loaded using `yaml.safe_load()` instead of `yaml.load()`, preventing arbitrary code execution through YAML deserialization attacks.

---

## Error Handling

### Sanitized Error Messages

Error messages returned to the UI are sanitized to prevent information disclosure:
- Home directory paths are replaced with `~`
- Full system paths are truncated
- Internal error details are not exposed to end users

---

## Electron Security Configuration

The application follows Electron security best practices:

```javascript
webPreferences: {
    contextIsolation: true,   // Prevents renderer access to Node.js
    nodeIntegration: false,   // Disables Node.js in renderer
    preload: '...'            // Uses preload script for IPC
}
```

### IPC Security

All IPC handlers validate inputs before processing:
1. **select-file/folder** - Registers user selection for later validation
2. **read-file** - Validates path is user-selected or in allowed location
3. **write-file** - Only allows writes to output folders
4. **download/open-file** - Only allows output files

---

## Python CLI Security

### Path Validation

The CLI validates all file paths before processing:
- Checks for path traversal patterns
- Resolves to absolute paths
- Validates file existence for input files

### Input Validation

Configuration files are validated against:
- Required structure (mapping.yaml, rules.yaml)
- Column name mappings
- Date format compliance

---

## Dependency Management

Dependencies are pinned to version ranges for stability and security:

```
click>=8.0.0,<9.0.0
openpyxl>=3.1.0,<4.0.0
pyyaml>=6.0,<7.0
python-dateutil>=2.8.0,<3.0.0
```

### Recommendations

1. **Regular Updates:** Periodically update dependencies to receive security patches
2. **Dependency Scanning:** Use tools like `safety` or `pip-audit` to check for vulnerabilities
3. **Lock Files:** Maintain `requirements.txt` with exact versions for production

---

## Threat Model

### Addressed Threats

| Threat | Mitigation |
|--------|------------|
| Path Traversal | Path validation, blocking `..` patterns |
| XXE (XML External Entity) | openpyxl 3.x, data_only mode |
| YAML Deserialization | yaml.safe_load() |
| Arbitrary File Access | User-selection tracking, extension filtering |
| Information Disclosure | Error message sanitization |
| Code Injection | No shell=True, array-based spawn arguments |

### Out of Scope

The application trusts:
- Excel file content (data values only)
- YAML configuration structure
- User-selected file paths

---

## Security Testing Checklist

Before release, verify:

- [ ] Path traversal blocked: `../../../etc/passwd`
- [ ] Non-Excel files rejected for preview
- [ ] Write operations restricted to output folder
- [ ] Error messages don't expose full paths
- [ ] openpyxl version >= 3.1.0 installed
- [ ] yaml.safe_load used throughout

---

## Reporting Security Issues

If you discover a security vulnerability, please report it responsibly by contacting the development team directly rather than creating a public issue.

