Feature: EWMA Risk Measure Calculation
  SR-MR-002-B2-1
  # paragraph_ids: MR-002-B2-1
  EWMA Risk Measure Calculation

  @positive @priority_high  # TC-SR-MR-002-B2-1-positive-01
  Scenario: Calculate risk measure using EWMA rescaled historical returns
    Given historical returns data is available for the look back period
    And EWMA parameters are configured for risk measure calculation
    When the system calculates the risk measure using EWMA rescaled historical returns
    Then the risk measure is calculated based on EWMA rescaled historical returns
    And discrete data points on the distribution tail are selected for calculation

  @boundary @priority_high  # TC-SR-MR-002-B2-1-boundary-01
  Scenario: Calculate risk measure at look back period boundary
    Given historical returns data spans exactly the look back period
    And EWMA calculation is configured for the defined period
    When the system calculates the risk measure at the boundary of the look back period
    Then the EWMA calculation correctly includes data points at the period boundary
    And discrete data point selection includes valid tail boundary points

  @data_validation @priority_high  # TC-SR-MR-002-B2-1-data_validation-01
  Scenario: Validate historical returns data for EWMA calculation
    Given historical returns data is submitted for risk measure calculation
    When the system validates the historical returns data for EWMA processing
    Then historical returns data is valid for EWMA rescaling
    And data points are suitable for discrete selection on distribution tail
