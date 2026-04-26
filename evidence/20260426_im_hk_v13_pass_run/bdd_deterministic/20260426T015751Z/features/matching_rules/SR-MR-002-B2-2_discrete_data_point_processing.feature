Feature: Discrete Data Point Processing
  SR-MR-002-B2-2
  # paragraph_ids: MR-002-B2-2
  Discrete Data Point Processing

  @positive @priority_high  # TC-SR-MR-002-B2-2-positive-01
  Scenario: Process discrete data points without interpolation
    Given An Initial Margin Risk Parameter File with discrete data points on the distribution tail
    And The data points are selected for FHS ES calculation
    When The system processes the discrete data points for margin calculation
    Then The calculation proceeds using only the discrete data points
    And No interpolation is performed between the discrete data points

  @negative @priority_high  # TC-SR-MR-002-B2-2-negative-01
  Scenario: Reject interpolation attempt between discrete data points
    Given An Initial Margin Risk Parameter File with discrete data points
    And A request or configuration that would require interpolation between data points
    When The system attempts to process the data with interpolation between discrete points
    Then The interpolation is not performed
    And The system uses only the discrete data points as provided
