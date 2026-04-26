Feature: Cross-Day Position Netting
  SR-MR-004-C-2
  # paragraph_ids: MR-004-C-2
  Cross-Day Position Netting

  @positive @priority_high  # TC-SR-MR-004-C-2-positive-01
  Scenario: Positions of same instrument aggregated across different trade and settlement dates
    Given Multiple positions exist for the same instrument
    And Positions have different trade dates
    And Positions have different settlement dates
    When Cross-day netting calculation is performed
    Then One netted quantity is produced for the instrument
    And One netted contract value is produced for the instrument

  @boundary @priority_high  # TC-SR-MR-004-C-2-boundary-01
  Scenario: Single position returns unchanged as netted result
    Given Only one position exists for an instrument
    When Cross-day netting calculation is performed
    Then Netted quantity equals the single position quantity
    And Netted contract value equals the single position contract value

  @data_validation @priority_high  # TC-SR-MR-004-C-2-data_validation-01
  Scenario: Netted quantity and contract value match sum of input positions
    Given Multiple positions for the same instrument with known quantities
    And Each position has a known contract value
    When Cross-day netting calculation is performed
    Then Netted quantity equals the sum of all position quantities
    And Netted contract value equals the sum of all contract values
