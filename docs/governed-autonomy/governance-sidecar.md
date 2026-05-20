# Governance Sidecar

`governance.yml` is the process-level source of truth for a governed skill set. It records the accountable roles, authority, evidence, gates, escalation, state policy, and step decomposition that the generated skills inherit.

## Shape

Typical process directories use this layout:

```text
<process-id>/
├── governance.yml
├── governance-validation.md
└── skills/
    ├── <step-id>/SKILL.md
    └── ...
```

`governance-validation.md` is authoring evidence. It records what the dialog asked, what was probed, what contradictions were found, and which sources informed accepted claims.

## Core Fields

`governance.yml` should include:

- `governanceVersion: "1"`;
- `process` with `id`, `name`, `purpose`, and `scope.includes` / `scope.excludes`;
- `roles`, including at least one accountable human role and autonomous roles with `accountable_for: nothing`;
- `authority.default_autonomy_tier`, `authority.default_allowed_actions`, and `authority.prohibited_actions`;
- `local_definitions` for every `local:` ref;
- `input_gates`;
- `risk`;
- `evidence.destination` and `evidence.items`;
- `gates`;
- `escalation`;
- `state.canonical` and `state.projections`;
- `freshness`;
- `steps`;
- `warnings` and `knownGaps`.

## Reference Conventions

Use namespaced refs:

- `catalog:...` for catalog actions, evidence kinds, and risk patterns;
- `local:...` for process-local definitions;
- `role:...` for roles;
- `step:...` for steps;
- `evidence:...` for evidence items;
- `lane:...` only when a process introduces lanes.

Every `local:` ref must have a top-level `local_definitions` entry with a `definition` of at least 20 characters and a `category`.

## Authority Semantics

Process-level `authority.default_allowed_actions` is a default for steps, not a total authority envelope. A step can replace the default with `steps[*].authority_overrides.allowed_actions`.

Process-level `authority.prohibited_actions` is the hard ceiling. Step-level prohibited actions union with the process-level list; a step cannot remove inherited prohibitions.

Effective step authority is:

- allowed actions: step override if present, otherwise process default;
- prohibited actions: process prohibitions plus step prohibitions;
- autonomy tier: step override if present, otherwise process default.

If an action is both effectively allowed and prohibited, lint should report an error.

## Step Kinds

`steps[*].step_kind` is one of:

- `execute`: produces a work product;
- `investigate`: read-only, produces findings;
- `decide`: routes or classifies;
- `approve`: a human gates a transition;
- `monitor`: ongoing observation.

Investigation steps are read-only by definition. If an investigation needs to ask a human or write a record, split that into a later step.

## Enforcement

`enforcement.tool_action_map` is optional. When absent, the sidecar remains advisory. Runtime behavior is unchanged.

When present, `tool_action_map` maps an action ref to Claude Code tool-call patterns:

```yaml
enforcement:
  tool_action_map:
    catalog:action:approve-own-work:
      - "Bash(git push *)"
    catalog:action:draft-artifact:
      - "Write"
      - "Edit(*)"
```

The map does not grant authority. It only lets the runtime identify which governed action a pending tool call represents. The active step still uses the authority merge rules above. If the matched action is effectively prohibited for that step, the PreToolUse hook blocks the call.

The hook also blocks write tools during `investigate` steps. A step becomes active when the runtime writes `.governance/active-step.yml`, usually through `scripts/ga-enforce --start-step <step-id>`.

```yaml
step: draft
done:
  tool_name: Bash
  command_glob: ga-step done draft
```

PostToolUse can check declared evidence presence when the active step is marked done. It checks files named by `evidence.items[*].path` under the process directory when `evidence.destination` is `repo`. PostToolUse cannot undo a completed tool call. If evidence is missing, it keeps the active-step marker in place and feeds Claude a block reason.

Hook enforcement constrains tool calls and evidence presence. It does not inspect model reasoning, infer scope, detect cross-tool collusion, or govern anything outside the Claude Code hook harness.

## Skill Frontmatter

Each generated step skill includes governance frontmatter:

```yaml
governance:
  process: ../../governance.yml
  step: implement
  inherits: [authority, evidence, escalation]
  overrides:
    autonomy_tier: draft
```

The YAML sidecar is canonical for tooling. The skill prose must still restate authority, evidence, and escalation so the runtime agent sees the constraints without opening separate files. Drift between prose and YAML is a critique finding.
