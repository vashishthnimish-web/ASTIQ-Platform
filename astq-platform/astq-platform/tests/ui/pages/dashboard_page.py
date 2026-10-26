from selenium.webdriver.common.by import By

from tests.ui.pages.base_page import BasePage


class DashboardPage(BasePage):
    def load(self):
        return self.open("/")

    def total_runs(self) -> int:
        return int(self.find("#stat-total").text)

    def go_to_suites(self):
        self.click("#nav-suites")
        return self

    def suite_keys(self):
        self.find("#suite-table")
        return [r.get_attribute("data-suite") for r in self.driver.find_elements(By.CSS_SELECTOR, "#suite-table tbody tr")]

    def go_to_history(self):
        self.click("#nav-runs")
        return self
