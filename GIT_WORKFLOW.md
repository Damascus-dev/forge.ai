# Forge Git Workflow — Trunk-Based Development

## Strategy: Trunk-Based Development (TBD)

**Why TBD for solo dev:**
- ✓ Simpler workflow (one branch: `main`)
- ✓ Faster iteration (commit, test, push immediately)
- ✓ Clearer history (linear, no merge conflicts)
- ✓ Better for CI/CD (every commit is deployable)
- ✓ Less cognitive overhead (focus on code, not process)
- ✗ Requires discipline: never commit broken code

**Alternative (not chosen):** Feature branches require PR reviews, which slows solo dev without adding value.

---

## Commit Strategy

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

Fixes #<issue-number> (optional)
```

**Types:**
- `feat`: New feature (React Flow, semantic logging, etc.)
- `fix`: Bug fix (error handling, broken API, etc.)
- `refactor`: Code restructuring (no functional change)
- `perf`: Performance optimization
- `test`: Test additions or fixes
- `docs`: Documentation updates
- `chore`: Deps, build config, infrastructure
- `ci`: CI/CD changes

**Scopes:**
- `api`: FastAPI backend
- `agents`: Agent runtime
- `chaos`: Chaos engine
- `events`: Event store
- `frontend`: React UI
- `logging`: Semantic logging system
- `docker`: Docker infrastructure
- `docs`: Documentation

**Examples:**
```
feat(logging): add semantic embedding to postgres

- Created postgres schema for actions + embeddings
- Integrated Ollama nomic-embed-text for local embeddings
- Background worker generates embeddings async

Fixes #12

---

fix(api): add error handling to experiment endpoints

- Wrap all endpoints in try/catch
- Return proper 400/500 HTTP responses
- Add structured logging for failures

---

feat(frontend): implement react-flow visualization

- Added WorkflowCanvas component
- Render experiment nodes with spawn/terminate animations
- Added chaos event visualization (latency, packet loss)

---

docs: update bootstrap with semantic logging setup

- Added SEMANTIC_LOGGING.md
- Updated README with new embeddings requirements
- Documented weekly summarization workflow
```

### Commit Frequency

- **Small changes:** Commit immediately after testing (1-2 hours of work)
- **Feature completion:** Commit when feature is functionally complete
- **Bug fixes:** Commit same-day (don't accumulate fixes)
- **Documentation:** Commit with related code (not separate)

### Branch Strategy

```
main (production-ready code)
  ├─ Never force-push to main
  ├─ All code must pass 13/13 tests before commit
  ├─ Tag releases: v1.0.0, v1.0.1, etc.
  └─ Commit every 1-2 days during active development
```

**No feature branches during development** (TBD principle).
**If you need to experiment:** Create temporary local branch, delete before pushing.

---

## Daily Workflow

### Morning (Start of Session)

```bash
cd /media/davinci/New\ Volume/reccon.ai
git pull                          # Get any changes (unlikely in solo dev)
git status                        # Check working tree
python -m pytest tests/ -v        # Verify tests still pass
```

### During Session

```bash
# Make code changes
git add <modified files>          # Stage changes
git commit -m "feat(scope): description"  # Commit
git push                          # Push immediately (don't accumulate commits)
```

### End of Session

```bash
git log --oneline -5              # Review today's commits
git status                        # Ensure clean working tree
# Optional: git tag session-<date> for weekly milestones
```

---

## Weekly Workflow

### Friday (End of Week)

```bash
# Generate semantic summary of week's work
python forge/scripts/weekly_summary.py

# This script will:
# 1. Fetch all commits from Mon-Fri
# 2. Extract commit messages and diffs
# 3. Generate embeddings via Ollama
# 4. Create semantic summary in markdown + postgres
# 5. Output to forge/logs/week-summary-<date>.md

# Tag weekly milestone
git tag -a week-summary-$(date +%Y%m%d) -m "Weekly summary $(date)"
git push --tags

# Review summary, update PROGRESS.md
```

---

## Publishing to GitHub

### Initial Setup (Week 1)

```bash
# Create repo on GitHub (public, MIT license)
# Clone to your machine

git remote add origin https://github.com/yourusername/forge.git
git branch -M main
git push -u origin main
```

### Ongoing (Weekly Push)

```bash
git push origin main              # Push all commits
git push --tags                   # Push version tags
```

### Release (v1.0.0 Launch)

```bash
# Tag final release
git tag -a v1.0.0 -m "Release v1.0.0: Workflow visualization + semantic logging"
git push origin main --tags

# GitHub will auto-create release page
```

---

## Rules (Non-Negotiable)

1. **Never commit if tests fail**
   ```bash
   pytest tests/ -v
   # Must show: 13/13 passed
   ```

2. **Never commit with commented-out code**
   - Delete unused code, don't comment it

3. **Always push to origin same day**
   - Don't let commits sit locally
   - GitHub becomes your backup

4. **Keep main releasable at all times**
   - Anyone should be able to `git clone && docker compose up` and have it work

5. **Document breaking changes in commit body**
   - If API changes, explain migration path

---

## Tools & Commands Cheat Sheet

```bash
# Status
git status
git log --oneline -10
git diff HEAD~1

# Stage & Commit
git add -A                        # Stage all changes
git add <file>                    # Stage specific file
git commit -m "msg"

# Undo
git reset HEAD~1                  # Undo last commit (keep changes)
git revert <commit-hash>          # Create inverse commit

# Push/Pull
git push origin main
git pull origin main

# Tags
git tag -a v1.0.0 -m "msg"
git push --tags

# Weekly Summary
python forge/scripts/weekly_summary.py
```

---

## Workflow Diagram

```
Monday
  ├─ git pull (no changes usually)
  └─ Start development

Tue-Thu
  ├─ Make code changes
  ├─ Run tests (13/13)
  ├─ git add + git commit
  └─ git push origin main (same day)

Friday
  ├─ Continue dev work
  ├─ git push final commits
  ├─ python forge/scripts/weekly_summary.py (generate summary)
  ├─ git tag week-summary-<date>
  └─ git push --tags

GitHub (Weekly)
  └─ View commit history + tags
  └─ Share weekly summary on Twitter/blog
```

---

## Tips for Success

1. **Commit often** (every 1-2 hours of work)
   - Easier to debug if something breaks
   - Clearer history for future reference

2. **Write meaningful commit messages**
   - Future you will thank present you
   - Also helps with semantic summarization

3. **Review diffs before pushing**
   ```bash
   git diff HEAD~1  # See what changed
   ```

4. **Use GitHub for backups**
   - Push every single day
   - Your SSD is safe, but not invincible

5. **Tag milestones**
   - Weekly summaries (auto-generated)
   - Phase completions (manual)
   - Version releases (manual)

---

## Semantic Logging Integration

The weekly summary process will:
1. Query all commits since last summary
2. Extract code changes + meanings
3. Generate embeddings for each commit
4. Store in postgres: `commits` table
5. Generate summary via LLM + semantic search
6. Output to: `forge/logs/week-summary-<date>.md`

See `SEMANTIC_LOGGING.md` for details.
