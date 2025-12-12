# Audition Scheduler - Project Context

## Project Overview
A Python CLI tool (`audish`) with an Electron desktop UI for managing conservatory auditions. Currently built for Juilliard and being positioned for expansion to other music conservatories.

**Current Status:** Working prototype in use at Juilliard. Seeking to expand to 2-3 additional conservatories with implementation fees of $8-10K per school plus annual maintenance.

**Primary Goal:** Refine the application to be production-ready and demo-worthy for sales conversations with Curtis, New England Conservatory, and other top music schools.

## Business Context
- **Target Market:** Elite music conservatories (Juilliard, Curtis Institute, New England Conservatory, Manhattan School of Music, etc.)
- **Revenue Model:** Implementation fee ($8-10K) + annual maintenance
- **Current Stage:** Pre-revenue, seeking first paying customer beyond Juilliard
- **Key Decision Maker:** Sam (UX designer/systems thinker, not a developer)
- **Sales Strategy:** Leverage Juilliard as reference account, target 2-3 schools in next 6 months

## Technical Stack

### Core Scheduling Engine (Python)
- **Language:** Python 3.8+
- **Package Management:** pip with pyproject.toml (setuptools)
- **CLI Framework:** Click
- **Excel I/O:** openpyxl
- **Config:** YAML (PyYAML)
- **Date Handling:** python-dateutil
- **Architecture:** Stateless CLI (no database, Excel in → Excel out)

### Desktop UI (Electron)
- **Framework:** Electron 28
- **Frontend:** React (TypeScript) with Vite
- **Main Process:** TypeScript (Node.js)
- **Build Tool:** electron-builder
- **Architecture:** Electron app shells the Python CLI via subprocess

### Deployment Model
- **Python CLI:** Installable via `pip install -e .` (editable install for development)
- **Desktop App:** Standalone installers (.dmg for macOS, .exe for Windows, .AppImage/.deb for Linux)
- **Important Limitation:** Desktop app requires Python + `audish` package to be installed separately (not bundled)

## Key Features

### Scheduling Capabilities
1. **Excel-based Workflow**
   - Input: Applicant data (Slate export) + Faculty availability spreadsheet
   - Output: FinalSchedule.xlsx (adds Date/Time/Order) + Conflicts.xlsx + Metrics.txt

2. **Constraint-Based Scheduling**
   - Degree precedence (BM → MM/GD → AD → DMA)
   - Teacher presence policy (prefer or require 1st/2nd/3rd choice)
   - Same-school spacing (avoid back-to-back from same institution)
   - Double-major coordination (prevent overlap, keep within 24 hours)
   - Faculty availability windows (supports complex time constraints)

3. **Flexible Cadence Patterns**
   - Fixed intervals (15/20/30 minutes)
   - Per-hour caps with half-hour distribution (e.g., 5/hr → [3 at :00, 2 at :30])
   - Special patterns: open blocks, periodic breaks, mid-schedule breaks, buffer time
   - Discipline and degree-specific rules

4. **Faculty Availability Grammar**
   - Natural language notes parsing: "after 1pm", "before 2pm", "10:00-14:00"
   - Day exclusions: "not Friday", "no Fri"
   - Date exclusions: "except 3/1"

### Desktop UI Features
- Drag-and-drop file upload
- Calendar configuration (add/edit audition days)
- Visual results display (scheduled applicants, conflicts, metrics)
- Download output files
- Real-time feedback during scheduling

## Architecture Principles
- **Simplicity over scalability** - Optimize for 2-3 schools, not 100
- **Configuration-driven** - Schools customize via YAML files, not code changes
- **Excel-native workflow** - Admissions staff already live in Excel
- **Stateless execution** - No database, no sessions, just file → process → file
- **Fail-fast validation** - Catch configuration errors early with clear messages

## UX Priorities
1. **Reliability is paramount** - Schedule errors would be catastrophic for admissions departments
2. **Configuration must be approachable** - Admissions staff (not developers) need to modify rules
3. **Error messages must be actionable** - When scheduling fails, explain why and what to fix
4. **Results must be auditable** - Staff need to understand why each applicant got their slot
5. **Process must feel fast** - Even if it takes time, show progress and feedback

## Code Quality Standards
- **Readability matters most** - Future maintainers may be admissions staff with basic Python knowledge
- **YAML over code** - Move complexity into configuration files, not Python
- **Comprehensive conflict reasons** - Never just say "failed", explain exactly why
- **Tested critical paths** - Scheduling logic and constraint validation must have tests
- **Comments explain "why"** - Code should explain business rules, not just implementation

## What to Avoid
- **Premature generalization** - Don't build multi-tenancy when you have 1 customer
- **Feature creep** - Resist adding "nice to haves" before closing deals
- **Over-abstraction** - Simple, clear code beats clever code
- **Breaking YAML compatibility** - Configuration changes must be backward-compatible
- **Technical jargon in UI** - Admissions staff shouldn't see "constraint violation" errors

## Current Priorities (Ranked)

### 1. Demo Polish (HIGHEST)
Must-haves for sales conversations:
- UI looks professional and finished
- No crashes during demos
- Clear, helpful error messages (not stack traces)
- Fast enough to run during live demos (or show metrics from pre-run)
- Results are easy to understand and trust

### 2. Documentation for New Schools
- Step-by-step setup guide for new conservatories
- How to create mapping.yaml for their Slate export
- How to configure rules.yaml for their disciplines
- Troubleshooting guide for common configuration issues

### 3. Missing Features (Validate with Customers)
- What did Juilliard contacts say they need that isn't built yet?
- What would make Curtis or New England Conservatory say "yes"?
- Are there common conservatory workflows we're missing?

### 4. Packaging and Distribution (REVISED)
- Current UX issue: Users must manually select mapping.yaml and rules.yaml files
- **Better approach**: Hardcode school-specific configs, hide from users
- Phase 1: Single school hardcoded (Juilliard) - simplest demo
- Phase 2: School selector dropdown - after first paying customer
- Phase 3: User data directory - after 5+ schools for scalability
- Trade-off: Simplicity and reliability vs. user customization

## Known Issues/Tech Debt

### Technical Debt
- ~~**Electron app doesn't bundle Python**~~ ✅ RESOLVED - Now bundles Python via PyInstaller
- **UI testing is manual via demo rehearsal** - Appropriate for current stage but should be automated after securing 3+ customers
- ~~**Configuration validation is limited**~~ ✅ RESOLVED - Comprehensive validation with helpful error messages
- **No undo/retry in UI** - If scheduling fails, must restart from scratch
- **Faculty name matching is fuzzy** - Sometimes fails on names with special characters

### UX Issues
- **Progress feedback is minimal** - Large schedules appear to hang
- **Conflict explanations could be clearer** - Reason codes are technical
- **No way to preview schedule** - Can't see what would happen before committing
- **Calendar setup is tedious** - Manually adding each day is slow

### Business Risks
- **Single customer dependency** - If Juilliard drops us, we have no revenue
- **No pricing validation** - Haven't tested if $8-10K is right price point
- **Unknown implementation effort** - How long does it take to onboard a new school?

## Domain Knowledge

### Conservatory Context
- **Audition season is short** - Typically Feb-March, schedules must be perfect
- **Stakes are extremely high** - Wrong schedule affects students' entire careers
- **Faculty are protective of their time** - Availability constraints are non-negotiable
- **Admissions staff are overworked** - Tool must save time, not add complexity
- **Each school is unique** - Disciplines, degrees, and processes vary significantly

### Common Disciplines (from Juilliard rules.yaml)
- Strings: Violin, Viola, Cello, Double Bass
- Woodwinds: Flute, Oboe, Clarinet, Bassoon
- Brass: Trumpet, Trombone, French Horn, Tuba, Bass Trombone
- Piano (split by external vs. current Juilliard students)
- Voice, Organ, Guitar, Harp, Percussion
- Composition, Conducting, Jazz Studies, Historical Performance

### Degree Types
- **BM** (Bachelor of Music) - Undergraduate, typically longer auditions
- **MM** (Master of Music) - Graduate
- **GD** (Graduate Diploma) - Post-masters
- **AD** (Artist Diploma) - Advanced performance study
- **DMA** (Doctor of Musical Arts) - Highest degree

---

## For AI Assistants Working on This Project

### Primary User Context
- **Sam is a UX designer**, NOT a developer
- **Assume minimal technical knowledge** - Explain architectural decisions in plain language
- **Sam is entrepreneurial** but needs guidance turning ideas into sustainable business
- **Don't assume Sam knows what he's talking about** when he suggests technical approaches
- **Ask clarifying questions** about business requirements before diving into code

### Communication Preferences
- **Explain WHY, not just WHAT** - "We should do X because it solves Y problem for admissions staff"
- **Flag business implications** - "This approach means longer onboarding for new schools"
- **Warn about complexity upfront** - "This will add 2 weeks of development time"
- **Suggest simpler alternatives** - "Instead of rebuilding X, we could..."
- **Use analogies to UX/design** - Sam thinks in user flows, not data structures

### Development Approach
- **Frame changes in user value** - "This lets admissions staff fix mistakes without re-running"
- **Consider "good enough for 3 customers"** - Don't over-engineer for scale
- **Remember this is built to SELL** - Features must be demo-worthy, not just functional
- **Prioritize reliability over features** - One bug in a demo kills the deal
- **Think about onboarding effort** - How hard is it for a new school to adopt this?

### Code Review Focus
1. **Accessibility (WCAG 2.1 AA)** - Institutions care deeply about compliance
2. **User experience quality** - Does this feel professional and trustworthy?
3. **Maintainability** - Could an admissions staff member with basic Python skills understand this?
4. **Data integrity** - Scheduling errors would be catastrophic
5. **Error messages** - Are they actionable for non-technical users?
6. **Configuration complexity** - Can schools customize without developer help?

### Important Reminders
- **The bottleneck is sales, not features** - Every hour coding should serve closing deals
- **Juilliard is the proof point** - Use them as reference, not just feedback source
- **Conservatories are conservative** - They value reliability over innovation
- **Implementation is billable work** - Don't make setup so easy that schools don't pay for it
- **The UI is the sales tool** - CLI is powerful, but UI closes deals

### Questions to Ask Before Building
1. "Does this help close the next 2-3 deals?" - If no, deprioritize
2. "What's the simplest version that demonstrates value?" - Start there
3. "How does this affect the demo/sales conversation?" - Consider optics
4. "What happens if this breaks during a demo?" - Assess risk
5. "Could a school do this themselves with our docs?" - Balance ease vs. billable hours

### When Sam is Confused or Stuck
- **Probe for the business goal** - What problem is he trying to solve for customers?
- **Offer 2-3 options with trade-offs** - Help him make informed decisions
- **Explain in UX terms** - "This is like choosing between a wizard and advanced mode"
- **Validate with customer needs** - "Did Juilliard ask for this, or are we guessing?"
- **Suggest talking to users first** - "Before building this, let's ask Curtis what they need"

---

## Project Structure Reference

```
audish/                      # Python package (scheduling engine)
  __init__.py
  cli.py                     # Click CLI entrypoint
  mapping.py                 # Column normalization (Excel → logical fields)
  faculty.py                 # Faculty availability parsing
  faculty_names.py           # Name matching/normalization
  rules.py                   # Slot generation from rules.yaml
  scheduler.py               # Core greedy scheduling algorithm
  io_excel.py                # Excel input/output
  reason_codes.py            # Conflict reason constants

electron/                    # Desktop UI
  main/                      # Electron main process (TypeScript)
  renderer/                  # React frontend
    src/
      components/            # UI components
      lib/                   # Utilities and state management
  package.json

schools/juilliard/          # School-specific configuration
  mapping.yaml               # Excel column mappings
  rules.yaml                 # Scheduling rules and calendar

tests/                       # Python tests (pytest)
  test_faculty.py
  test_rules.py
  test_scheduler.py

output/                      # Generated files (gitignored)
  FinalSchedule.xlsx
  Conflicts.xlsx
  Metrics.txt

Documentation files:
  README.md                  # CLI usage
  QUICKSTART.md              # Electron UI setup
  PACKAGING.md               # Distribution guide
  TESTER_INSTRUCTIONS.md     # For beta testers
```

---

## Next Steps for Productization

### Before Next Demo
1. Polish error messages in UI (no stack traces)
2. Add progress indicator for long-running schedules
3. Make conflict reasons more user-friendly
4. Test packaging on clean machine (verify Python dependency is clear)
5. Create 2-page sales sheet highlighting Juilliard success

### Before Approaching Curtis/NEC
1. Create template mapping.yaml and rules.yaml for new schools
2. Write "Implementation Guide" documenting onboarding process
3. Estimate: How many hours to configure a new school?
4. Decide: Is setup included in $8-10K, or separate professional services?
5. Practice demo with someone who doesn't know the system

### Technical Improvements (After Validating Demand)
1. Consider bundling Python with Electron app
2. Add configuration validation with helpful error messages
3. Build "schedule preview" mode (dry run without committing)
4. Create audit log showing why each applicant got their slot
5. Add automated tests for UI critical paths

### Strategic Questions to Answer
1. What's the actual time to onboard a new school?
2. Are we priced correctly at $8-10K?
3. Should we offer SaaS (web app) instead of installed software?
4. What support/training do schools need post-implementation?
5. How do we handle configuration changes mid-audition-season?