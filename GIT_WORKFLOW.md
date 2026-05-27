# Forge Git Workflow — Trunk-Based Development

## Strategy: Trunk-Based Development (TBD)

**Why TBD:**
- Simple workflow (one branch: `main`)
- Fast iteration (commit, test, push immediately)
- Clear linear history (no merge conflicts)
- Every commit is deployable
- Less cognitive overhead

---

## Commit Strategy

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

Fixes #<issue-number> (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code restructuring
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
```

### Commit Frequency

- **Small changes:** Commit immediately after testing
- **Feature completion:** Commit when feature is functionally complete
- **Bug fixes:** Commit same-day
- **Documentation:** Commit with related code

---

## Daily Workflow

```bash
git status                        # Check working tree
python -m pytest tests/ -v        # Verify tests pass
git add <modified files>          # Stage changes
git commit -m "feat(scope): description"
git push                          # Push immediately
```

---

## Rules

1. **Never commit if tests fail**
   ```bash
   pytest tests/ -v
   ```

2. **Never commit with commented-out code**
   - Delete unused code, don't comment it

3. **Always push to origin same day**

4. **Keep main releasable at all times**

5. **Document breaking changes in commit body**

---

## Cheat Sheet

```bash
# Status
git status
git log --oneline -10
git diff HEAD~1

# Stage & Commit
git add -A
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
```
