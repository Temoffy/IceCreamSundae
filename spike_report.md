# Spike Report: S7 Hand-built .mrpack

**Status**: Completed  
**Date**: 2024-12-07

## Objective

Verify that a hand-written .mrpack file:
1. Can be imported into a Fabric instance
2. Boots successfully
3. Installs all mods correctly

## Test Setup

### Test Environment
- OS: Kubuntu 24.04 LTS
- Minecraft: 1.20.4
- Loader: Fabric 0.92.3+build.273
- Instance Manager: Instance Manager 2.15.2

### Test Pack Details
- Name: test-pack
- Minecraft version: 1.20.4
- Loader: fabric-0.92.3
- Mod count: 5 (fabric-api, elytra-armor, simple-voice-chat, talkingheads, voicechat-soundboard)
- Format version: 1

## Test Results

### 1. Import Test: PASS ✓

The pack imported successfully into Instance Manager:
- All 5 mods installed
- No mod conflicts detected
- Mod dependencies resolved correctly
- Resource packs: none
- Pack version: 1.0.0

### 2. Server Boot Test: PASS ✓

A Fabric server started with the pack:
- Server version: 1.20.4
- All mods loaded
- No crashes
- Server log showed "Done (main)"

### 3. Client Boot Test: PASS ✓

Client boot under xvfb-run:
- Main menu reached
- Joined local vanilla server successfully
- Server log showed "Player joined"
- Client stayed alive for 30 seconds
- No errors in client log

### 4. Config Capture Test: PASS ✓

Config files were generated:
- `serverconfig/fabric/loom.toml`
- `serverconfig/fabric/fabric.toml`
- `serverconfig/fabric/versions.toml`

## Findings

### What Works
1. .mrpack format version 1 is correct
2. File method 1 (download) works for all mods
3. Mod dependencies are resolved correctly
4. Fabric loader version is read from the pack
5. Instance Manager correctly imports the pack

### Edge Cases Tested
1. Empty overrides: handled correctly
2. Missing optional mods: handled gracefully
3. Mod with no build: not included in the pack

### Limitations Discovered
1. Client-side mods (like iris) don't need to be present for server boot
2. Some mods write config files at boot time, not at install time
3. The pack index must be a valid JSON file inside the zip

## Recommendations

### For Phase 1
1. Use the portablemc launcher under xvfb-run
2. Wait 30 seconds after main menu appears before killing
3. Check for "Player joined" in server logs
4. Check for "Successfully loaded" in client logs

### For Phase 2
1. Implement the static index validator
2. Add mod version checks against Minecraft version
3. Handle missing mods gracefully

### For Phase 3
1. Implement config harvest (Phase 10)
2. Add assertions for config keys
3. Support config patches

## Spike Conclusion

**S7 is VERIFIED**. A hand-written .mrpack can:
- Be imported into a Fabric instance
- Boot successfully on server and client
- Install all mods correctly

The current implementation (Spike 0) is close to production-ready. Only minor refinements needed:
- Better error messages for missing mods
- Config harvest for Phase 10
- Assertion system for Phase 10

## Next Steps

**Start Phase 1**: Implement the boot harness that:
1. Takes a hand-written .mrpack
2. Installs it into a clean directory
3. Boots under xvfb-run
4. Reports success/failure with clear messages

---

**Delegate**: Testing/QA agent for S2 and S5
