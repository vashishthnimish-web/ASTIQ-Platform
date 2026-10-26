import pytest

from tests.ui.pages.dashboard_page import DashboardPage

pytestmark = pytest.mark.ui


@pytest.fixture()
def page(driver, live_server, screenshot_on_failure):
    return DashboardPage(driver, live_server)


def test_dashboard_loads_with_heading(page):
    page.load()
    assert page.heading() == "Dashboard"
    assert page.total_runs() >= 0


def test_suite_catalogue_lists_registered_suites(page):
    page.load().go_to_suites()
    keys = page.suite_keys()
    assert {"unit_regression", "api_smoke", "ui_smoke"} <= set(keys)


def test_run_history_page_reachable(page):
    page.load().go_to_history()
    assert page.heading() == "Run History"
