// Auto-refresh a run detail page until the run reaches a terminal state.
(function () {
  var el = document.getElementById("run-live");
  if (!el || el.dataset.terminal === "true") return;
  var id = el.dataset.runId;
  var timer = setInterval(function () {
    fetch("/api/runs/" + id, { headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (run) {
        if (["PASSED", "FAILED", "ERROR", "CANCELLED"].indexOf(run.status) !== -1) {
          clearInterval(timer);
          window.location.reload();
        }
      })
      .catch(function () { /* keep polling; transient errors are fine */ });
  }, 2000);
})();
