Feature: Corporate Action Position Adjustment Repetition
  SR-MR-004-E-1
  # paragraph_ids: MR-004-E-1
  Corporate Action Position Adjustment Repetition

  @positive @priority_high  # TC-SR-MR-004-E-1-positive-01
  Scenario: Repeat position adjustment for multiple corporate actions with different ex-dates
    Given A clearing participant holds positions in an instrument
    And Multiple corporate actions are announced for the same instrument
    And The corporate actions have different ex-dates
    When The system processes corporate action position adjustments
    And Each corporate action is processed according to its ex-date
    Then Position adjustment is repeated for each corporate action
    And Each adjustment is applied separately according to the trade date of the position
    And All adjustments are reflected in the final position

  @negative @priority_high  # TC-SR-MR-004-E-1-negative-01
  Scenario: Single corporate action does not require repetition
    Given A clearing participant holds positions in an instrument
    And Only one corporate action is announced for the instrument
    And The position is traded before the ex-date
    When The system processes the corporate action position adjustment
    And Only one corporate action exists for the instrument
    Then Position adjustment is performed exactly once
    And No repetition of adjustment occurs
    And The adjusted position reflects the single corporate action
