# Evaluation plan
Version: 1.0.0  
Generated (UTC): 2026-02-07T08:11:25Z

## Purpose
Validate that MCP Geo improves dataset selection correctness, speed, accessibility, and governance safety for both humans and AI agents.

## Evaluation dimensions

### 1) Usability and task performance
- Metric: Task completion rate (%)
- Metric: Time to correct dataset (seconds)
- Metric: Elicitation abandonment rate (%)
- Thresholds:
  - completion >= 85%
  - median time <= 120s for novice tasks
  - abandonment <= 15%

### 2) Retrieval quality
- Metric: top-1 dataset correctness
- Metric: top-3 recall for target dataset
- Metric: wrong-geography selection rate
- Metric: incompatible-comparison selection rate
- Thresholds:
  - top-1 >= 75%
  - top-3 >= 92%
  - wrong-geography <= 5%
  - incompatible-comparison <= 3%

### 3) Explainability quality
- Metric: user-rated helpfulness of “why this/why not others”
- Metric: link reason acceptance rate
- Thresholds:
  - helpfulness >= 4.0/5
  - acceptance >= 85%

### 4) Accessibility compliance
- Metric: WCAG checks pass rate on key journeys
- Metric: chart text-alternative coverage
- Metric: keyboard-only task completion
- Thresholds:
  - WCAG checks >= 95%
  - text-alternative coverage = 100%
  - keyboard completion >= 90%

### 5) Governance and misuse prevention
- Metric: cards with visible caveats (%)
- Metric: cards with revision status (%)
- Metric: provenance completeness (%)
- Metric: unqualified ranking outputs (% should be 0)
- Thresholds:
  - caveat display = 100%
  - revision status = 100%
  - provenance completeness = 100%
  - unqualified ranking outputs = 0%

## Test design

### A) Persona cohorts
- novice policy user
- analyst/statistician
- AI-agent workflow

### B) Task set
- 20 canonical tasks across domains:
  - inflation, labour, housing, population, health, crime, productivity
- Include:
  - trend tasks
  - comparison tasks
  - small-area tasks
  - revision-sensitive tasks

### C) Baselines
Compare against:
1. ONS site search only
2. ONS thematic browse only
3. MCP Geo hybrid selection model

### D) Data collection
- event logs:
  - tile selected
  - elicitation path
  - candidate rankings
  - final dataset chosen
  - caveat visibility state
- post-task survey:
  - confidence
  - clarity
  - perceived trust

## Reporting cadence
- weekly pilot dashboard
- fortnightly quality review
- monthly governance review

## Exit criteria for production
All thresholds met for two consecutive evaluation cycles and no critical governance/a11y defects open.
