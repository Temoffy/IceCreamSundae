# Pending Spike Tasks

## S2. Software Rendering Test
**Priority**: Medium  
**Requires**: Root access to install mod packages  
**Goal**: Verify Sodium, Iris, and Distant Horizons reach main menu with `LIBGL_ALWAYS_SOFTWARE=1` and `ALSOFT_DRIVERS=null`

**Test Plan**:
1. Install mods: sodium, iris, distant-horizons
2. Test each with software rendering flags
3. Add `test_skip` list for any failures

**Context**: S1 already confirmed llvmpipe works. Need to verify shader mods don't crash with software rendering.

---

## S5. Upload API Test
**Priority**: Medium  
**Requires**: Modrinth API token  
**Goal**: Check exact multipart fields for `POST /version`, draft status field, token scope, and primary file marking

**Test Plan**:
1. Test with valid token scope
2. Verify multipart field structure
3. Confirm draft status behavior
4. Document rate limits and ETag behavior

**Context**: S4 confirmed the versions endpoint doesn't exist, need to use project versions query.

---

## S7. Hand-built .mrpack Test
**Priority**: High  
**Requires**: Root access to install packages  
**Goal**: Write one .mrpack from one lock by hand, import it, and boot it to verify both installation and game boot

**Test Plan**:
1. Create a sample lock file
2. Write a .mrpack from it
3. Import into game instance
4. Boot and verify success

**Context**: This is the riskiest spike as it's where the last attempt stalled.

---

## Next Steps
Delegate these tasks to appropriate subagents:
- S2 → Testing/QA agent (requires package installation)
- S5 → API integration agent (requires Modrinth auth)
- S7 → Build system agent (requires package installation)
