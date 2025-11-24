# Faculty Name Matching Solution

## Problem

Faculty names appear differently between two Excel sheets:
- **Faculty Availability Sheet**: `"John Smith"`, `"Mary Johnson"`
- **Applicant Info Sheet**: `"Dr. John Smith"`, `"Prof. Mary Johnson"`, `"Ms. Jane Doe"`

The scheduler needs to match teacher preferences (from applicants) to faculty availability (from faculty sheet).

## Solution

### Automatic Name Normalization

The system automatically normalizes names by:

1. **Converting to lowercase** - case-insensitive matching
2. **Removing titles** - strips Dr., Prof., Mr., Ms., Mrs., etc.
3. **Removing punctuation** - handles hyphens and apostrophes
4. **Collapsing whitespace** - normalizes spacing

### Examples

| Applicant Teacher Name | Faculty Name | Match Result |
|------------------------|--------------|--------------|
| `Dr. John Smith` | `John Smith` | ✅ Match |
| `Prof. Mary Johnson` | `Mary Johnson` | ✅ Match |
| `Ms. Jane O'Connor` | `Jane O'Connor` | ✅ Match |
| `DR. ROBERT CHEN` | `Robert Chen` | ✅ Match |
| `Prof. Jean-Pierre Dubois` | `Jean Pierre Dubois` | ✅ Match |

### How It Works

```python
# Name normalization process:
"Dr. John Smith"        →  normalize  →  "john smith"
"John Smith" (faculty)  →  normalize  →  "john smith"
                                           ✅ MATCH!
```

## Match Rate Reporting

When you run the scheduler, step [4/7] reports matching statistics:

```
[4/7] Building faculty name mapping...
  ✓ Built name mapping for 100 faculty members
  ✓ Teacher name match rate: 89.3%
  ⚠ 279 unmatched teacher preferences
```

### What the Match Rate Means

- **89.3% match rate** = 89.3% of teacher preferences were successfully matched to faculty
- **Unmatched preferences** could be due to:
  - Faculty member not in availability sheet
  - Spelling variations that normalization didn't catch
  - Nicknames or alternate names

## Manual Aliases (Optional)

For edge cases where automatic matching fails, you can add manual aliases in `mapping.yaml`:

```yaml
faculty_name_aliases:
  "Dr. Jean-Pierre Rampal": "Jean Pierre Rampal"
  "Prof. Mary O'Brien-Smith": "Mary OBrien Smith"
  "Bob Smith": "Robert Smith"
  "Yo-Yo Ma": "YoYo Ma"
```

**Format**: `"Name in applicant data": "Name in faculty sheet"`

### When to Use Manual Aliases

Use manual aliases when:
- ✅ Faculty uses a nickname (Bob vs Robert)
- ✅ Different hyphenation or spacing variations
- ✅ Middle names included/excluded inconsistently
- ✅ Cultural name variations (different name order)

## Impact on Scheduling

### Teacher Preference Ranking

The scheduler ranks slots by teacher availability:
- **Rank 3** = 1st choice teacher available (best)
- **Rank 2** = 2nd choice teacher available
- **Rank 1** = 3rd choice teacher available
- **Rank 0** = No preferred teacher available

With better name matching, more applicants get their 1st choice teacher!

### Teacher Presence Policy

In `rules.yaml`:
- **`teacher_presence_policy: "prefer"`** - Schedules even without teacher match (current default)
- **`teacher_presence_policy: "require"`** - Only schedules when a teacher preference matches

## Debugging Name Mismatches

### Step 1: Check the Match Rate

Run the scheduler and look for:
```
⚠ 279 unmatched teacher preferences
```

If the match rate is low (<80%), investigate further.

### Step 2: Examine the Data

**Check Faculty Names:**
```bash
# Open faculty availability Excel
# Look at the "Faculty" column
# Note exact spelling and format
```

**Check Teacher Names in Applicants:**
```bash
# Open applicant info Excel
# Look at "1st Choice Teacher", "2nd Choice Teacher" columns
# Compare to faculty names
```

### Step 3: Add Manual Aliases

If you find systematic mismatches, add them to `mapping.yaml`:

```yaml
faculty_name_aliases:
  "Mismatched Name in Applicants": "Correct Name in Faculty Sheet"
```

### Step 4: Re-run and Verify

```bash
make run
```

Check if the match rate improved!

## Technical Details

### Supported Title Prefixes

The normalizer removes these titles:
- Academic: `Dr.`, `Prof.`, `Professor`
- Courtesy: `Mr.`, `Ms.`, `Mrs.`, `Miss`, `Mx.`
- Honorific: `Sir`, `Dame`, `Rev.`, `Hon.`

### Special Character Handling

| Character | Treatment | Example |
|-----------|-----------|---------|
| Hyphen `-` | Converted to space | `Jean-Pierre` → `jean pierre` |
| Apostrophe `'` | Removed | `O'Brien` → `obrien` |
| Periods `.` | Removed | `Dr.` → `dr` |
| Multiple spaces | Collapsed | `John  Smith` → `john smith` |

### Limitations

- **Nicknames**: Won't auto-match `Bob` to `Robert` (use manual alias)
- **Name order**: Assumes Western name format (given name, family name)
- **Diacritics**: Currently removed (é becomes e)

## Testing

The name matching system has comprehensive tests in `tests/test_faculty_names.py`:

```bash
# Run name matching tests
.venv/bin/pytest tests/test_faculty_names.py -v
```

**Test Coverage:**
- ✅ Title removal (Dr., Prof., Mr., Ms., etc.)
- ✅ Hyphenated names
- ✅ Apostrophes and special characters
- ✅ Case insensitivity
- ✅ Extra whitespace handling
- ✅ Manual aliases
- ✅ Empty/None handling

## Future Enhancements

Potential improvements:
- Fuzzy matching for small spelling differences
- Nickname dictionary (Bob ↔ Robert, Bill ↔ William)
- Middle name/initial handling
- Support for non-Western name formats
- Interactive name mapping tool




