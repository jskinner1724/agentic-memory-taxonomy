# Agentic Memory: A Functional Taxonomy

## Overview

Agentic memory is not one thing. It is the set of mechanisms that allow an agent to preserve relevant state, learn from experience, maintain goals, revise beliefs, and act coherently over time.

The familiar categories are:

- **Short-term / working memory** — the active context for the current task.
- **Long-term memory** — information retained across tasks or sessions.
- **Episodic memory** — records of events, interactions, observations, and outcomes.
- **Semantic memory** — general facts, concepts, entities, and relationships.
- **Procedural memory** — knowledge of how to perform actions or workflows.

These are a strong foundation, but they are not fully parallel categories. Working memory describes a time horizon; episodic, semantic, and procedural memory describe different kinds of content that may persist long-term.

## Additional core memory types

### Prospective memory

Memory of intended future actions, reminders, follow-ups, and commitments.

> “After the missing data arrives, update the report and notify the user.”

Without prospective memory, an agent may recall the past accurately while still failing to complete what it promised to do.

### Goal and commitment memory

The objectives, priorities, constraints, obligations, and definitions of success that give a task direction.

Goals should be represented separately from conversation history so that they survive summarization and remain visible during planning.

### Provenance memory

Where a belief came from, who supplied it, what evidence supports it, and whether it was observed, stated, inferred, or guessed.

```text
User stated: “The deadline is Friday.”
Document states: “The deadline is Thursday.”
Agent inference: “There may be a timezone or version conflict.”
```

These should not be stored or weighted as equivalent memories.

### Temporal memory

When something was true, when it changed, when it expires, and what superseded it.

An agent needs to distinguish:

- true now;
- true at a past time;
- expected to become true;
- expired;
- superseded;
- disputed;
- unknown.

### Causal memory

Why something happened, not merely what happened.

```text
Episodic: The deployment failed.
Causal: The deployment failed because production could not access the credential store.
```

Causal memory enables transfer of lessons to new situations.

### Negative or inhibitory memory

Memory of failed approaches, rejected options, forbidden actions, disproven assumptions, safety boundaries, and conditions under which an action should not be attempted.

Expertise consists partly of knowing what to avoid. This is one of the most important and underdeveloped categories in agent systems.

### Social and relational memory

People, roles, relationships, authority, trust, preferences, ownership, and who said or approved what.

This enables an agent to reason about whether a claim came from an owner, reviewer, observer, or untrusted source.

### Identity and self-model memory

The agent’s role, capabilities, limitations, responsibilities, permissions, operating assumptions, and continuity over time.

An agent should remember not only facts about the world, but also facts about what it is allowed and able to do.

### Salience and value memory

Importance, urgency, risk, emotional significance, and expected future usefulness.

This helps determine what deserves retention and attention rather than treating every stored item equally.

### Metamemory

Memory about the reliability and applicability of other memories:

- How confident am I?
- Where did this come from?
- Has it been contradicted?
- When was it last verified?
- Under what conditions should it be retrieved?
- Should I verify it before acting?

Metamemory may be the most important missing category because any persistent memory system will contain errors. A system must represent uncertainty about memory itself.

## A more complete model

Agent memory is better understood as three intersecting dimensions.

### Content

- episodic — what happened;
- semantic — what is believed to be true;
- procedural — how to do something;
- causal — why something happens;
- social — who relates to whom.

### Control

- working — what is active now;
- prospective — what should happen later;
- goal/commitment — what must be achieved;
- inhibitory — what must not happen;
- salience — what deserves attention.

### Epistemic status

- provenance — where it came from;
- confidence — how reliable it is;
- temporal validity — when it applies;
- metamemory — how it should be retrieved or verified.

One memory can occupy several categories at once. For example:

> “Do not use the old migration script because it corrupted production data.”

This is episodic, causal, procedural, inhibitory, provenance-bearing, and confidence-weighted at the same time.

## Recommended architecture

The most promising design is a **predictive, event-sourced memory system**.

```text
experience stream
      ↓
event interpretation
      ↓
belief / goal / procedure updates
      ↓
conflict and time resolution
      ↓
task-specific context reconstruction
      ↓
action
      ↓
observed outcome
```

The system should preserve original evidence separately from its interpretation:

```text
Observation: “The deployment timed out.”
Interpretation: “The connection pool may be exhausted.”
Confidence: 0.55
```

Important memories should be converted into conditional knowledge:

> Method A works under conditions C, fails under conditions D, and should be preferred only when C holds.

When a new task arrives, the agent should reconstruct the smallest context needed for the decision rather than inject all related memories. Retrieval should be based on decision need, authority, temporal validity, causal relevance, and risk—not only semantic similarity.

## Bottom line

The best memory system will not be the one that remembers the most. It will be the one that:

- remembers the right abstractions;
- preserves evidence beneath those abstractions;
- knows when information expires;
- distinguishes facts from interpretations;
- learns from outcomes;
- retrieves according to decisions rather than word similarity;
- revises beliefs without erasing history;
- exposes uncertainty instead of fabricating confidence.

The deepest design principle is:

> A memory should not only answer “what do I remember?” It should also answer “why do I believe it, when is it valid, what follows from it, and what should I avoid because of it?”

