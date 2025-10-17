# Claude AI Assistant Instructions

<!--
TEMPLATE_VERSION: 1.4.2
TEMPLATE_SOURCE: /home/jimmyb/templates/CLAUDE.md.template
-->

Please refer to **AGENTS.md** for complete development guidelines for the template repository.

This project follows the [agents.md](https://agents.md/) standard for AI coding assistants.

## Quick Reference

### Repository Purpose

**This IS the master template repository** - all other projects sync FROM here.

**Primary Task**: Maintain and evolve AI-optimized templates for all projects.

### Core Development Principles
1. **KISS** - Keep templates simple
2. **TDD** - Test changes in real projects
3. **SOC** - Each template has single responsibility
4. **DRY** - Don't duplicate across templates
5. **Documentation Standards** - Factual, dated, objective
6. **Jimmy's Workflow** - Red/Green Checkpoints (MANDATORY for template changes)
7. **YAGNI** - Don't add template fields until needed
8. **Fix Now** - Template bugs must be fixed immediately

### Jimmy's Workflow for Template Changes
Use for ALL template modifications:
- 🔴 **RED**: IMPLEMENT (modify templates)
- 🟢 **GREEN**: VALIDATE (test in real project)
- 🔵 **CHECKPOINT**: GATE (bump VERSION, update CHANGELOG, commit)

**Invoke**: *"Let's use Jimmy's Workflow to execute this plan"*

**Reference**: See **JIMMYS-WORKFLOW.md** for complete system

### Critical Rules for Template Work
- ✅ Test template changes in REAL project before committing
- ✅ Bump VERSION when making changes
- ✅ Update CHANGELOG.md for every version
- ✅ Use GitHub CLI (`gh`) for repo operations
- ✅ Verify protected section markers are paired
- ❌ Never commit untested template changes
- ❌ Never bump VERSION without updating CHANGELOG
- ❌ Never skip validation in real project
- ❌ Never add template complexity without clear need

### GitHub Operations
```bash
# Issues
gh issue create --title "Bug in AGENTS.md.template" --body "Details"
gh issue list

# Pull Requests
gh pr create --title "feat: add new principle" --body "Description"
gh pr checks

# Releases (major versions)
gh release create v2.0.0 --title "Major Update" --notes "See CHANGELOG.md"
```

### Common Commands
```bash
# Test Templates
cd ~/test-project
cp ~/templates/AGENTS.md.template ./AGENTS.md
# Fill placeholders and test with AI assistant

# Test Version Tools
~/templates/tools/check-version.sh        # From project dir
~/templates/tools/sync-templates.sh --dry-run  # Preview sync

# Validate Quality
grep "\[.*\]" ~/templates/AGENTS.md.template | grep -v http
# Should only show intentional placeholders

# Bump Version
echo "1.5" > ~/templates/VERSION
vim ~/templates/CHANGELOG.md  # Add version entry
```

### Version Bump Checklist
When modifying templates:
- [ ] Modify template files
- [ ] Test in real project
- [ ] Decide version bump (patch/minor/major)
- [ ] Update VERSION file
- [ ] Update CHANGELOG.md
- [ ] Update template version headers (if major/minor)
- [ ] Commit: "feat: [description]" or "fix: [description]"
- [ ] Push to GitHub
- [ ] Notify active projects (or they detect via check-version.sh)

---

*Last updated: 2025-01-04*
*Template Version: 1.4*
