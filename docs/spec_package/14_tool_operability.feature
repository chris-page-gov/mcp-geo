Feature: MCP Geo Live Tool Operability
  To reduce deployment surprises
  As a platform maintainer
  I want measurable live evidence that every registered tool is operable or explicitly blocked

  Background:
    Given a completed live harness report at:
      """
      data/evaluation_results_live_review_2026-02-21_after_patch2_full.json
      """
    And a completed missing-tool probe report at:
      """
      data/live_missing_tools_probe_report_2026-02-21.json
      """
    And a computed spec coverage report at:
      """
      data/spec_tool_operability_coverage_2026-02-21.json
      """

  @REQ-LIVE-TOOLS-01
  Scenario: Every registered tool has live execution evidence
    When I evaluate the registered tool set against harness and probe evidence
    Then each registered tool must be one of:
      | classification |
      | functional     |
      | blocked_auth   |
    And unresolved tools must equal 0

  @REQ-LIVE-TOOLS-02
  Scenario: Functional live operability threshold
    When I compute functional operability percentage
    Then functional coverage must be at least 95%

  @REQ-LIVE-TOOLS-03
  Scenario: Live harness quality floor
    When I compute total live harness score
    Then the score percentage must be at least 90%

  @REQ-LIVE-TOOLS-04
  Scenario: Entitlement blocker is explicit and actionable
    Given at least one tool is blocked by auth or entitlement
    Then the report must include tool name and normalized upstream error code
    And the blocker must be listed in release risk notes
