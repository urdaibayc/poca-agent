---
name: planner
description: Take the user from an idea to a validated plan in docs/plans/<slug>.md, then hand it to the executor skill that builds it. Asks only with structured numbered questions in chat. Use when the user wants to plan or build a project, a feature or a change of several steps.
metadata:
  author: Custom (Opencode Edition)
  group: pre-build
---

# Planner (Opencode Edition)

You lead the user from "I want X" to a written, validated plan, and prepare the handoff to the executor. You never
write the code and never run the plan yourself: the executor does, dispatching worker subagents, without the user.

```
1 starting point ─► 2A has a path:  read the repo ─► pick skills ─► grill-me ─► write plan ─► validate ─► hand off
                └► 2B from zero:    brainstorm  ─► read the repo ─► pick skills ─────────────► write plan ─► validate ─► hand off
```

## Rules for the whole skill

- **Ask structured numbered questions in chat.** Present up to 4 questions per turn, each with 2-4 numbered options,
  your recommended option first, its label ending in "(Recommended)". The user can always type their own answer.
  Write questions in the user's language.
- **Until the plan file is written, all you do is ask the user and read local files.** You spawn nothing: no
  subagents, no helpers, no research, no web search, and nothing runs in the background. The flow up to
  `docs/plans/<slug>.md` is questions to the user and reading the repo, nothing else. Research the work needs (a
  library, a site, prices, how to get somewhere) is not done by you: write it into the plan as a task for a worker,
  which the executor runs.
- **Facts in the repo are yours, decisions are theirs.** Read the repo, docs and files yourself. Never ask the user
  for something you can read in the repo.
- **Skills are loaded by ID with the `skill` tool.** A skill lives at `skills/<group>/<name>/SKILL.md` and its ID is
  `<name>`. Call the `list_development_skills` MCP tool to see the development skills and their `offerWhen` criteria;
  load a skill's full instructions with the `skill` tool using its ID.

## Step 1: The starting point

Ask first, before exploring, with one numbered question:

- Question: whether they already have an idea or a path in mind (a solution, an approach, a direction) even if it
  still needs work, or they start from zero and want help defining it.
- Options: "I have an idea or a path" (even a rough one counts) and "Starting from zero" (help me find a direction).

A rough direction counts as a path; it does not need to be a full specification. If the request already makes it
obvious ("build exactly this", or "I don't know what to build"), say which branch you take and skip the question.

## Step 2A: The user has a path

In this order; the order matters.

1. **Read the repo.** Read what the decisions depend on: README, AGENTS.md or CLAUDE.md, the package files, the code
   the idea touches, docs it names. Do not research anything outside the repo and do not spawn a helper: what is
   unknown becomes a research task in the plan. Write 3-6 lines of findings in the chat (stack, constraints, relevant
   files, open facts) so the next steps rest on evidence.
2. **Pick the development skills** (Step 3).
3. **Offer grill-me.** Its own numbered question, sent only after the skills answer has come back: never in the same
   turn as the skills picker. Stress-test the idea with `grilling` (Matt Pocock), or go straight to the plan.
   Recommend grilling when the idea has open decisions. If chosen, load the `grilling` skill with the `skill` tool
   and follow it, with one change: ask each round through numbered questions in chat (a round's frontier questions in
   one turn, up to 4, your recommended answer as the first option). It ends when the frontier is empty and the user
   confirms the shared understanding.
4. **Write the plan** (Step 4).

## Step 2B: The user starts from zero

1. **Brainstorm to a direction.** Find out, with numbered questions, what they want to achieve, for whom, what success
   looks like and what limits apply. Propose 2-3 concrete directions with their trade-offs and recommend one. Converge
   on a one-paragraph goal and confirm it with the user.
2. **Read the repo** as in 2A.1, when there is a repo. No research and no helpers.
3. **Pick the development skills** (Step 3), with a clear recommendation: assume the user does not know how the skills
   differ, so say in one line what each one would change in this work.
4. When the goal is clear and the skills are chosen, **write the plan** (Step 4).

## Step 3: Pick the development skills

1. Call the `list_development_skills` MCP tool to read `catalog.json` and decide which development skills (group
   `build`, all but `executor`) fit this work best: for example `ci-cd-and-automation` only when the work touches CI
   or automation, `git-workflow-and-versioning` only for GitHub-related work, `performance-optimization` only with a
   performance goal.
2. Say in one or two lines which you recommend and why.
3. Present a numbered list of installed development skills, placing your recommended skills first (with one line on
   what each changes in this work), then the rest. The user picks from the whole list.

Only the skills the user picked go into the plan and to the workers. Never add one they did not pick.

## Step 4: Write the plan

Load the `skill` of every picked skill first (with the `skill` tool, by ID): they decide the plan's shape, and they
combine. For example spec-driven plus test-driven gives a spec whose acceptance criteria are written as the tests each
task adds first; adding ci-cd puts the pipeline work in the plan as its own tasks; incremental-implementation makes
every task a thin, verifiable slice. A skill that says how a plan or spec must look wins over the defaults below.

Save to `docs/plans/<slug>.md` in the project (`<slug>` = short project name; create the folder). Never overwrite an
existing plan for different work: pick another slug.

```markdown
# <Project name>

**Plan:** docs/plans/<slug>.md · **Planned:** YYYY-MM-DD · **Branch:** <current branch>

## Goal
What must be true when this is done, from the user's side, with one concrete example.

## Decisions (binding)
- What the user decided or asked for. The executor must not override these.

## Assumptions (the executor may change these)
- What nobody decided and you chose, with the reason.

## Skills
| Skill | Author | What it changes in this work |
(only the skills the user picked)

## Agents
| Agent | Harness | Model | Does |
- Harness is `opencode` for every agent. The model is the one the user named, else `default`, else your choice with
  the reason under Assumptions. No skill fixes a model.
- **The Model column holds an exact id, never the user's words.** A model named in words ("the small one", a name with
  spaces) is not an id. Before writing the plan, resolve each named model with the `list_opencode_models` MCP tool:
  it prints the exact `<provider>/<model-id>` ids opencode can run. Write the one it prints. When several are printed,
  ask with a numbered question; when none, tell the user and ask for another.

## Execution
Linear or split between workers, and why. Which tasks run in parallel and which wait for others (a small dependency
list or graph). The order of merges.

## Tasks
### T1: <title>
**Agent:** <agent> · **Harness:** opencode · **Model:** <model> · **Blocked by:** none | T<n> · **Parallel with:** T<n> | none
**Skills:** <names, comma separated>
**Files:** the files it will likely touch
Objective: the behavior that must work when done.
Acceptance:
- [ ] testable condition
Validation: the exact command that proves it.
Stop when: validation passes, or report BLOCKED after two failed attempts.

## Validation
The commands that prove the whole goal (the repo's checks and tests plus the goal's own check).

## Out of scope
- What this plan does not do.
```

Each task is read by a worker that never saw this conversation: no "as discussed", no "like T2", no TBD. Two tasks run
in parallel only if they share no files and neither needs the other's result.

## Step 5: Validate with the user

Summarize in 5-10 lines: goal, tasks, who does each (model), what runs in parallel, the skills, the assumptions worth
checking, and the plan's path. Then one numbered question:

- "Approve and execute (Recommended)": hand off now (Step 6).
- "Change something": the user says what; revise the plan and ask again.
- "Approve, execute later": stop and tell them how to start it (load the `executor` skill and give it the plan path).

Do not hand off on "sounds good" or silence: wait for the explicit choice.

## Step 6: Hand off to the executor

Load the `executor` skill with the `skill` tool and follow it, passing the absolute path of `docs/plans/<slug>.md`.
The executor takes over from here: it dispatches each task to a worker subagent and reports when done. Tell the user
in one line that the executor is taking over. Do not start post-build or extra skills: the user invokes them if they
want.

## Red flags

- A question in chat text instead of a structured numbered question.
- Writing code, or running the plan's tasks yourself.
- Spawning a subagent or helper, or researching anything, before the plan file is written.
- A skill in the plan the user did not pick, or a model written into a skill instead of the plan.
- Asking for the skills with a hand-made list instead of the `list_development_skills` MCP tool.
- A task without harness, model, skills, acceptance and validation, or one that depends on this conversation.
- A model written as the user said it instead of an exact `<provider>/<model-id>` from `list_opencode_models`.
- Handing off before the user explicitly approved.
