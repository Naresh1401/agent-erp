"""Playwright E2E tests for the AgentERP frontend."""

import re

from playwright.sync_api import Page, expect


def test_homepage_loads(page: Page):
    """Verify the app loads and shows the sidebar."""
    page.goto("http://localhost:3000")
    expect(page.locator("text=AgentERP")).to_be_visible()
    expect(page.locator("text=Dashboard")).to_be_visible()
    expect(page.locator("text=Agent Monitor")).to_be_visible()


def test_navigation(page: Page):
    """Verify all nav links work."""
    page.goto("http://localhost:3000")

    for label in ["Agent Monitor", "Orders", "Inventory", "Documents", "Migration"]:
        page.click(f"text={label}")
        expect(page.locator(f"h2:has-text('{label.split()[0]}')")).to_be_visible()


def test_agent_dispatch_panel(page: Page):
    """Verify agent dispatch buttons are visible."""
    page.goto("http://localhost:3000/agents")
    expect(page.locator("text=Document Processor")).to_be_visible()
    expect(page.locator("text=Order Processor")).to_be_visible()
    expect(page.locator("text=Inventory Intelligence")).to_be_visible()
    expect(page.locator("text=Data Migration")).to_be_visible()


def test_document_upload_form(page: Page):
    """Verify document upload form is functional."""
    page.goto("http://localhost:3000/documents")
    expect(page.locator("text=Upload Document")).to_be_visible()

    # Fill in sample data
    page.click("text=invoice-2024-001.pdf")  # Quick load button
    expect(page.locator("input[placeholder*='invoice']")).to_have_value("invoice-2024-001.pdf")


def test_migration_schema_display(page: Page):
    """Verify migration page shows legacy schema."""
    page.goto("http://localhost:3000/migration")
    expect(page.locator("text=Legacy ERP Schema")).to_be_visible()
    expect(page.locator("text=tbl_cust")).to_be_visible()
    expect(page.locator("text=Run Migration Agent")).to_be_visible()
