# Selenium page objects

Page objects live in `tests/ui/pages/` (`BasePage`, `DashboardPage`) following the Page Object
pattern: tests describe *what* a user does; page classes know *how* (stable CSS ids such as
`#nav-suites`, `#suite-table`, `#stat-total`). This top-level `pages/` folder is kept as a pointer
to match the agreed repository layout.
