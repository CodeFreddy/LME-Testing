Feature: Position Processing and Adjustments
  SR-MR-012-B-1
  # paragraph_ids: MR-012-B-1
  Position Processing and Adjustments

  @positive @priority_high  # TC-SR-MR-012-B-1-positive-01
  Scenario: Combine Multi-Counter Eligible Securities Positions
    Given Positions traded on multi-counter eligible securities
    And Positions have different trading counters but same settlement counter
    When The system processes positions for marginable position generation
    And The system combines multi-counter eligible securities positions into their settlement counters
    Then Positions are correctly aggregated by settlement counter
    And Combined positions reflect the total position for each settlement counter

  @boundary @priority_high  # TC-SR-MR-012-B-1-boundary-01
  Scenario: Position Exclusion for Specific Stock/Cash Collateral Coverage
    Given Positions that are covered by specific stock collateral or specific cash collateral
    And Positions at the boundary of collateral coverage threshold
    When The system processes positions for marginable position generation
    And The system applies specific stock/cash collateral covered position exclusion logic
    Then Positions covered by specific stock collateral are excluded from margin calculation
    And Positions covered by specific cash collateral are excluded from margin calculation

  @data_validation @priority_high  # TC-SR-MR-012-B-1-data_validation-01
  Scenario: Validate Corporate Action Adjustment and Cross-Day Netting
    Given Position data requiring corporate action adjustment
    And Positions from multiple trading days requiring cross-day netting
    When The system validates and processes position adjustments
    And The system applies corporate action position adjustment logic
    And The system applies cross-day position netting logic
    Then All positions are correctly adjusted for corporate actions
    And All positions are correctly cross-day netted
    And Adjusted and netted positions are included in marginable position report
