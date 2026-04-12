# frozen_string_literal: true

require 'cucumber/rspec/driver'
require 'selenium-webdriver'

# Hooks for test lifecycle management

Before('@smoke') do
  # Only run smoke tests with fast, critical paths
  @fast_mode = true
end

Before('@regression') do
  # Full regression tests with all validations
  @fast_mode = false
end

Before('@trade') do
  # Ensure trading session is authenticated
  @session ||= LME::Client.login(
    username: ENV['LME_USERNAME'] || 'trader_001',
    password: ENV['LME_PASSWORD'] || 'trade_pass'
  )
end

Before('@post_trade') do
  # Post-trade operations require cleared trades
  @cleared_trades = []
end

After('@post_trade') do
  # Cleanup: release any held positions
  @cleared_trades.each do |trade_id|
    LME::PostTrade.release_position(trade_id) rescue nil
  end
end

# Audit trail hook - logs all step definitions for traceability
AfterStep do |scenario, step|
  # Record step execution for audit
  AuditLog.record(
    scenario: scenario.name,
    step: step.text,
    status: scenario.status,
    timestamp: Time.now.utc.iso8601
  )
rescue => e
  puts "Audit logging failed: #{e.message}"
end

# Retry hook for flaky tests
Cucumber::Rspec::Driver.class_eval do
  alias original_after after

  def after(*args)
    retry_count = ENV.fetch('RETRY_COUNT', 0).to_i
    retry_count.times do |i|
      begin
        return original_after(*args)
      rescue => e
        puts "Retry #{i + 1}/#{retry_count} failed: #{e.message}"
        raise if i == retry_count - 1
      end
    end
  end
end
