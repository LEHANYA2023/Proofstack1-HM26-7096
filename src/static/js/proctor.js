/**
 * proctor.js — lightweight, honest assessment-integrity monitor.
 *
 * What this deliberately does NOT do, and why:
 *   - No webcam / gaze tracking. Reliable gaze estimation needs a
 *     calibrated camera and per-user baseline; a flaky "you looked away"
 *     verdict is worse than none, and raises real consent/privacy
 *     questions we can't do justice to in a hackathon window.
 *   - No per-person keystroke *identity* biometrics (i.e. "prove this is
 *     still Priya typing"). That needs an enrolled typing profile per
 *     student, collected with consent, over multiple sessions.
 *
 * What it DOES do — cheap signals that are each gameable alone, but
 * expensive to fake all at once, all disclosed to the candidate up front:
 *   1. one live session per attempt (server-enforced — see assessments.py)
 *   2. tab-switch / window-blur detection
 *   3. paste detection when there's no matching local typing history
 *   4. dev-tools-open heuristic (outer/inner window size delta)
 *   5. fullscreen-exit detection (if fullscreen was requested)
 *   6. keystroke-cadence anomaly (bot/script-like uniform timing)
 *
 * Every event is POSTed to /api/assessments/attempts/<id>/event where the
 * SERVER decides the severity and updates attempt.integrity_score — this
 * file never computes or shows a trust score to the candidate itself.
 */

function createProctor({ attemptId, sessionToken, token, answerElId }) {
  let keyTimestamps = [];
  let localTypedChars = 0;
  let cadenceTimer = null;

  async function report(type, detail) {
    try {
      await fetch(`/api/assessments/attempts/${attemptId}/event`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ type, detail, session_token: sessionToken }),
      });
    } catch (e) {
      // Network hiccups shouldn't crash the test the candidate is taking.
      console.warn("proctor: failed to report event", type, e);
    }
  }

  function onVisibilityChange() {
    if (document.hidden) report("focus_loss", "tab/window hidden");
  }

  function onBlur() {
    report("focus_loss", "window lost focus");
  }

  function onPaste(e) {
    const pasted = (e.clipboardData || window.clipboardData).getData("text") || "";
    // A large paste with little to no local typing beforehand is the
    // clearest cheap signal of "answer copied in from elsewhere."
    if (pasted.length > 40 && localTypedChars < pasted.length * 0.3) {
      report("paste_no_history", `pasted ${pasted.length} chars vs ${localTypedChars} typed so far`);
    }
  }

  function onContextMenu(e) {
    e.preventDefault();
    report("context_menu_blocked", "right-click attempted");
  }

  function onFullscreenChange() {
    if (!document.fullscreenElement) report("fullscreen_exit", "left fullscreen mode");
  }

  function checkDevtools() {
    const widthDelta = window.outerWidth - window.innerWidth;
    const heightDelta = window.outerHeight - window.innerHeight;
    // Generous thresholds — this is a heuristic, not a certainty, and is
    // reported as a soft flag for a human reviewer, never an auto-fail.
    if (widthDelta > 200 || heightDelta > 200) {
      report("devtools_suspected", `outer/inner window delta ${widthDelta}x${heightDelta}`);
    }
  }

  function onKeyDown() {
    const now = performance.now();
    if (keyTimestamps.length > 0) {
      const gap = now - keyTimestamps[keyTimestamps.length - 1];
      keyTimestamps.push(now);
    } else {
      keyTimestamps.push(now);
    }
    localTypedChars += 1;

    if (keyTimestamps.length >= 25) {
      const intervals = [];
      for (let i = 1; i < keyTimestamps.length; i++) {
        intervals.push(keyTimestamps[i] - keyTimestamps[i - 1]);
      }
      fetch(`/api/assessments/attempts/${attemptId}/event`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ type: "cadence_check", intervals_ms: intervals, session_token: sessionToken }),
      }).catch(() => {});
      keyTimestamps = [];
    }
  }

  function start() {
    document.addEventListener("visibilitychange", onVisibilityChange);
    window.addEventListener("blur", onBlur);
    document.addEventListener("contextmenu", onContextMenu);
    document.addEventListener("fullscreenchange", onFullscreenChange);
    cadenceTimer = setInterval(checkDevtools, 4000);

    const el = document.getElementById(answerElId);
    if (el) {
      el.addEventListener("paste", onPaste);
      el.addEventListener("keydown", onKeyDown);
    }
  }

  function stop() {
    document.removeEventListener("visibilitychange", onVisibilityChange);
    window.removeEventListener("blur", onBlur);
    document.removeEventListener("contextmenu", onContextMenu);
    document.removeEventListener("fullscreenchange", onFullscreenChange);
    if (cadenceTimer) clearInterval(cadenceTimer);
    const el = document.getElementById(answerElId);
    if (el) {
      el.removeEventListener("paste", onPaste);
      el.removeEventListener("keydown", onKeyDown);
    }
  }

  return { start, stop };
}
