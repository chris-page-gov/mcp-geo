# SOTA Practice Rationale for Repo Extent + Complexity

This skill uses a layered metric model aligned with current state-of-practice:

1. Inventory and language footprint
- GitHub Linguist is used by GitHub language stats and supports `linguist-generated`
  and `linguist-vendored` attributes to avoid counting generated/vendor content as
  implementation complexity.
- Source:
  - https://github.com/github-linguist/linguist
  - https://docs.github.com/repositories/working-with-files/managing-files/customizing-how-changed-files-appear-on-github

2. Code complexity
- Cyclomatic complexity for Python functions is used as a primary structural
  complexity signal.
- Threshold bands are compatible with Radon’s widely-used grading guidance.
- Source:
  - https://radon.readthedocs.io/en/master/intro.html#cyclomatic-complexity

3. Hotspots (complexity x change)
- Complexity alone misses operational risk; hotspots prioritize complex files that
  also change frequently.
- This follows hotspot analysis practice used in modern code health tooling.
- Source:
  - https://docs.enterprise.codescene.io/versions/6.7.8/guides/technical/hotspots.html

4. Change dynamics
- Local Git churn and contributor activity provide delivery-context risk signals.
- Optional GitHub Stats API can add repository-level code-frequency and contributor
  views for remotely hosted repos.
- Source:
  - https://docs.github.com/rest/metrics/statistics

5. Representation pattern
- Dual-scope reporting (`git_tracked`, `workspace`) captures both release-state
  complexity and in-flight complexity.
- Exclusion-first policy prevents generated outputs from inflating complexity,
  matching the requirement to reflect script complexity rather than output volume.
