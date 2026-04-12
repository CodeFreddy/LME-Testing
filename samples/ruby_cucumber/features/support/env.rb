# frozen_string_literal: true

require 'bundler/setup'
require 'cucumber'
require 'selenium-webdriver'
require 'watir'
require 'rest-client'
require 'json'
require 'pry'

# LME Test Client Library
require_relative '../../lib/lme_client'
require_relative '../../lib/lme_api'
require_relative '../../lib/lme_post_trade'

World do
  # Share state between steps
  Object.new.tap do |world|
    world.instance_variable_set(:@session, nil)
    world.instance_variable_set(:@response, nil)
    world.instance_variable_set(:@browser, nil)
    world.instance_variable_set(:@order_params, {})
  end
end

# Configure Selenium for local development
Selenium::WebDriver::Firefox::ServiceManager.class_eval do
  def self.binary_path=(path)
    @binary_path = path
  end
end if ENV['FIREFOX_BINARY']

def setup_browser
  options = Selenium::WebDriver::Firefox::Options.new
  options.headless! if ENV['HEADLESS']

  browser = Watir::Browser.new :firefox, options: options
  at_exit { browser.close }
  browser
end

def setup_api_client
  base_url = ENV['LME_API_URL'] || 'https://lme-test.internal/api/v1'
  LME::API::Client.new(base_url: base_url)
end

Before('@api') do
  @api = setup_api_client
end

Before('@web') do
  @browser = setup_browser
  @browser.cookies.clear
end

Before('@auth') do
  @session = LME::Client.login(
    username: ENV['LME_USERNAME'] || 'test_user',
    password: ENV['LME_PASSWORD'] || 'test_password'
  )
end

After('@web') do
  @browser.close if @browser
end

After do |scenario|
  # Log scenario result for audit trail
  puts "Scenario: #{scenario.name} - #{scenario.status}"

  # Capture screenshot on failure for @web scenarios
  if scenario.failed? && @browser
    screenshot = "screenshots/#{scenario.name.gsub(/\s+/, '_')}_#{Time.now.strftime('%Y%m%d_%H%M%S')}.png"
    @browser.screenshot.save(screenshot)
    embed screenshot, 'image/png'
  end
end
