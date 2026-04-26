Feature: Initial Margin Calculation using IMRPF
  SR-MR-001-B2-1
  # paragraph_ids: MR-001-B2-1
  Initial Margin Calculation using IMRPF

  @positive @priority_high  # TC-SR-MR-001-B2-1-positive-01
  Scenario: Calculate total MTM and margin requirement using IMRPF
    Given HKSCC VaR Platform is operational
    And Initial Margin Risk Parameter File (IMRPF) has been disseminated for the current business day
    And Clearing Participant has a portfolio of HKSCC clearable instruments
    When the system calculates the total MTM and margin requirement using the IMRPF
    Then the initial margin requirement is calculated for the portfolio
    And portfolio margin component is applied for Primary Tier (Tier P) instruments
    And flat rate margin component is applied for Non-constituent Tier (Tier N) instruments

  @boundary @priority_high  # TC-SR-MR-001-B2-1-boundary-01
  Scenario: Calculate margin with minimum portfolio positions
    Given HKSCC VaR Platform is operational
    And IMRPF has been disseminated for the current business day
    And Clearing Participant has a portfolio with single instrument position
    When the system calculates the initial margin requirement for the minimal portfolio
    Then the margin calculation completes successfully
    And appropriate margin component is applied based on instrument tier classification

  @data_validation @priority_high  # TC-SR-MR-001-B2-1-data_validation-01
  Scenario: Validate IMRPF file structure and risk parameters
    Given HKSCC VaR Platform is operational
    And IMRPF file is received for processing
    When the system validates the IMRPF file structure and key risk parameters
    Then the file contains all required key risk parameters for IM calculation
    And file format is valid for daily dissemination to Clearing Participants
