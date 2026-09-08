# ARMS as an operating model

ARMS means **Applications, Routines, Memory, Skills**. It describes the standing environment around agents. A model supplies inference; ARMS supplies repeatability, durable context, triggers, and useful connections. Agent identities and role policies sit across these layers.

## The three levels

| Layer | Level 1 | Level 2 | Level 3 | Evidence |
| --- | --- | --- | --- | --- |
| Skills | A named procedure for one recurring job | A small router with templates, examples, checks | Invoke the reviewed procedure from a controlled application or job | Real inputs create the intended artifact; incomplete input fails usefully |
| Memory | An explicit home for sources and outputs | Short indexes and dated decisions | Searchable visual projection of approved records | A fresh session finds the authoritative source without broad scanning |
| Routines | Manually proven work on an explicit local schedule | A runner able to operate without the primary computer | Bounded execution, ownership, recovery and delivery verification | Actual scheduled artifact, duplicate test, pause and recovery evidence |
| Applications | One useful authorized integration | Discover and evaluate a maintained CLI/API/MCP | Build a narrow custom tool when needed | Exact permitted operation succeeds, with source and scope recorded |

The original guide’s routine levels emphasize where execution lives: local, second machine, cloud. The supplied adaptation adds durability as the upper-level goal. This repository retains both: **location is a deployment choice; reliability is an earned property**. Cloud hosting alone never earns Level 3.

## What flows between the layers

A trigger contains a work-order ID, source window and revision. The routine creates a run, not free-form authority. The run loads a skill revision, retrieves a bounded context packet from Memory, and obtains permitted data through an Application adapter. The skill emits a draft and source references. Validation checks those references and output shape. Review accepts or rejects a specific artifact revision. Only a separately allowed domain operation can change an external system. The receipt becomes a dated memory candidate.

Example: a weekly research brief reads saved sources, selects evidence for the week, produces a draft, and queues it for review. Sending the brief is a separate capability. If the source service fails, last week’s output must not be relabeled as this week’s success.

## Ownership boundaries

| Record | Authority | Consumers |
| --- | --- | --- |
| Source snapshot | Import or connector service | Skill, search, inspector |
| Skill definition | Versioned project files | Agent and launcher |
| Routine definition | Authorized scheduler configuration | Scheduler and controls |
| Run/event record | Runner and domain services | Activity and review queue |
| Artifact revision | Artifact store | Reviewer, export, memory |
| Accepted decision | Review service and authorized person | Application, future context |
| Layout | Per-workspace presentation preferences | UI only |

A summary is not a source. An index is not an independent database. A successful model exit is not successful validation. Acceptance is not permission to perform every suggested action.

## The feedback loop

Review failures improve the skill’s procedure or fixtures. Retrieval failures improve the router. Missed jobs improve the scheduler and runbook. Unused widgets are candidates for removal. Record changes as reviewed revisions; never build an unlimited self-modification loop that promotes its own suggestions to production.

## Agent roles

Start with one coordinator and named capabilities. Add a researcher, reviewer or executor only when workload isolation warrants it. Record role, permitted operations, input contract, model adapter, resource limits and stop conditions. Two role names do not create isolation if both share unrestricted credentials. Enforce restrictions in tools/processes and domain services.

## Maturity is not a shopping list

A single-person research OS can remain local indefinitely. A shared support OS may need identity and tenant isolation before its first app connection. Choose the smallest complete workflow and let evidence determine expansion.
