from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class BasePage:
    def __init__(self, driver, base_url):
        self.driver, self.base_url = driver, base_url.rstrip("/")
        self.wait = WebDriverWait(driver, 10)

    def open(self, path=""):
        self.driver.get(f"{self.base_url}{path}")
        return self

    def find(self, css):
        return self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, css)))

    def click(self, css):
        self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, css))).click()

    def heading(self):
        return self.find("h1").text
