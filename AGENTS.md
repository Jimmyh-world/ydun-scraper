# AI-Optimized Template System - Template Repository

<!--
TEMPLATE_VERSION: 1.4.2
TEMPLATE_SOURCE: /home/jimmyb/templates/AGENTS.md.template
LAST_SYNC: 2025-10-04
SYNC_CHECK: This IS the master repository - other projects sync FROM here
-->

**STATUS: PRODUCTION** - Last Updated: 2025-10-04

## Repository Information
- **GitHub Repository**: https://github.com/ydun-code-library/Rules-and--templates
- **Local Directory**: `/home/jimmyb/templates`
- **Primary Purpose**: Maintain and evolve the AI-optimized template system for all projects

## Important Context

This repository IS the single source of truth for all project templates. When AI assistants work in other projects, they reference templates FROM this repository.

**Critical Responsibility**: Changes here propagate to ALL projects using these templates. Every modification must be tested, validated, and properly versioned.

**Meta-Documentation**: This AGENTS.md documents the template repository itself, using the very templates it provides. This ensures the template system follows its own standards ("eating our own dog food").

**Phase 2 Plan**: See `PHASE-2-PLAN.md` for the complete implementation plan for AI assistant auto-discovery and compliance audit system. Ready for execution in a fresh session.

## For AI Assistants: Project Compliance Audit Workflow

**When user says**: *"check templates directory"* OR *"make sure we're following the rules"* OR *"are we up to date with templates?"*

**Your mission**: Audit the current project against this template system

### Step 1: Understand Your Context

```bash
# You are currently in: [determine current working directory]
# Templates master location: /home/jimmyb/templates/
# Task: Compare current project to template standards
```

**Possible scenarios:**
- 🆕 **New project** - No AGENTS.md → Needs initialization
- ⚠️ **Existing project, out of date** - Has AGENTS.md but old version
- 📝 **Using templates but incomplete** - Has AGENTS.md with unfilled placeholders
- ❌ **Not using templates** - No AGENTS.md, no structure
- ✅ **Fully compliant** - Up to date and complete

### Step 2: Run Compliance Checks

Execute these checks **automatically** (don't just suggest - actually run them):

#### Check 1: Does AGENTS.md Exist?
```bash
test -f ./AGENTS.md && echo "✅ AGENTS.md present" || echo "❌ AGENTS.md MISSING"
```
- ❌ **If missing** → Project needs initialization (see ~/templates/init-project.md)
- ✅ **If present** → Proceed to Check 2

#### Check 2: Does AGENTS.md Have Version Header?
```bash
grep "TEMPLATE_VERSION:" ./AGENTS.md
```
- ❌ **If missing** → Old format (pre-v1.4), needs migration
- ✅ **If present** → Proceed to Check 3

#### Check 3: Are Templates Up to Date?
```bash
~/templates/tools/check-version.sh
```
- **Exit 0** → ✅ Up to date
- **Exit 1** → ⚠️ Out of date → Show what's new from CHANGELOG
- **Exit 2** → ❌ Error → Report issue

#### Check 4: Are 8 Core Principles Present?
```bash
grep -c "^### [1-8]\." ./AGENTS.md
```
- **Count = 8** → ✅ All principles present
- **Count < 8** → ⚠️ Missing principles → Suggest sync

#### Check 5: Are Placeholders Filled?
```bash
grep "\[PROJECT_NAME\]\|\[GITHUB_URL\]\|PROJECT_SPECIFIC_CONTEXT - Replace with" ./AGENTS.md
```
- **Found placeholders** → ⚠️ Unfilled sections → List which ones need filling
- **No placeholders** → ✅ Customized

#### Check 6: Is CLAUDE.md Present?
```bash
test -f ./CLAUDE.md && echo "✅ Present" || echo "⚠️ Missing"
```
- ❌ **Missing** → Suggest copying from ~/templates/CLAUDE.md.template
- ✅ **Present** → Good

#### Check 7: Is JIMMYS-WORKFLOW.md Present or Referenced?
```bash
test -f ./JIMMYS-WORKFLOW.md || grep -q "JIMMYS-WORKFLOW.md" ./AGENTS.md
```
- ❌ **Neither** → Suggest copying or referencing
- ✅ **Present/Referenced** → Good

### Step 3: Generate Compliance Report

**Format your report like this:**

```
========================================
  Template Compliance Audit
========================================

Project: [PROJECT_NAME from AGENTS.md or directory name]
Location: [current directory path]
Audit Date: [YYYY-MM-DD HH:MM]

CHECKS:
-------
✅ AGENTS.md:              Present (v1.2)
⚠️  Template Version:      OUT OF DATE (v1.2 → v1.4.1)
✅ CLAUDE.md:              Present
✅ JIMMYS-WORKFLOW.md:     Referenced (../JIMMYS-WORKFLOW.md)
⚠️  8 Core Principles:     Only 6 found (missing: YAGNI, Fix Now)
⚠️  Placeholders:          3 unfilled (SERVICE_OVERVIEW, KNOWN_ISSUES, COMMON_PATTERNS)
✅ GitHub Workflow:        gh CLI referenced

SUMMARY:
--------
Status: ⚠️  NEEDS UPDATE

Issues Found:
1. Template version out of date (v1.2 → v1.4.1)
2. Missing 2 principles (YAGNI, Fix Now)
3. 3 sections have unfilled placeholders

RECOMMENDATIONS:
----------------
1. Run: ~/templates/tools/sync-templates.sh
   → This will update to v1.4.1 and add missing principles
   → Your customizations in PROJECT_SPECIFIC sections will be preserved

2. Fill remaining placeholders:
   - SERVICE_OVERVIEW (describe what this project does)
   - KNOWN_ISSUES (list current blockers/bugs)
   - COMMON_PATTERNS (add code examples used in project)

3. Review CHANGELOG for new features:
   ~/templates/CHANGELOG.md

========================================
```

### Step 4: Offer Actions

**Based on findings, proactively offer:**

**If Missing AGENTS.md:**
> "This project has no AGENTS.md. I can initialize it with templates. Shall I:
> 1. Copy ~/templates/AGENTS.md.template to ./AGENTS.md
> 2. Help you fill in the placeholders
> 3. Copy CLAUDE.md and JIMMYS-WORKFLOW.md
> Would you like me to proceed?"

**If Out of Date:**
> "Templates are out of date (v1.2 → v1.4.1).
> What's new in v1.4.1: [show from CHANGELOG]
> Shall I run ~/templates/tools/sync-templates.sh to update?
> Your customizations will be preserved."

**If Unfilled Placeholders:**
> "Found 3 unfilled placeholder sections. Shall I help you fill them?
> 1. SERVICE_OVERVIEW - What does this project do?
> 2. KNOWN_ISSUES - Any current bugs/blockers?
> 3. COMMON_PATTERNS - Any code patterns to document?"

**If Fully Compliant:**
> "✅ Project is template-compliant!
> - AGENTS.md up to date (v1.4.1)
> - All 8 principles present
> - All sections customized
> - CLAUDE.md and workflow present
> Great work maintaining standards!"

### Step 5: Quick Audit Mode

**For faster checks, also support:**
```bash
~/templates/tools/audit-project.sh --quick
# Shows: ✅ Compliant OR ⚠️ Issues found (run without --quick for details)
```

---

## Key Insight: Discovery Pattern

**The magic happens when AI reads ~/templates/AGENTS.md:**

```
User: "hey claude, check templates directory"
          ↓
AI: Reads ~/templates/AGENTS.md
          ↓
AI: Sees "For AI Assistants: Project Compliance Audit Workflow"
          ↓
AI: "Ah! I should run these 7 checks!"
          ↓
AI: Executes checks, generates report
          ↓
AI: Offers remediation based on findings
```

**This makes ~/templates/ DISCOVERABLE and ACTIONABLE!**

Ready to implement!

### 1. KISS (Keep It Simple, Stupid)
- Keep templates simple and easy to customize
- Avoid over-complicated placeholder systems
- Question every new template field - is it truly needed?
- Simple templates = easier adoption

### 2. TDD (Test-Driven Development)
- Test template changes in real projects before committing
- Validate version control scripts with actual projects
- Verify sync tools preserve customizations
- Never release untested template changes

### 3. Separation of Concerns (SOC)
- Each template file has single responsibility
- AGENTS.md = comprehensive guidelines
- CLAUDE.md = quick reference
- JIMMYS-WORKFLOW.md = workflow documentation
- Don't mix concerns across files

### 4. DRY (Don't Repeat Yourself)
- Shared sections across templates should be referenced, not duplicated
- Use protected section markers to avoid duplication during sync
- Common patterns documented once in JIMMYS-WORKFLOW.md

### 5. Documentation Standards
- Always include actual dates when updating templates
- Use objective, factual language only
- Avoid marketing terms like "production-ready", "world-class"
- Document current state clearly
- Update CHANGELOG.md for every version bump

### 6. Jimmy's Workflow (Red/Green Checkpoints)
**MANDATORY for all template changes**

Use the Red/Green/Blue checkpoint system when modifying templates:

- 🔴 **RED (IMPLEMENT)**: Modify template files
- 🟢 **GREEN (VALIDATE)**: Test in real project, verify sync tools work
- 🔵 **CHECKPOINT**: Bump VERSION, update CHANGELOG, commit

**Critical Rules:**
- NEVER skip validation in real project
- NEVER bump VERSION without testing changes
- ALWAYS update CHANGELOG.md
- ALWAYS test sync tools after template changes

**Reference**: See **JIMMYS-WORKFLOW.md** for complete workflow system

### 7. YAGNI (You Ain't Gonna Need It)
- Don't add placeholder fields until actually needed
- Resist urge to create templates for every possible project type
- Build templates based on actual usage patterns
- Delete unused template sections

### 8. Fix Now, Not Later
- Fix template issues immediately when discovered in projects
- Update VERSION and sync to all projects
- Don't let template bugs accumulate
- When project reports template issue, fix in master and propagate

**Exception**: If fix requires breaking changes, document migration path in CHANGELOG.md

## GitHub Workflow

### Use GitHub CLI (gh) for All GitHub Operations

**Standard Tool**: Use `gh` CLI for all GitHub interactions

**Common Operations for Template Repo:**
```bash
# Pull Requests
gh pr create --title "feat: add principle #9" --body "Description"
gh pr checks                        # Check CI/CD status

# Issues
gh issue create --title "Template bug: placeholder missing" --body "Details"
gh issue list                       # Track template issues

# Releases (when major version)
gh release create v2.0.0 --title "Major: 9 Core Principles" --notes "See CHANGELOG.md"
```

## Service Overview

<!-- PROJECT_SPECIFIC START: SERVICE_OVERVIEW -->
**Purpose**: This repository maintains the AI-optimized template system used across all Jimmy's projects.

**Key Responsibilities:**
- Maintain AGENTS.md.template (comprehensive AI assistant guidelines)
- Maintain CLAUDE.md.template (quick reference)
- Maintain JIMMYS-WORKFLOW.md (Red/Green checkpoint system)
- Maintain version control system (VERSION, CHANGELOG, sync tools)
- Provide technology-specific templates (Cardano, Solidity)
- Ensure templates follow 8 Core Development Principles

**Template Distribution Model:**
- Projects copy templates to their roots
- Projects fill in placeholders with project-specific info
- Projects use version control tools to stay synced
- Protected sections preserve customizations during sync
<!-- PROJECT_SPECIFIC END: SERVICE_OVERVIEW -->

## Current Status

<!-- PROJECT_SPECIFIC START: CURRENT_STATUS -->
🔄 **Active Development** - 90% Complete

**Template System:**
- ✅ Core templates (AGENTS, CLAUDE, WORKFLOW)
- ✅ Version control system (VERSION, CHANGELOG, tools)
- ✅ 8 Core Development Principles defined
- ✅ Protected section markers for customization preservation
- ✅ check-version.sh (version detection)
- ✅ sync-templates.sh Phase 1 (JIMMYS-WORKFLOW auto-sync)
- 🔄 sync-templates.sh Phase 2 (AGENTS.md smart merge) - planned
- ✅ Cardano-specific templates (comprehensive)
- ⚪ Solidity-specific templates (basic - needs expansion)
- ⚪ Project type variants (planned but not created)

**Repository Hygiene:**
- ✅ Legacy files archived
- ✅ Directory structure cleaned
- ✅ Path references updated
- 🔄 Git repository (in progress)
<!-- PROJECT_SPECIFIC END: CURRENT_STATUS -->

## Technology Stack

**Infrastructure:**
- **Language**: Bash (scripts), Markdown (documentation)
- **Version Control**: Git + GitHub
- **Distribution**: Direct file copy + reference
- **Automation**: Bash scripts (check-version.sh, sync-templates.sh)

**Template Technologies:**
- **Markdown**: All documentation and templates
- **HTML Comments**: Version headers and protected section markers
- **Placeholders**: `[PLACEHOLDER]` syntax for find-and-replace

## Build & Test Commands

### Development
```bash
# No build required (pure documentation/templates)

# Test templates in new project
cd /path/to/test-project
cp ~/templates/AGENTS.md.template ./AGENTS.md
# Fill placeholders and verify

# Test version control scripts
~/templates/tools/check-version.sh        # From project directory
~/templates/tools/sync-templates.sh --dry-run  # Preview sync

# Validate version consistency
cat ~/templates/VERSION                   # Should match all template headers
```

### Quality Checks
```bash
# Check for unfilled placeholders in templates
grep "\[.*\]" ~/templates/AGENTS.md.template | grep -v "http" | grep -v "example"

# Verify protected section markers are paired
STARTS=$(grep -c "PROJECT_SPECIFIC START:" ~/templates/AGENTS.md.template)
ENDS=$(grep -c "PROJECT_SPECIFIC END:" ~/templates/AGENTS.md.template)
test "$STARTS" -eq "$ENDS" && echo "✅ Markers paired" || echo "❌ Marker mismatch"

# Check script permissions
test -x ~/templates/tools/check-version.sh && echo "✅ check-version.sh executable"
test -x ~/templates/tools/sync-templates.sh && echo "✅ sync-templates.sh executable"
```

### Version Management
```bash
# Bump version (when making template changes)
echo "1.5" > ~/templates/VERSION

# Update changelog
vim ~/templates/CHANGELOG.md  # Add new version section

# Update template version headers
# Manually update TEMPLATE_VERSION in affected files
```

## Repository Structure

```
/home/jimmyb/templates/
├── README.md                       # This file - main entry point
├── AGENTS.md                       # Repository self-documentation (meta!)
├── CLAUDE.md                       # Quick reference for template work
├── VERSION                         # Current version number (1.4)
├── CHANGELOG.md                    # Version history and migration guides
├── AGENTS.md.template              # Template for projects
├── CLAUDE.md.template              # Quick reference template
├── AGENTS-TEMPLATE-GUIDE.md        # Comprehensive usage guide
├── JIMMYS-WORKFLOW.md              # Complete workflow system (v1.1)
├── JIMMYS-WORKFLOW-TEMPLATE.md     # Task planning template (v1.0)
├── init-project.md                 # Initialization checklist
├── tools/                          # Version control automation
│   ├── check-version.sh            # Detect version mismatches
│   └── sync-templates.sh           # Smart sync (Phase 1)
├── cardano/                        # Cardano/Aiken templates
│   ├── AGENTS.md                   # Cardano template collection docs
│   ├── aiken-development-rules.md
│   ├── cardano-security-patterns.md
│   ├── validator-design-guide.md
│   └── ... (10+ files)
├── solidity/                       # Solidity/Ethereum templates
│   ├── solidity_cursor_rules.md
│   ├── solidity_design_guide.md
│   └── solidity_upgrade_guide.md
├── project-types/                  # Project type variants (planned)
│   └── README.md
└── archive/                        # Legacy files
    └── legacy/                     # Old prompts/PDFs from May 2025
```

## Development Workflow

### Adding a New Principle (Example: Principle #9)

**Using Jimmy's Workflow:**

#### 🔴 RED: IMPLEMENT
1. Add principle to AGENTS.md.template (after Fix Now)
2. Add principle to CLAUDE.md.template
3. Update AGENTS-TEMPLATE-GUIDE.md references (8 → 9)
4. Update this AGENTS.md (add principle above)
5. Bump VERSION: 1.4 → 1.5
6. Update CHANGELOG.md with new version entry

#### 🟢 GREEN: VALIDATE
```bash
# Test in real project
cd ~/test-project
cp ~/templates/AGENTS.md.template ./AGENTS.md
# Fill placeholders
# Verify principle #9 is present and clear

# Test version detection
~/templates/tools/check-version.sh
# Should show test project is out of date (1.4 → 1.5)

# Verify CHANGELOG is accurate
cat ~/templates/CHANGELOG.md | grep "Version 1.5"

# Check no broken references
grep "\[PLACEHOLDER\]" ~/templates/AGENTS.md.template | grep -v example
# Should only show intentional placeholders
```

#### 🔵 CHECKPOINT: New Principle Added
- **Status**: 🔵 COMPLETE
- **Validated**: Tested in real project, version tools work
- **Rollback**: `git revert [hash]` + restore VERSION file
- **Next**: Notify all active projects to sync templates

### Fixing Template Bug

**Using Fix Now Principle:**

#### Found: Issue in template placeholder
```bash
# FIX IMMEDIATELY (don't defer!)
vim ~/templates/AGENTS.md.template  # Fix the issue

# Test fix
cd ~/test-project && cp ~/templates/AGENTS.md.template ./AGENTS.md.test

# If fix is non-breaking (clarification only):
# - Update LAST_UPDATED date in template
# - No VERSION bump needed
# - Commit: "fix: clarify placeholder description"

# If fix is breaking (changes structure):
# - Bump VERSION (e.g., 1.4 → 1.4.1 for patch, 1.4 → 1.5 for minor)
# - Update CHANGELOG.md
# - Commit: "fix(breaking): update template structure"
```

### Testing Templates

**Before Committing Template Changes:**
1. Copy updated templates to test project
2. Fill placeholders completely
3. Ask AI assistant to read AGENTS.md
4. Verify AI understands all principles
5. Test Jimmy's Workflow invocation
6. Verify no placeholder confusion
7. Run version check/sync scripts

## Known Issues & Technical Debt

<!-- PROJECT_SPECIFIC START: KNOWN_ISSUES -->
### 🔴 Critical Issues
None currently

### 🟡 Important Issues
1. **Phase 2 Smart Merge Not Implemented** - sync-templates.sh currently provides manual guidance for AGENTS.md sync. Full smart merge with protected section preservation is planned but not yet built.

### 📝 Technical Debt
1. **Project Type Templates Missing** - project-types/ directory describes templates that don't exist yet (frontend-service, backend-service, etc.). Will create as needed when patterns emerge.
2. **Solidity Templates Minimal** - solidity/ directory has basic guides but could be expanded with more comprehensive patterns (similar to Cardano collection).
3. **No CI/CD for Template Validation** - Could add GitHub Actions to test templates in sample project on each commit.
<!-- PROJECT_SPECIFIC END: KNOWN_ISSUES -->

## Project-Specific Guidelines

<!-- PROJECT_SPECIFIC START: PROJECT_SPECIFIC_GUIDELINES -->
### Template Modification Rules

**When Adding New Principle:**
1. Update AGENTS.md.template (add principle with full explanation)
2. Update CLAUDE.md.template (add to quick reference list)
3. Update AGENTS-TEMPLATE-GUIDE.md (update all "N Core" references)
4. Update this AGENTS.md (document the principle for template work)
5. Update cardano/AGENTS.md if Cardano-specific implications
6. Bump VERSION file
7. Add version entry to CHANGELOG.md with migration guide
8. Test in real project
9. Commit with message: "feat: add principle #N - [Name]"

**When Adding New Template Section:**
1. Add to AGENTS.md.template with clear placeholder
2. Add PROJECT_SPECIFIC marker if customizable
3. Update AGENTS-TEMPLATE-GUIDE.md with explanation
4. Test in real project
5. Update VERSION + CHANGELOG if structural change
6. Commit

**When Fixing Template Bug:**
1. Fix immediately (Fix Now principle!)
2. Test fix in project
3. Decide: Patch (1.4.1) or Minor (1.5) version bump
4. Update CHANGELOG.md
5. Notify active projects to sync

### Testing Requirements

**Before Committing Template Changes:**
- [ ] Copied to test project and filled placeholders
- [ ] AI assistant successfully read and understood
- [ ] All placeholders are clear and well-documented
- [ ] No broken markdown syntax
- [ ] Version tools work (check-version.sh, sync-templates.sh)
- [ ] CHANGELOG.md updated
- [ ] VERSION file bumped (if needed)

**Coverage Requirements:**
- Test in at least 1 real project before releasing
- Verify sync tools preserve customizations
- Check markdown renders correctly on GitHub

### Version Bump Policy

**Patch (1.4.0 → 1.4.1):**
- Typo fixes in templates
- Placeholder clarifications
- Documentation improvements
- No structural changes

**Minor (1.4 → 1.5):**
- New template sections added
- New principles added
- Tool improvements (scripts)
- Non-breaking enhancements

**Major (1.x → 2.0):**
- Breaking template structure changes
- Removal of principles
- Major reorganization
- Requires migration work in all projects

<!-- PROJECT_SPECIFIC END: PROJECT_SPECIFIC_GUIDELINES -->

## Common Patterns & Examples

<!-- PROJECT_SPECIFIC START: COMMON_PATTERNS -->
### Pattern 1: Adding Technology-Specific Template Collection

**Example**: The cardano/ directory

**Process:**
1. Create subdirectory: `mkdir cardano`
2. Create AGENTS.md for collection: `cardano/AGENTS.md`
3. Add technology-specific guides
4. Document in main README.md
5. Reference from AGENTS-TEMPLATE-GUIDE.md

### Pattern 2: Version Bump Workflow

**When bumping version:**
```bash
# 1. Update version file
echo "1.5" > ~/templates/VERSION

# 2. Update CHANGELOG.md
vim ~/templates/CHANGELOG.md
# Add ## Version 1.5 section with changes

# 3. Update template headers
sed -i 's/TEMPLATE_VERSION: 1.4/TEMPLATE_VERSION: 1.5/' AGENTS.md.template CLAUDE.md.template

# 4. Update guide version
sed -i 's/Template System Version.*1.4/Template System Version: 1.5/' AGENTS-TEMPLATE-GUIDE.md

# 5. Test
cd ~/test-project
~/templates/tools/check-version.sh  # Should detect 1.4 → 1.5

# 6. Commit
git add .
git commit -m "chore: bump template version to 1.5"
```
<!-- PROJECT_SPECIFIC END: COMMON_PATTERNS -->

## Dependencies & Integration

<!-- PROJECT_SPECIFIC START: DEPENDENCIES -->
### External Services
- **GitHub**: Template repository hosting and distribution
- **Git**: Version control for templates themselves

### Related Projects
All projects using these templates integrate with this repository:
- Reference templates via file copy
- Track version with check-version.sh
- Sync updates with sync-templates.sh
- Preserve customizations via protected sections
<!-- PROJECT_SPECIFIC END: DEPENDENCIES -->

## Environment Variables

<!-- PROJECT_SPECIFIC START: ENVIRONMENT_VARIABLES -->
```bash
# No environment variables required
# Templates are static files distributed via filesystem
```
<!-- PROJECT_SPECIFIC END: ENVIRONMENT_VARIABLES -->

## Troubleshooting

<!-- PROJECT_SPECIFIC START: TROUBLESHOOTING -->
### Common Issues

**Issue**: Project can't find templates
**Solution**: Verify path ~/templates/ exists and templates are present

**Issue**: check-version.sh reports error
**Solution**:
- Ensure PROJECT_AGENTS_FILE exists in project
- Verify TEMPLATE_VERSION comment exists in project's AGENTS.md
- Check ~/templates/VERSION file exists

**Issue**: sync-templates.sh doesn't preserve customizations
**Solution**:
- Verify PROJECT_SPECIFIC markers are present in project's AGENTS.md
- Check backup was created in .template-sync-backup/
- For now, Phase 2 not implemented - follow manual merge instructions

**Issue**: Added new principle but projects don't see it
**Solution**:
- Bump VERSION file
- Update CHANGELOG.md
- Projects run check-version.sh to detect
- Projects run sync-templates.sh to update
<!-- PROJECT_SPECIFIC END: TROUBLESHOOTING -->

## Resources & References

### Documentation
- README.md - Main collection overview
- AGENTS-TEMPLATE-GUIDE.md - Comprehensive usage guide
- CHANGELOG.md - Version history
- init-project.md - Project initialization checklist

### External Resources
- https://agents.md/ - Agent configuration standard
- https://claude.ai/claude-code - Claude Code documentation

## Template Version Management

**This IS the master repository** - other projects sync FROM here, not the reverse.

**When making changes:**
1. Modify templates locally
2. Test in real project
3. Bump VERSION if needed
4. Update CHANGELOG.md
5. Commit and push
6. Notify active projects (or they detect via check-version.sh)

**Version Control Files:**
- `VERSION` - Current system version (1.4)
- `CHANGELOG.md` - Complete history
- Template headers - Version tracking in each file

## Important Reminders for AI Assistants

1. **Always use Jimmy's Workflow** for template modifications
2. **Follow TDD** - Test changes in real project before committing
3. **Keep it KISS** - Don't over-complicate templates
4. **Apply YAGNI** - Don't add fields/sections until actually needed
5. **Use GitHub CLI** - Use `gh` for issues, PRs, releases
6. **Fix Now** - Template bugs must be fixed immediately and propagated
7. **Document dates** - Include actual dates in CHANGELOG
8. **Validate explicitly** - Test in real project, don't assume
9. **Never skip checkpoints** - Version bump → CHANGELOG → Test → Commit
10. **Update this file** - Keep this AGENTS.md current as template system evolves

---

**This document follows the [agents.md](https://agents.md/) standard for AI coding assistants.**

**Template Version**: 1.4.1
**Last Updated**: 2025-10-04
