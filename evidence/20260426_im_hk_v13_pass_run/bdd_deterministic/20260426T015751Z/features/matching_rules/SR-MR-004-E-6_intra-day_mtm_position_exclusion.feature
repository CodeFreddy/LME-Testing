Feature: Intra-Day MTM Position Exclusion
  SR-MR-004-E-6
  # paragraph_ids: MR-004-E-6
  Intra-Day MTM Position Exclusion

  @positive @priority_high  # TC-SR-MR-004-E-6-positive-01
  Scenario: Positions to be settled today excluded from intra-day MTM calculation
    Given Stock positions exist that are to be settled today
    And Positions include unposted debit, unposted credit, cash prepayment, and allocated shares
    When Intra-day MTM and margin requirement calculation is performed
    Then Positions to be settled today are excluded from the calculation
    And MTM and margin requirement are not collected from positions being settled

  @boundary @priority_high  # TC-SR-MR-004-E-6-boundary-01
  Scenario: Position at settlement boundary correctly classified for exclusion
    Given A stock position with settlement date matching the collection time
    And The collection time of intra-day MTM equals the settlement obligation time
    When Intra-day MTM and margin requirement calculation is performed
    Then Position is excluded from calculation if settlement is at collection time
    And No duplicate collection occurs for positions being settled

  @data_validation @priority_high  # TC-SR-MR-004-E-6-data_validation-01
  Scenario: Excluded positions not present in MTM calculation result
    Given Stock positions include unposted debit positions
    And Stock positions include unposted credit positions
    And Stock positions include cash prepayment positions
    And Stock positions include allocated shares to be settled today
    When Intra-day MTM and margin requirement calculation is performed
    Then None of the excluded position types appear in the MTM calculation result
    And Margin requirement calculation excludes all specified position types
