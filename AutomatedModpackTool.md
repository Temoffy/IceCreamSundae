# Modpack Automation: the mrpack_vonneumannifier (mrvn)

Don't start building until Telos says so.

## 1. Purpose

Keep two Modrinth modpacks up to date: IceCreamSundae (full) and IceCreamMondae (lite). The loader is Fabric. The parent pack is Fabulously Optimized.

Telos drops out for weeks or months. The tool must run alone, including on new Minecraft versions once enough mods have builds. It asks Telos for help in two cases only:

1. The parent changed its mod list or resource pack files.
2. Something broke that the tool can't fix.

The tool checks mod builds, follows the parent, applies configs, builds a .mrpack, tests it, queues it, and uploads one pack per day.

## 2. Terms

Each term has one meaning in this document.

- **Minecraft version**: a game release such as 1.21.10 or 26.2.
- **Pack version**: the number on an upload, such as `26.2-1.0`.
- **Edition**: full or lite.
- **Build**: one .mrpack file for one edition and one Minecraft version.
- **Parent**: the Fabulously Optimized pack.
- **Lock**: the file that lists the exact mod files of the last build queued or uploaded for one edition and one Minecraft version. Only the queue stage writes it.
- **Upload**: a pack version sent to Modrinth, as a draft or published.
- **Completeness**: the percent of wanted mods that have a build for a Minecraft version (Section 7).

## 3. Working agreement for the implementing assistant

1. Don't write code until Telos says start. Then work one phase at a time (Section 14).
2. Run the spikes in Section 5 first. Report the results. Change this plan where a spike disproves an assumption.
3. Question anything unclear or doubtful before building. Telos prefers a question now over wasted work.
4. Design for unattended runs: fail loudly, need no memory from Telos, keep all state in the repo. Do the least that meets the plan, like a lazy senior dev: no extra modules, options, or abstractions, and ask before adding any.
5. Never ask for secrets. Never commit them. The tool's name isn't final (first idea: mrpackVonNeumannifier): use packtool as a placeholder, and spell it only in names that one find-and-replace can change.
6. write minimally, simply, and maintainably.
7. use the 'pi --print "text"' command to delegate work when possible to preserve context.

## 4. Decisions

1. **No packwiz.** The tool keeps its own lock file and writes the .mrpack index itself. This removes a binary, a pin, and a fallback path. The Modrinth API gives every field the index needs.
2. **Read the parent from Modrinth, not git.** The parent's published .mrpack has the mod hashes, configs, and resource packs. A version on Modrinth is by definition published.
3. **A parent change doesn't block mod updates.** The tool keeps building against the last accepted parent version. A PR proposes the new one.
4. **Queue is first in first out.** Batches sorted with newest minecraft versions first, full before lite.
5. **Notifications use ntfy only.** ntfy can forward to email with a header. This removes the SMTP secrets.
6. **Config work comes last.** Whole-file copy and an `options.txt` merge come first. Patches, harvest, and capture come after.
7. **The tool never edits `manifest/mods.yaml`.** Telos does, inside the PR.
8. **Tests run in tiers.** Static checks, then a server boot, then a client boot.

9. Modrinth only. Fabric only.
10. Python 3.12 venv. Host is Kubuntu with systemd user timers.
11. One manifest. The lite edition is the full manifest filtered by `lite: false` flags.
12. Mod channel: newest release. If a Minecraft version has no release of a mod, use the newest beta or alpha and mark it in the changelog. A per-mod override is allowed. Follow parent pre-releases the same way.
13. Every active Minecraft version gets update checks, old ones included.
14. Build and test everything in one run. Upload one build at a time.
15. never sort minecraft versions as strings or numbers. Sort chronologically
16. Telos puts project IDs and tokens in the files. The tool ships TODO placeholders and `.env.example`.
17. The client test uses portablemc under xvfb-run. No GUI launcher.
18. `auto_publish: false` at first, so uploads are drafts. Flip it after several clean drafts.
19. Telos creates settings by playing the game. A `capture` command records them (Phase 10).

20. **Completeness numbers.** release at 95%, beta at 70%, alpha at 50%, plus `required` mods (Section 7).
21. **Config policy.** shipped configs are defaults, delivered through yosbr or a similar mod, so updates don't overwrite player edits. Spike S6 picks the mod and path for each Minecraft version.

## 5. Open questions and spikes

### Spikes (verify before relying on them)

- **S1. Boot.** Does portablemc run Fabric on the newest Minecraft (26.x)? Check the pinned loader, offline account, the join-server flag, the Java runtime for a local vanilla server, and the quit rule: wait 15 to 30 seconds after the client is fully booted, then kill it. Confirm that configs are written by then. Capture one good boot log and one failed boot log. Pick the success and failure patterns from them. Fallback: Prism Launcher CLI.
- **S2. Software rendering.** Do Sodium, Iris, and Distant Horizons reach the main menu with `LIBGL_ALWAYS_SOFTWARE=1` and `ALSOFT_DRIVERS=null`? If one fails, add a `test_skip` list for the test only.
- **S3. Parent .mrpack.** For recent Fabulously Optimized versions, read the index and overrides. Confirm:
  1. `POST /version_files` turns the index hashes into project IDs.
  2. Which loader version the index names.
  3. Which config, mod, and resource pack files ship in overrides.
  4. Whether any file names the parent pack and must be renamed.
- **S4. Availability queries.** Check `GET /project/{id}/version` with `loaders` and `game_versions` filters. Check how to pick the newest build per channel (by `date_published`, not by number). Check rate limits and the ETag behavior.
- **S5. Upload.** Check the exact multipart fields for `POST /version`, draft status, the token scope, and how the primary file is marked.
- **S6. Config defaults.** Which mechanism does the parent use on each Minecraft version (`config/yosbr`, `config/modpack_defaults`, or both)? Which path does the installed mod read? Which defaults mod does the pack need when the parent has none? Confirm that a shipped default doesn't overwrite a player edit on pack update.
- **S7. Hand-built .mrpack.** Write one .mrpack from one lock by hand. Import it and boot it. Pass: both install it and the game boots. Verified independantly by Telos importing into instance manager.

## 6. Architecture

Four kinds of data, each in its own place:

1. **Manifest** (`manifest/`): what Telos wants. Telos edits it.
2. **Lock** (`lock/`): what the tool last queued or uploaded. Generated. Never edited by hand.
3. **State** (`state/`): what the tool remembers. Only the tool writes it. Committed.
4. **Source** (`source/`): where the code lives, where most of your work will be done.

Stages. Each reads files and writes files, so any stage can rerun alone:

1. **discover**: read Mojang's version manifest. Or just parent's versions. Add new releases as candidates. Move a candidate to active when the parent has a published version for it and completeness reaches what's needed for alpha.
2. **parent**: read the parent's published versions. Accept silently or open a PR (Section 9).
3. **resolve**: read the manifest, parent, and Modrinth. Write the full result and the derived lite result to build/. Compare each to its lock. If an edition is unchanged, stop for that edition.
4. **build**: apply configs, write both editions, validate each .mrpack.
5. **test**: static checks, server boot, client boot (Section 10).
6. **queue**: when a build passes all test tiers, write its queue.json entry, then its lock. The lock is never written earlier.
7. **publish**: a separate daily step.

A failure in one Minecraft version doesn't stop the others.

## 7. Rules

### Wanted mods and completeness

- **Wanted** = manifest entries that apply to the Minecraft version (per `versions`), plus parent mods, minus entries with `exclude: true`.
- A wanted mod is **built** when it, or one of its fallbacks, has a build.
- **Completeness** = built / wanted, as a percent.
- A missing `required` mod holds the build, whatever the percent. Marked in manifest.
- The changelog lists mods with no build in addition to the differences from the prior release on that version (if any).

### Lite edition

The resolver derives the lite set from the full result. Remove every mod with lite: false. Then add back any mod that a kept mod requires. Lite has its own lock. If a change touches only mods outside the lite set, the lite lock stays the same and no lite build starts.

### Loader version

Use the loader version named in the accepted parent .mrpack. If the parent has none, use the newest stable Fabric loader.

### Pack versions

Format: `{mc}-{major}.{minor}`, for example `26.2-1.0`.

1. Major bumps when a mod is added or removed, or the parent mod list changed.
2. Minor bumps for mod updates. Minor resets on major. No version change or pack updates pushed for config changes alone.
3. A new Minecraft version starts at 1.0.
4. The number is the next one after the last **uploaded** number for that edition and Minecraft version. A superseded build never used its number, so the next build reuses it.

### Content hash

Hash the sorted list of (path, sha512) for every file in the build, including overrides. Zip files are deterministic: sorted entries, fixed timestamps. A build joins the queue only when its content hash differs from the last queued or uploaded hash for that edition and Minecraft version. When the hash is the same, write the lock and stop.

### Queue and publish

1. The queue is first-in-first-out by time added.
2. Each edition and Minecraft version is its own item. The editions don’t wait for each other.
3. A new ready build replaces an older ready build for the same edition and Minecraft version, and keeps its position.
4. The queue holds at most 8 ready builds. A build that replaces a ready build always goes in. Any other build goes in only while fewer than 8 builds are ready. Failed builds don’t count.
5. The daily publish step uploads the next item in the queue. It exits quietly if the last upload is newer than min_days_between.
6. It checks the artifact checksum, then calls POST /version. The upload is a draft unless auto_publish is true.
7. In draft mode it sends a note that a draft needs a click.
8. Never create a change just to have something to upload.

### Outcomes per Minecraft version

- `NOTHING_CHANGED`: nothing queued, nothing sent.
- `QUEUED`: a tested build is ready. Nothing is sent (in draft mode, publish sends the note).
- `NEEDS_DECISION`: a parent PR is open. Send one notification only. Builds continue from the accepted parent version.
- `HELD`: completeness is below `alpha_at`, or a required mod is missing. Report why.
- `FAILED`: send one notification per failure signature. Repeat after 7 days.
- `DEFERRED`: a change exists and the queue is full. The tool doesn’t test it. The lock stays as it is. Nothing is queued. Nothing is sent.

The run exits nonzero if any version failed, so `OnFailure=` fires as a backstop.

## 8. Repo layout

```
pyproject.toml          # dependencies
README.md               # full run book: how to resume after months away, how to roll back a bad upload
manifest/
  packs.yaml  mods.yaml  mc-versions.yaml  parent.yaml
configs/
  base/  <mc>/                # each holds files/ options.d/ (patches/ added in Phase 10)
assertions/
  extra.yaml
assets/                       # icons
lock/<mc>_(full|lite).json    # last queued or uploaded mod files, per edition
state/
  uploads.json  queue.json  parent/<mc>.json  runs/
build/                        # git-ignored: builds, game dirs, logs, caches
tests/
deploy/                       # systemd units
source/                       # code
```

## 9. Data files

### manifest/packs.yaml

```yaml
settings:
  loader: fabric
  channel: release # beta or alpha only when no release exists
  version_format: "{mc}-{major}.{minor}"
  completeness:
    release_at: 95
    beta_at: 70
    alpha_at: 50 # also the onboarding threshold
  publish:
    auto_publish: false # false uploads as draft
    min_days_between: 1
  notify:
    ntfy_email: true # forward to email through ntfy
packs:
  full:
    name: IceCreamSundae
    modrinth_project_id: TODO
    icon: assets/full.png
  lite:
    name: IceCreamMondae
    name_template: "{name} {mc}"
    modrinth_project_id: TODO
    icon: assets/lite.png
```

### manifest/mods.yaml

One entry per mod.

Fields:

- `id`: Modrinth slug. Required.
- `name`: display name.
- `lite`: `false` removes the mod from the lite edition. Default true.
- `required`: `true` holds the build when this mod has no build. Default false.
- `fallback`: nested mod list of the same format, tried when this mod has no build for the Minecraft version. Fallback mods trigger their own companions, not the parent's companions.
- `companions`: optional dependencies to add with this mod. The resolver adds required dependencies by itself.
- `exclude`: `true` never ships the mod, even if the parent has it.
- `versions`: Minecraft version expression, such as `>=1.21.5`. The entry applies only there. When the entry doesn't apply, its fallbacks don't either. To swap one mod for another across ranges, write two entries with `versions` and no fallback.
- `pin` and `reason`: hold the mod at a pack version number. `pin` is a map from Minecraft version to mod version number.

Parent mods need no entry. The tool matches parent project IDs. Add an entry only to set a flag, such as `lite: false` on `iris`.

```yaml
- id: fabric-api
  required: true
- id: elytra-armor
  name: Armored Elytra
  fallback:
    - id: metalwings
      name: Metal Wings
- id: simple-voice-chat
  companions:
    - id: talkingheads
      name: Talking Heads
      lite: false
    - id: voicechat-soundboard
      name: voicechat soundboard
- id: faithful-32x
  lite: false
- id: iris
  lite: false
- id: capes
  exclude: true
```

### manifest/mc-versions.yaml

Three lists: `active` (checked every run), `candidate` (found, not onboarded), `retired` (no work). `init` seeds `active` from the Minecraft versions already on the two Modrinth projects. Telos may edit the lists.

### manifest/parent.yaml

```yaml
project: fabulously-optimized # Modrinth slug
remove_files: [] # paths to delete after copying parent overrides
rename_in_files: {} # S3: files that name the parent pack and need the new pack name
```

### Parent handling

1. The tool lists the parent's published versions for each active Minecraft version. It picks the newest by the channel rule.
2. It downloads that .mrpack. It turns the index hashes into project IDs with one `POST /version_files` call.
3. It compares the project ID set and the resource pack (.zip) list to `state/parent/<mc>.json`. That file holds the accepted parent version ID and its lists.
4. **No change in mods or .zip files\*\***:\*\* accept the new parent version, commit the state file, and list changes in the changelog.
5. **Change in mods or .zip files:** open a PR on branch `parent/<mc>/<parent-version-id>`. The PR updates `state/parent/<mc>.json` and lists adds and removals in the body. Telos edits `manifest/mods.yaml` in the same PR if a flag is needed. Merging is the approval.
6. Closing without merging records a rejection. The tool lists closed PRs by branch name, so it doesn't reopen the same one.
7. Until the PR merges, builds use the accepted parent version. The tool downloads it again by ID, so builds stay reproducible.

GitHub access: the tool uses the `git` CLI to push the branch and the REST API only to open the PR.

### Lock file (lock/<mc>\_<edition>.json)

Per mod: project ID, slug, version ID, version number, version type, file name, sha1, sha512, size, download URL, client and server side flags, dependency IDs, and source (`manifest`, `parent`, `dependency`, `companion`, `fallback`). Also: loader version, accepted parent version ID.

### Configs

Phase 7 starts with two layers, applied in order: `base`, then `<mc>`. Each layer has:

1. `files/`: whole files copied by path. A later layer replaces an earlier file.
2. `options.d/`: `options.txt` fragments merged by key into the parent's `options.txt`. No duplicate keys. Build the `resourcePacks` line from the files actually present plus an ordered name list.

The parent's config folder and .zip files are copied first. Shipped configs must not name the parent pack. Put shipped configs and options.txt in the defaults folder that S6 picks (yosbr or similar), never directly in config/, so player edits survive updates.

Phase 10 adds:

1. `patches/`: key-level patches. Fields: target path, format (toml, json, properties, key-value), a `set` map, and `require_keys` (fail if a key is missing from the harvested default). JSON5 files can't be patched without losing comments, so copy them whole.
2. **Defaults harvest**: build a bare pack, boot it once in a clean directory, copy the generated configs, apply patches, and write the result to the path S6 picks. Cache by a hash of the mod set. Mods that write config late fall back to whole-file copy.
3. **Capture**: `packtool capture --pack full --mc <mc> --layer base` builds the pack, runs the harvest, opens the game in a real window, and waits for Telos to quit. It diffs the game directory against the defaults and writes patches or whole files into the chosen layer. Telos reviews the result in git.
4. **Range layers**: add `range/<expr>` only if duplication across Minecraft versions starts to hurt.

### assertions/

Every patched key and every `options.txt` fragment key becomes an assertion. `assertions/extra.yaml` adds manual ones: file, format, key, `equals` or `exists`, and `when` (`boot1`, `boot2`, or `both`). The second boot catches mods that rewrite configs.

### state/

- `uploads.json`: last uploaded pack version, time, and content hash, per edition and Minecraft version. `init` seeds it from Modrinth.
- `parent/<mc>.json`: accepted parent version ID, project IDs, and .zip files.
- `queue.json`: pack, Minecraft version, pack version, artifact path, checksum, content hash, status (`ready`, `uploaded`, `superseded`, `failed`).
- `runs/`: the last N run reports (markdown and JSON). Roll older ones into one summary file in batches.

## 10. Tests

Each build runs three tiers. A fail at one tier stops the later tiers.

1. **Static.** Validate the .mrpack index: format version, loader and Minecraft dependencies, hashes, allowed download hosts, path safety. Read each jar's `fabric.mod.json` and check its `depends` against the Minecraft version, loader, and the other mods. This catches most version mismatches without starting the game.
2. **Server.** Start a Fabric server with the mods marked server-capable. Pass: the log shows the server finished starting.
3. **Client.** Install from the .mrpack into a clean directory. Boot twice under xvfb-run. Boot 1 joins a local vanilla server. Pass when the server log shows the player joined, the client stays alive for N seconds, and the client log has no unlisted errors. Boot 2 checks that settings persisted and runs the assertions.

The launcher waits 15 to 30 seconds after the client is fully booted, then kills the process group. A timeout covers boots that never finish.

## 11. Modules (source/)

1. `cli.py`: argparse. Subcommands: `init`, `check`, `discover`, `parent`, `resolve`, `build`, `test`, `queue`, `publish`, `capture`, `status`. Flags: `--pack`, `--mc`, `--dry-run`.
2. `models.py`: pydantic models for every manifest, lock, and state file. Bad input fails at load with a clear message.
3. `mcversion.py`: parse and order versions from Mojang's manifest (cached). Range expressions. Lists new releases (type release only). Tests: 1.21.9 vs 1.21.10, and 26.2.
4. `modrinth.py`: httpx client with a User-Agent that names the project and a contact, retries, ETag cache, bulk hash lookup, project versions, project metadata (title, license, side flags).
5. `parent.py`: Section 9, Parent handling.
6. `resolver.py`: picks mod files (channel, pin, versions, exclude, fallback), adds required dependencies and companions, computes completeness, and derives the lite set. It writes to build/, never to lock/.
7. `configs.py`: layers, `options.txt` merge, parent file cleanup. Later: patches, harvest, capture.
8. `builder.py`: writes the .mrpack, computes the content hash, runs the static checks.
9. `installer.py`: unpacks a .mrpack into a clean game directory. Installs servers as needed. Downloads with a cache keyed by hash. Verifies hashes.
10. `launcher.py`: portablemc under xvfb-run, local vanilla server, a real-window mode for capture.
11. `checks.py`: success and failure patterns, crash-report detection, assertions, two-boot comparison.
12. `changelog.py`: text from the lock diff: parent version, mods added, removed, updated, config changes, mods with no build.
13. `queue.py`, `publisher.py`: Section 7 rules, the slot limit, the lock write, and the Modrinth upload.
14. `github.py`: `git` push and the REST call that opens or updates a PR.
15. `notify.py`: ntfy, with the email header. Dedupe by failure signature.
16. `state.py` (atomic writes), `runlog.py`, `lock.py` (flock so runs can't overlap).

`init` is part of `cli.py` and `state.py`. It seeds `uploads.json` and `mc-versions.yaml` from both Modrinth projects. It takes the current parent version as the first accepted one, with no PR. It builds and tests both editions. It queues a build when its content hash differs from the last upload. It writes locks the same way the queue stage does.. Uploads stay drafts.

Tests: `tests/fixtures` holds recorded Modrinth responses, made by a script. Unit tests cover every module. One slow test, marked `integration`, boots a vanilla Fabric instance with no pack.

## 12. Run flows

### check (weekly timer)

1. Take the run lock. Run git pull.
2. Discover new Minecraft releases. Onboard those that meet the thresholds.
3. For each active Minecraft version, run parent, even when the queue is full.
4. Order the versions: those with a ready build first, then the rest by newest MC version.
5. For each version, run resolve into build/.
6. For each edition whose result differs from its lock, make the build and compute its content hash.
7. If the hash equals the last queued or uploaded hash, write the lock and go to the next edition.
8. If the queue has no free slot, counting a slot for the same MC version and edition as empty, (Section 7, rule 4), report DEFERRED and go to the next edition. Or if no free slot and going to a version not in the queue, abort early to save duplicate work.
9. Otherwise, run the three test tiers. If they pass, write the queue.json entry, then the lock. If a tier fails, report FAILED and leave the lock as it is.
10. Isolate failures per version and per edition.
11. Write the run report.
12. commit and push to main

### publish (daily timer)

Section 7, Queue and publish.

## 13. Deploy, secrets, and tools

**Timers.** `packtool-check.timer` (weekly, `Persistent=true`), `packtool-publish.timer` (daily), `packtool-alert@.service` through `OnFailure=`, an optional heartbeat ping so that Telos knows everything is operational, and `loginctl enable-linger`. `Persistent=true` runs a missed job at the next boot.

**Secrets** live in `~/.config/packtool/env` (mode 0600): `MODRINTH_TOKEN` (scope: create versions), `GITHUB_TOKEN`, `NTFY_TOPIC`. Telos creates the file. The tool ships `.env.example` with names only.

**Tools.**

1. Python 3.12 venv.
2. Python libraries: httpx, pydantic 2, PyYAML (read only), tomlkit (Phase 10), pytest, and portablemc.
3. git, xvfb-run, Mesa software GL, and the Mojang Java runtime that portablemc downloads.
4. systemd user timers.
5. Modrinth API v2, GitHub REST API, Fabric meta API, ntfy.
6. Fallback launcher: Prism Launcher CLI, if S1 fails.

**Updating portablemc.** Mojang changes can break an old portablemc. In Phase 11, add one step to `check`: run the vanilla Fabric smoke boot. If it fails, try the newest portablemc in a temporary environment. If that resolves it, update packages.

## 14. Phases

Phases are executed by the agent, user, or temporary scripts isolated from the full tool itself.

- **P0:** Spikes S1 to S7. Write a spike report in the README. Update this plan where results differ.
- **P1:** Boot harness on a small hand-made test pack (S7's .mrpack). Do this first. It's the riskiest part and where the last attempt stalled. Accept: the test boots the pack twice and passes. A broken config or a missing mod fails with a clear reason.
- **P2:** Skeleton: `pyproject`, `models`, `mcversion`, `state`, `runlog`, `lock`, `cli`. Seed `mods.yaml`. Accept: ordering and schema tests pass.
- **P3:** `modrinth.py` and `resolver.py` as a read-only report. Accept: for one Minecraft version, list every mod with its newest build, type, fallback used, missing mods, and completeness. No writes.
- **P4:** Builder and static checks for both editions. No lock writes. Accept: both editions build for one Minecraft version. The mod set equals manifest plus parent, minus excluded, plus dependencies. The lite set holds the dependency closure. A change to a full-only mod gives an unchanged lite result.
- **P5:** Parent handling and PR. Accept: replay an old parent version, then a newer one. The PR lists adds and removals. Merging triggers a rebuild. A rejected PR doesn't reopen.
- **P6:** Server and client tiers, assertions. Accept: seeded failures are caught.
- **P7:** Config layers (whole files and `options.txt` merge). Accept: a changed `options.txt` key persists in a clean boot.
- **P8:** Queue, lock writes, and publisher in draft mode. Accept: three drafts upload on cadence in queue order. A failed test leaves the lock unchanged. A full queue skips new versions and still replaces ready builds. A crash between the queue.json write and the lock write causes one rebuild with the same hash and no new item.
- **P9:** Timers, alerts, heartbeat, and new-release discovery. Accept: break something on purpose and exactly one alert arrives. A fixture for a new Minecraft release onboards only when the thresholds are met.
- **P10:** Patches, defaults harvest, capture. Accept: capture records a changed setting as a patch. The key persists in a clean boot. A mod's config format change fails loudly.
- **P11:** portablemc update step. Then set `auto_publish` to true.
- **Later, optional:** `borrow: [<mc>]` on a mod entry. It accepts a build tagged for another Minecraft version and adds a `fabric_loader_dependencies.json` entry by parsing the JSON. The tool keeps it only if the three test tiers pass. Consider automating tests spreading existing builds to neighboring versions without a build and proposing borrows by PR.

## 15. Known Issues

1. Client boot under xvfb is slow and can fail for reasons outside the pack (GPU, audio). Detect success from log lines, not screenshots.
2. A boot to the main menu doesn't catch crashes inside a world. The join test covers part of that. `borrow` raises this risk.
3. The test server is vanilla, so server-side mod behavior isn't tested on the client join.
4. Mod updates can break behavior without a crash. Assertions catch only the keys they check.
5. Some mods write config late, so the defaults harvest misses them. Use whole-file copy for those.
6. Modrinth modpack rules limit which files a pack may include. Any file in overrides needs a manual permission check and credit statement in modrinth.
7. Modrinth requires a descriptive User-Agent and rate-limits requests.
8. Minecraft 26.x versioning differs from 1.21.x. Don't assume a `1.x.y` format.
9. The machine may be off when a timer fires.
10. A draft counts as published for every tool rule (pack versions, content hash, queue).
11. newest-first can content-starve older versions. This is acceptable to focus mostly on newer versions.

## 16. Non-goals

CurseForge support, a web dashboard, Docker, a GUI launcher import test, automatic resolution of parent changes.
