Feature: Initial Margin Risk Parameter File Dissemination
  SR-MR-001-B1-1
  # paragraph_ids: MR-001-B1-1
  Initial Margin Risk Parameter File Dissemination

  @positive @priority_high  # TC-SR-MR-001-B1-1-positive-01
  Scenario: Successful daily dissemination of IMRPF to CPs
    Given VaR Platform is launched and operational
    And HKSCC CPs are registered and active
    When Daily dissemination of the Initial Margin Risk Parameter File is triggered
    Then IMRPF containing key risk parameters is disseminated to all HKSCC CPs

  @negative @priority_high  # TC-SR-MR-001-B1-1-negative-01
  Scenario: IMRPF dissemination failure when file is not available
    Given VaR Platform is launched
    And IMRPF file generation has failed or file is not available
    When Daily dissemination of the Initial Margin Risk Parameter File is triggered
    Then Dissemination fails and appropriate error handling is triggered
    And CPs do not receive an invalid or incomplete file

  @data_validation @priority_high  # TC-SR-MR-001-B1-1-data_validation-01
  Scenario: Validation of IMRPF key risk parameters content
    Given IMRPF file is generated for daily dissemination
    When Key risk parameters in the IMRPF are validated
    Then All key risk parameters required for calculating IM are present and valid
