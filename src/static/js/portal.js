const TOKEN = localStorage.getItem('proofstack_token');
const ME = JSON.parse(localStorage.getItem('proofstack_user') || 'null');
const portal = document.body.dataset.portal;

// ---- Auth guard ----
if (!TOKEN || !ME || ME.role !== portal) {
  location.href = '/login/' + portal;
}

// ---- Tiny API helper ----
const API = {
  get: async (u) => {
    const r = await fetch(u, { headers: { Authorization: `Bearer ${TOKEN}` } });
    return { ok: r.ok, data: await r.json().catch(() => ({})) };
  },
  send: async (u, method = 'POST', body = {}) => {
    const r = await fetch(u, {
      method,
      headers: { Authorization: `Bearer ${TOKEN}`, 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    return { ok: r.ok, data: await r.json().catch(() => ({})) };
  },
};

const esc = (s) =>
  String(s ?? '').replace(/[&<>'"]/g, (c) =>
    ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[c])
  );

const initials = (n) =>
  String(n || 'U').split(' ').map((x) => x[0]).slice(0, 2).join('').toUpperCase();

// ---- Chart helper -------------------------------------------------------
// Renders/replaces a Chart.js chart on the canvas with id `canvasId`.
// Destroys the previous chart on that id first so re-rendering a tab never
// stacks charts on top of each other or leaks memory across tab switches.
const CHARTS = {};
const CHART_COLORS = ['#c7f36b', '#6be7ff', '#b89cff', '#ffb86b', '#ff86b5', '#79e2a8'];
function renderChart(canvasId, config) {
  const el = document.getElementById(canvasId);
  if (!el || typeof Chart === 'undefined') return;
  if (CHARTS[canvasId]) CHARTS[canvasId].destroy();
  Chart.defaults.color = '#8c96a7';
  Chart.defaults.borderColor = '#252c37';
  Chart.defaults.font.family = 'Manrope, system-ui, sans-serif';
  CHARTS[canvasId] = new Chart(el.getContext('2d'), config);
}

// ---- Per-portal section list + default tab ----
const SECTIONS = {
  student: [
    { id: 'overview', label: 'Overview', icon: '◈' },
    { id: 'profile', label: 'Profile + evidence links', icon: '◎' },
    { id: 'submit', label: 'Add proof', icon: '＋' },
    { id: 'assignments', label: 'Assignments', icon: '▤' },
    { id: 'interviews', label: 'AI interviews', icon: '◆' },
    { id: 'ranking', label: 'Ranking', icon: '⌂' },
    { id: 'reviews', label: 'Honest reviews', icon: '◇' },
    { id: 'opportunities', label: 'Opportunities', icon: '✉' },
    { id: 'mentor', label: 'Private mentor', icon: '↗' },
  ],
  expert: [
    { id: 'queue', label: 'Review queue', icon: '◇' },
    { id: 'mentor', label: 'Mentor inbox', icon: '↗' },
  ],
  recruiter: [
    { id: 'candidates', label: 'Candidate room', icon: '◉' },
    { id: 'ranking', label: 'Ranking', icon: '⌂' },
    { id: 'assignments', label: 'Assignments', icon: '▤' },
    { id: 'insights', label: 'Talent map', icon: '⌁' },
    { id: 'opportunities', label: 'Opportunities sent', icon: '✉' },
    { id: 'ai', label: 'AI analyst', icon: '✦' },
  ],
  institution: [
    { id: 'overview', label: 'Control room', icon: '◈' },
    { id: 'students', label: 'Student registry', icon: '◎' },
  ],
};

// ---- Global state ----
const state = {
  tab: (SECTIONS[portal] && SECTIONS[portal][0].id) || 'overview',
  experts: [],
  activeExpert: null,
};

// ---- Layout (runs once) ----
function layout() {
  const titles = {
    student: 'Student portal',
    expert: 'Expert portal',
    recruiter: 'Recruiter portal',
    institution: 'Institution portal',
  };
  const roleLabels = {
    student: '01 / CANDIDATE',
    expert: '02 / HUMAN REVIEW',
    recruiter: '03 / HIRING',
    institution: '04 / TRUST LAYER',
  };
  const sections = SECTIONS[portal] || [];

  document.body.className = 'portal-body';
  document.body.dataset.portal = portal;

  document.getElementById('app').innerHTML = `
    <div class="shell">
      <aside class="sidebar">
        <div class="side-brand">PROOF<span>STACK</span></div>
        <div class="side-role">${roleLabels[portal]}</div>
        <div class="side-title">${titles[portal]}</div>
        <div class="side-nav">
          ${sections
            .map(
              (x, i) =>
                `<button data-tab="${x.id}" class="${i === 0 ? 'active' : ''}">${x.icon} ${x.label}</button>`
            )
            .join('')}
        </div>
        <div style="margin-top:45px">
          <div class="tiny">SIGNED IN AS</div>
          <div style="margin-top:7px;font-weight:700;font-size:12px">${esc(ME.name)}</div>
          <button id="logout" class="logout" style="background:none;border:0;padding:12px 0">↗ Sign out</button>
        </div>
      </aside>
      <main class="content"><div id="view"></div></main>
    </div>
    <div id="modal" class="modal"><div class="modal-card" id="modal-card"></div></div>
  `;

  document.querySelectorAll('[data-tab]').forEach((b) => {
    b.onclick = () => {
      document.querySelectorAll('[data-tab]').forEach((x) => x.classList.remove('active'));
      b.classList.add('active');
      state.tab = b.dataset.tab;
      renderTab();
    };
  });

  document.getElementById('logout').onclick = () => {
    localStorage.clear();
    location.href = '/';
  };
}

// ---- Shared bits ----
function pageHeader(title, sub = '') {
  return `
    <div class="topline">
      <div>
        <div class="eyebrow">${portal.toUpperCase()} / ${state.tab.toUpperCase()}</div>
        <h1>${title}</h1>
        <div class="muted">${sub}</div>
      </div>
      <div class="user-chip">${esc(ME.name)} · ${esc(ME.track || 'hybrid')}</div>
    </div>`;
}

function openModal(html) {
  document.getElementById('modal-card').innerHTML = html;
  const modal = document.getElementById('modal');
  modal.classList.add('open');
  modal.onclick = (e) => {
    if (e.target.id === 'modal') modal.classList.remove('open');
  };
}

// ---- Router ----
async function renderTab() {
  try {
    if (portal === 'student') return studentTab();
    if (portal === 'expert') return expertTab();
    if (portal === 'recruiter') return recruiterTab();
    if (portal === 'institution') return institutionTab();
  } catch (e) {
    console.error(e);
    document.getElementById('view').innerHTML = pageHeader('Something went wrong', String(e));
  }
}

// ============================================================
// STUDENT
// ============================================================
async function studentTab() {
  if (state.tab === 'overview') return studentOverview();
  if (state.tab === 'profile') return studentProfile();
  if (state.tab === 'submit') return studentSubmit();
  if (state.tab === 'assignments') return studentAssignments();
  if (state.tab === 'interviews') return studentInterviews();
  if (state.tab === 'ranking') return studentRanking();
  if (state.tab === 'reviews') return studentReviews();
  if (state.tab === 'opportunities') return studentOpportunities();
  if (state.tab === 'mentor') return studentMentor();
}

async function studentOverview() {
  const r = await API.get('/api/dashboard/student');
  const subs = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('Your proof, in progress.', 'A profile that shows evidence beyond marks and job titles.') +
    `<div class="grid">
       <div class="card span-4">
         <div class="tiny">EVIDENCE ITEMS</div>
         <div class="metric">${subs.length}<small> projects / proofs</small></div>
         <p>Every project can be technical, research, communication, design, operations or another real skill.</p>
       </div>
       <div class="card span-4">
         <div class="tiny">PROFILE TRACK</div>
         <div class="metric" style="font-size:26px">${esc(ME.track || 'technical')}</div>
         <p>Choose the kind of evidence that actually represents your strengths.</p>
       </div>
       <div class="card span-4">
         <div class="tiny">MENTORING</div>
         <div class="metric" style="font-size:26px">PRIVATE</div>
         <p>Ask a senior expert what to improve without making the conversation public.</p>
       </div>
       <div class="card span-8">
         <h2>Latest evidence</h2>
         <div class="list">
           ${
             subs
               .map(
                 (s) => `
             <div class="list-item">
               <div class="row">
                 <div>
                   <b>Submission ${esc(s.id.slice(0, 8))}</b>
                   <div class="tiny">Proof score ${s.scores.proof_score} · build ${s.build_passed ? 'passed' : 'needs review'}</div>
                 </div>
                 <button class="btn btn-ghost" onclick="showSubmission('${s.id}')">Inspect evidence</button>
               </div>
             </div>`
               )
               .join('') || '<div class="empty">No submissions yet. Start with one piece of work.</div>'
           }
         </div>
       </div>
       <div class="card span-4">
         <h2>AI career coach</h2>
         <p>Ask about resumes, projects, interviews or non-technical career paths.</p>
         <div class="chat" style="height:310px">
           <div id="ai-log" class="chat-log">
             <div class="bubble them">Tell me what you want to improve. I will keep the advice practical and evidence-based.</div>
           </div>
           <div class="chat-form">
             <input id="ai-input" placeholder="e.g. How do I improve my resume?">
             <button class="btn btn-primary" onclick="askAI()">→</button>
           </div>
         </div>
       </div>
     </div>`;
}

async function studentProfile() {
  document.getElementById('view').innerHTML =
    pageHeader('Your profile is your context.', 'Give recruiters the information a score cannot.') +
    `<div class="card">
       <form id="profile-form" class="grid">
         <label class="span-6">Name<input name="name" value="${esc(ME.name)}"></label>
         <label class="span-6">Headline<input name="headline" value="${esc(ME.headline || '')}"></label>
         <label class="span-6">Track
           <select name="track">
             <option value="technical" ${ME.track === 'technical' ? 'selected' : ''}>technical</option>
             <option value="hybrid" ${ME.track === 'hybrid' ? 'selected' : ''}>hybrid</option>
             <option value="non-technical" ${ME.track === 'non-technical' ? 'selected' : ''}>non-technical</option>
           </select>
         </label>
         <label class="span-6">Skills<input name="skills" value="${esc((ME.skills || []).join(', '))}"></label>
         <label class="span-12">Bio<textarea name="bio" style="min-height:100px">${esc(ME.bio || '')}</textarea></label>
         <label class="span-6">Resume URL<input name="resume_url" value="${esc(ME.resume_url || '')}" placeholder="https://..."></label>
         <label class="span-6">GitHub profile<input name="github_profile_url" value="${esc(ME.github_profile_url || '')}" placeholder="https://github.com/..."></label>
         <label class="span-6">Portfolio / projects<input name="portfolio_url" value="${esc(ME.portfolio_url || '')}" placeholder="https://..."></label>
         <label class="span-6">Availability
           <select name="availability">
             <option value="open_to_opportunities" ${ME.availability === 'open_to_opportunities' ? 'selected' : ''}>Open to opportunities</option>
             <option value="selectively_available" ${ME.availability === 'selectively_available' ? 'selected' : ''}>Selective</option>
             <option value="not_available" ${ME.availability === 'not_available' ? 'selected' : ''}>Not available</option>
           </select>
         </label>
         <div class="span-12"><button class="btn btn-primary">Save profile →</button></div>
       </form>
     </div>`;

  document.getElementById('profile-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    const r = await API.send('/api/auth/profile', 'PUT', body);
    if (r.ok) {
      Object.assign(ME, r.data);
      localStorage.setItem('proofstack_user', JSON.stringify(ME));
      alert('Profile updated.');
    } else {
      alert(r.data.error || 'Save failed');
    }
  };
}

async function studentSubmit() {
  const r = await API.get('/api/challenges');
  const challenges = Array.isArray(r.data) ? r.data : [];
  state.challenges = challenges;

  document.getElementById('view').innerHTML =
    pageHeader('Add evidence, not noise.', 'Technical and non-technical challenges are both first-class.') +
    `<div class="grid">
       <div class="card span-5">
         <h2>Choose a challenge</h2>
         <div class="list">
           ${
             challenges
               .map(
                 (c, i) => `
             <button class="list-item" data-challenge="${c.id}" style="text-align:left" onclick="pickChallenge('${c.id}')">
               <div class="row">
                 <b>${esc(c.title)}</b>
                 <span class="tag accent">${esc(c.track)}</span>
               </div>
               <p>${esc(c.description)}</p>
               <span class="tiny">${esc(c.difficulty)} · ${(c.tags || []).map(esc).join(' · ')}</span>
             </button>`
               )
               .join('') || '<div class="empty">No challenges available yet. You can still submit evidence below.</div>'
           }
         </div>
       </div>
       <div class="card span-7">
         <div id="submission-form"></div>
       </div>
     </div>`;

  // Show a real, fillable form immediately — no extra click needed.
  window.pickChallenge(challenges[0] ? challenges[0].id : '');
}

async function studentReviews() {
  const r = await API.get('/api/dashboard/student');
  const subs = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('Transparent feedback.', 'See what reviewers saw and what they want you to improve.') +
    `<div class="list">
       ${
         subs
           .map(
             (s) => `
         <div class="card">
           <div class="row">
             <div>
               <h2>Evidence review</h2>
               <div class="tiny">Submission ${s.id.slice(0, 8)} · proof score ${s.scores.proof_score}</div>
             </div>
             <button class="btn btn-ghost" onclick="loadReviews('${s.id}')">Read all reviews</button>
           </div>
           <div id="reviews-${s.id}" style="margin-top:12px"></div>
         </div>`
           )
           .join('') || '<div class="empty">Submit evidence to receive review.</div>'
       }
     </div>`;
}

async function studentMentor() {
  const r = await API.get('/api/mentorship/experts');
  state.experts = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('A private room with experience.', 'Ask a senior expert how to sharpen your skills, story or evidence.') +
    `<div class="grid">
       <div class="card span-5">
         <h2>Senior experts</h2>
         <div class="list">
           ${
             state.experts
               .map(
                 (e) => `
             <button class="list-item" style="text-align:left" onclick="openMentor('${e.id}')">
               <div class="row">
                 <div class="avatar">${initials(e.name)}</div>
                 <div style="flex:1">
                   <div class="candidate-name">${esc(e.name)}</div>
                   <div class="tiny">${esc(e.headline || 'Senior expert')}</div>
                 </div>
                 <span class="tag accent">Private</span>
               </div>
             </button>`
               )
               .join('') || '<div class="empty">No experts available.</div>'
           }
         </div>
       </div>
       <div class="card span-7"><div id="mentor-pane" class="empty">Choose an expert. Your chat is private.</div></div>
     </div>`;
}

async function studentAssignments() {
  const r = await API.get('/api/assessments');
  const assignments = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('Assignments from recruiters & your institution.', 'Timed evidence tasks sent directly to you or open to everyone.') +
    `<div class="list">
       ${
         assignments
           .map(
             (a) => `
         <div class="card">
           <div class="row">
             <div>
               <h2>${esc(a.title)}</h2>
               <div class="tiny">${a.duration_minutes} min · status: ${esc(a.status)}</div>
               <p>${esc(a.description || '')}</p>
             </div>
             <button class="btn btn-primary" onclick="startAssignment('${a.id}')">Start →</button>
           </div>
           <div id="assignment-${a.id}" style="margin-top:12px"></div>
         </div>`
           )
           .join('') || '<div class="empty">No assignments yet. Recruiters and your institution can send you timed tasks here.</div>'
       }
     </div>`;
}

window.startAssignment = async (id) => {
  const r = await API.send('/api/assessments/' + id + '/start', 'POST', {});
  if (!r.ok) {
    alert(r.data.error || 'Could not start assignment');
    return;
  }
  const attempt = r.data;
  const el = document.getElementById('assignment-' + id);
  if (!el) return;
  el.innerHTML = `
    <div class="notice">${attempt.resumed ? attempt.note : 'Attempt started. Write your answer below, then submit — this is timed and monitored for basic integrity signals.'}</div>
    <form id="attempt-form-${id}" style="margin-top:10px">
      <label>Your answer
        <textarea name="answer_text" style="min-height:140px" placeholder="Write your response..." required></textarea>
      </label>
      <button class="btn btn-primary">Submit assignment →</button>
    </form>
    <div id="attempt-result-${id}" style="margin-top:10px"></div>`;

  document.getElementById(`attempt-form-${id}`).onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    const sr = await API.send(`/api/assessments/attempts/${attempt.attempt_id}/submit`, 'POST', body);
    const resEl = document.getElementById(`attempt-result-${id}`);
    if (sr.ok && resEl) {
      resEl.innerHTML = `<div class="notice">Submitted. Integrity score: ${sr.data.integrity_score}. A human reviewer will follow up with a score.</div>`;
    } else if (resEl) {
      resEl.innerHTML = `<div class="notice danger">${esc(sr.data.error || 'Submission failed')}</div>`;
    }
  };
};

async function studentInterviews() {
  const r = await API.get('/api/dashboard/student');
  const subs = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('AI interviews on your own work.', 'A structured follow-up on each submission — your answers become part of the evidence trail.') +
    `<div class="list">
       ${
         subs
           .map(
             (s) => `
         <div class="card">
           <div class="row">
             <div>
               <b>Submission ${esc(s.id.slice(0, 8))}</b>
               <div class="tiny">Proof score ${s.scores.proof_score}</div>
             </div>
             <button class="btn btn-primary" onclick="openInterview('${s.id}')">Open interview →</button>
           </div>
           <div id="interview-${s.id}" style="margin-top:12px"></div>
         </div>`
           )
           .join('') || '<div class="empty">Submit evidence first — interviews are tied to a specific submission.</div>'
       }
     </div>`;
}

window.openInterview = async (submissionId) => {
  const el = document.getElementById('interview-' + submissionId);
  if (!el) return;
  const existing = await API.get('/api/interview/for-submission/' + submissionId);
  let session = existing.data && existing.data.exists ? existing.data : null;
  if (!session) {
    const started = await API.send('/api/interview/' + submissionId + '/start', 'POST', {});
    if (!started.ok) {
      el.innerHTML = `<div class="notice danger">${esc(started.data.error || 'Could not start interview')}</div>`;
      return;
    }
    session = started.data;
  }
  renderInterviewSession(submissionId, session);
};

function renderInterviewSession(submissionId, session) {
  const el = document.getElementById('interview-' + submissionId);
  if (!el) return;
  const done = session.status === 'awaiting_human_review' || session.status === 'completed';
  el.innerHTML = `
    <div class="chat" style="height:280px">
      <div id="interview-log-${submissionId}" class="chat-log">
        ${session.transcript
          .map((t) => `<div class="bubble ${t.role === 'candidate' ? 'me' : 'them'}">${esc(t.content)}</div>`)
          .join('')}
      </div>
      ${
        done
          ? '<div class="notice">Interview complete — awaiting human review.</div>'
          : `<div class="chat-form">
               <input id="interview-input-${submissionId}" placeholder="Type your answer...">
               <button class="btn btn-primary" onclick="respondInterview('${submissionId}','${session.id}')">Send</button>
             </div>`
      }
    </div>`;
  const log = document.getElementById('interview-log-' + submissionId);
  if (log) log.scrollTop = 999999;
}

window.respondInterview = async (submissionId, sessionId) => {
  const input = document.getElementById('interview-input-' + submissionId);
  if (!input || !input.value.trim()) return;
  const r = await API.send('/api/interview/' + sessionId + '/respond', 'POST', { message: input.value });
  input.value = '';
  if (r.ok) renderInterviewSession(submissionId, r.data);
};

async function studentRanking() {
  const [lbRes, subsRes] = await Promise.all([
    API.get('/api/dashboard/leaderboard'),
    API.get('/api/dashboard/student'),
  ]);
  const rows = Array.isArray(lbRes.data) ? lbRes.data : [];
  const subs = Array.isArray(subsRes.data) ? subsRes.data : [];
  const myRow = rows.find((row) => row.student_id === ME.id);
  const best = subs.slice().sort((a, b) => b.scores.proof_score - a.scores.proof_score)[0];
  const top10 = rows.slice(0, 10);

  document.getElementById('view').innerHTML =
    pageHeader('Where you stand.', 'Ranked by proof score across every student on the platform.') +
    `<div class="grid">
       <div class="card span-4">
         <div class="tiny">YOUR RANK</div>
         <div class="metric">${myRow ? '#' + myRow.rank : '—'}<small> of ${rows.length}</small></div>
       </div>
       <div class="card span-4">
         <div class="tiny">YOUR PROOF SCORE</div>
         <div class="metric">${myRow ? myRow.best_proof_score : 0}</div>
       </div>
       <div class="card span-4">
         <div class="tiny">EVIDENCE ITEMS</div>
         <div class="metric">${myRow ? myRow.projects : 0}</div>
       </div>

       <div class="card span-7">
         <h2>Top 10 on the platform</h2>
         <div class="tiny" style="margin-bottom:10px">Proof score by student. Your bar is highlighted.</div>
         <div style="height:280px"><canvas id="chart-leaderboard"></canvas></div>
       </div>
       <div class="card span-5">
         <h2>How the proof score is built</h2>
         <div class="tiny" style="margin-bottom:10px">Weighting inside the Base score — see docs/architecture.md for the full formula.</div>
         <div style="height:280px"><canvas id="chart-weights"></canvas></div>
       </div>

       ${
         best
           ? `<div class="card span-12">
         <h2>Your best submission — score breakdown</h2>
         <div class="tiny" style="margin-bottom:10px">Each factor behind your top proof score of ${best.scores.proof_score}.</div>
         <div style="height:260px"><canvas id="chart-breakdown"></canvas></div>
       </div>`
           : ''
       }

       <div class="card span-12">
         <h2>Leaderboard</h2>
         <div class="list">
           ${
             rows
               .map(
                 (row) => `
             <div class="list-item ${row.student_id === ME.id ? 'active' : ''}">
               <div class="row">
                 <div class="row" style="justify-content:flex-start">
                   <div class="avatar">#${row.rank}</div>
                   <div>
                     <b>${esc(row.name)}${row.student_id === ME.id ? ' (you)' : ''}</b>
                     <div class="tiny">${esc(row.track)} · ${row.projects} evidence items</div>
                   </div>
                 </div>
                 <span class="tag accent">${row.best_proof_score} proof</span>
               </div>
             </div>`
               )
               .join('') || '<div class="empty">No students yet.</div>'
           }
         </div>
       </div>
     </div>`;

  renderChart('chart-leaderboard', {
    type: 'bar',
    data: {
      labels: top10.map((r) => (r.student_id === ME.id ? r.name + ' (you)' : r.name)),
      datasets: [
        {
          label: 'Proof score',
          data: top10.map((r) => r.best_proof_score),
          backgroundColor: top10.map((r) => (r.student_id === ME.id ? '#c7f36b' : '#6be7ff55')),
          borderRadius: 6,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true }, x: { ticks: { autoSkip: false } } },
    },
  });

  renderChart('chart-weights', {
    type: 'pie',
    data: {
      labels: ['Technical 35%', 'Architecture 20%', 'Review 20%', 'Integrity 15%', 'Explanation 10%'],
      datasets: [{ data: [35, 20, 20, 15, 10], backgroundColor: CHART_COLORS }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } } },
  });

  if (best) {
    renderChart('chart-breakdown', {
      type: 'bar',
      data: {
        labels: ['Technical', 'Architecture', 'Review', 'Integrity', 'Explanation'],
        datasets: [
          {
            label: 'Score (0-100)',
            data: [
              best.scores.technical,
              best.scores.architecture,
              best.scores.review,
              best.scores.integrity,
              best.scores.explanation,
            ],
            backgroundColor: CHART_COLORS,
            borderRadius: 6,
          },
        ],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, max: 100 } },
      },
    });
  }
}

// ============================================================
// EXPERT
// ============================================================
async function expertTab() {
  if (state.tab === 'queue') return expertQueue();
  if (state.tab === 'mentor') return expertMentorInbox();
}

async function expertQueue() {
  const r = await API.get('/api/recruiter/candidates');
  const candidates = (r.data && r.data.candidates) || [];
  const items = candidates.flatMap((x) =>
    (x.evidence || []).map((e) => ({ ...e, candidate: x.candidate }))
  );

  document.getElementById('view').innerHTML =
    pageHeader('Review what people actually made.', 'Your review becomes part of their visible evidence.') +
    `<div class="card">
       <div class="notice">Review fairly: judge the evidence relevant to the selected track. A non-technical research brief should not be penalized for lacking a GitHub repository.</div>
       <div class="list" style="margin-top:16px">
         ${
           items
             .map(
               (x) => `
           <div class="list-item">
             <div class="row">
               <div>
                 <div class="candidate-name">${esc(x.candidate.name)}</div>
                 <div class="tiny">${esc(x.project)} · ${esc(x.track)}</div>
               </div>
               <button class="btn btn-primary" onclick="reviewEvidence('${x.submission_id}','${esc(x.candidate.name)}','${esc(x.project)}')">Review →</button>
             </div>
             <div style="margin-top:9px">
               ${(x.candidate.skills || []).slice(0, 5).map((s) => `<span class="tag">${esc(s)}</span>`).join('')}
               <span class="tag accent">${x.proof_score} proof</span>
             </div>
           </div>`
             )
             .join('') || '<div class="empty">No evidence waiting.</div>'
         }
       </div>
     </div>`;
}

async function expertMentorInbox() {
  const r = await API.get('/api/mentorship/threads');
  const threads = Array.isArray(r.data) ? r.data : [];
  const groups = {};
  threads.forEach((m) => (groups[m.student_id] ??= []).push(m));

  document.getElementById('view').innerHTML =
    pageHeader('Mentor inbox.', 'Private conversations stay between you and the student.') +
    `<div class="list">
       ${
         Object.entries(groups)
           .map(([sid, msgs]) => {
             const last = msgs[msgs.length - 1];
             return `
             <button class="list-item" style="text-align:left" onclick="expertThread('${sid}')">
               <div class="row">
                 <div>
                   <b>Student thread</b>
                   <div class="tiny">${esc(last.message)}</div>
                 </div>
                 <span class="tag accent">${msgs.length} messages</span>
               </div>
             </button>`;
           })
           .join('') || '<div class="empty">No private conversations yet.</div>'
       }
     </div>`;
}

// ============================================================
// RECRUITER
// ============================================================
async function recruiterTab() {
  if (state.tab === 'candidates') return recruiterCandidates();
  if (state.tab === 'ranking') return recruiterRanking();
  if (state.tab === 'assignments') return recruiterAssignments();
  if (state.tab === 'insights') return recruiterInsights();
  if (state.tab === 'opportunities') return recruiterOpportunities();
  if (state.tab === 'ai') return recruiterAI();
}

async function recruiterCandidates() {
  const track = document.getElementById('track-filter')?.value || '';
  const skill = document.getElementById('skill-filter')?.value || '';
  const params = new URLSearchParams();
  if (track) params.set('track', track);
  if (skill) params.set('skill', skill);

  const r = await API.get('/api/recruiter/candidates?' + params.toString());
  const candidates = (r.data && r.data.candidates) || [];

  document.getElementById('view').innerHTML =
    pageHeader('Candidate evidence room.', 'Every fresher stays discoverable. Inspect context before forming a view.') +
    `<div class="card">
       <div class="filters">
         <input id="skill-filter" placeholder="Filter by skill" value="${esc(skill)}">
         <select id="track-filter">
           <option value="">All tracks</option>
           <option value="technical" ${track === 'technical' ? 'selected' : ''}>Technical</option>
           <option value="hybrid" ${track === 'hybrid' ? 'selected' : ''}>Hybrid</option>
           <option value="non-technical" ${track === 'non-technical' ? 'selected' : ''}>Non-technical</option>
         </select>
         <button class="btn btn-primary" onclick="recruiterCandidates()">Apply</button>
       </div>
       <div class="table-wrap">
         <table class="evidence-table">
           <thead>
             <tr>
               <th>Student</th><th>Track</th><th>Resume</th><th>GitHub</th>
               <th>Projects / proof</th><th>Signals</th><th>AI notes</th>
             </tr>
           </thead>
           <tbody>
             ${
               candidates
                 .map((c) => {
                   const p = c.candidate;
                   return `
                 <tr>
                   <td>
                     <b>${esc(p.name)}</b>
                     <div class="tiny">${esc(p.headline || 'Fresher')}</div>
                     <div>${(p.skills || []).slice(0, 3).map((s) => `<span class="tag">${esc(s)}</span>`).join('')}</div>
                   </td>
                   <td><span class="tag accent">${esc(p.track)}</span></td>
                   <td>${p.resume_url ? `<a class="link" href="${esc(p.resume_url)}" target="_blank">Resume ↗</a>` : '—'}</td>
                   <td>${p.github_profile_url ? `<a class="link" href="${esc(p.github_profile_url)}" target="_blank">Profile ↗</a>` : '—'}</td>
                   <td>
                     ${
                       (c.evidence || []).length
                         ? c.evidence
                             .map(
                               (e) => `
                       <div style="margin-bottom:8px">
                         <b>${esc(e.project)}</b>
                         <div class="tiny">${e.proof_score} proof · ${e.build_passed ? 'evidence verified' : 'needs review'}</div>
                         ${e.github_url ? `<a class="link" href="${esc(e.github_url)}" target="_blank">repository</a>` : ''}
                       </div>`
                             )
                             .join('')
                         : '<span class="muted">No project yet — still discoverable through profile.</span>'
                     }
                   </td>
                   <td>
                     ${p.verified_by_institution ? '<span class="status good">INSTITUTION VERIFIED</span>' : '<span class="status warn">NOT VERIFIED</span>'}
                     <br><span class="tiny">${c.summary.projects} evidence items</span>
                   </td>
                   <td>
                     <button class="btn btn-ghost" onclick="candidateAI('${p.id}')">Analyse</button>
                     <button class="btn btn-primary" style="margin-top:6px" onclick="inviteCandidate('${p.id}', '${esc(p.name).replace(/'/g, "\\'")}')">Invite ✉</button>
                   </td>
                 </tr>`;
                 })
                 .join('') || '<tr><td colspan="7"><div class="empty">No candidates match those filters.</div></td></tr>'
             }
           </tbody>
         </table>
       </div>
     </div>`;
}

async function recruiterInsights() {
  const r = await API.get('/api/recruiter/candidates');
  const candidates = (r.data && r.data.candidates) || [];
  const tracks = {};
  const skillCounts = {};
  const bands = { '0-25': 0, '25-50': 0, '50-75': 0, '75-100': 0 };
  candidates.forEach((c) => {
    const t = c.candidate.track || 'unknown';
    tracks[t] = (tracks[t] || 0) + 1;
    (c.candidate.skills || []).forEach((s) => {
      skillCounts[s] = (skillCounts[s] || 0) + 1;
    });
    const score = c.summary.best_proof_score || 0;
    if (score < 25) bands['0-25']++;
    else if (score < 50) bands['25-50']++;
    else if (score < 75) bands['50-75']++;
    else bands['75-100']++;
  });
  const topSkills = Object.entries(skillCounts).sort((a, b) => b[1] - a[1]).slice(0, 6);

  document.getElementById('view').innerHTML =
    pageHeader('Talent without tunnel vision.', 'A snapshot of the candidate pool across different kinds of evidence.') +
    `<div class="grid">
       ${
         Object.entries(tracks)
           .map(
             ([k, v]) => `
         <div class="card span-4">
           <div class="tiny">${esc(k.toUpperCase())}</div>
           <div class="metric">${v}<small> candidates</small></div>
           <p>Discoverability does not depend on having a technical repository.</p>
         </div>`
           )
           .join('') || '<div class="empty">No candidate data yet.</div>'
       }

       <div class="card span-4">
         <h2>Pool by track</h2>
         <div style="height:230px"><canvas id="chart-tracks"></canvas></div>
       </div>
       <div class="card span-4">
         <h2>Pool by proof score band</h2>
         <div style="height:230px"><canvas id="chart-bands"></canvas></div>
       </div>
       <div class="card span-4">
         <h2>Most common skills</h2>
         <div style="height:230px"><canvas id="chart-skills"></canvas></div>
       </div>

       <div class="card span-12">
         <h2>Recruiting principle</h2>
         <p>ProofStack exposes scores as one signal among many. Recruiters can inspect the resume, profile, project evidence, human reviews, institution verification and AI notes before making their own decision.</p>
       </div>
     </div>`;

  renderChart('chart-tracks', {
    type: 'pie',
    data: {
      labels: Object.keys(tracks),
      datasets: [{ data: Object.values(tracks), backgroundColor: CHART_COLORS }],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom', labels: { boxWidth: 12 } } } },
  });

  renderChart('chart-bands', {
    type: 'bar',
    data: {
      labels: Object.keys(bands),
      datasets: [{ label: 'Candidates', data: Object.values(bands), backgroundColor: '#6be7ff', borderRadius: 6 }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });

  renderChart('chart-skills', {
    type: 'bar',
    data: {
      labels: topSkills.map(([k]) => k),
      datasets: [{ label: 'Candidates', data: topSkills.map(([, v]) => v), backgroundColor: '#ffb86b', borderRadius: 6 }],
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

async function recruiterAI() {
  document.getElementById('view').innerHTML =
    pageHeader('AI candidate analyst.', 'AI summarizes evidence; humans remain responsible for recruiting decisions.') +
    `<div class="card">
       <div class="notice">AI output can be incomplete or wrong. Treat it as a reading aid, not a hiring verdict.</div>
       <div class="chat" style="height:420px">
         <div id="ai-log" class="chat-log">
           <div class="bubble them">Ask me to explain a candidate's evidence, identify missing proof, or suggest fair follow-up questions.</div>
         </div>
         <div class="chat-form">
           <input id="ai-input" placeholder="Ask about evidence or interview questions">
           <button class="btn btn-primary" onclick="askAI()">→</button>
         </div>
       </div>
     </div>`;
}

async function recruiterRanking() {
  const r = await API.get('/api/dashboard/leaderboard');
  const rows = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('Talent ranking.', 'Every student ranked by proof score — one signal among several, not a verdict.') +
    `<div class="card">
       <div class="list">
         ${
           rows
             .map(
               (row) => `
           <div class="list-item">
             <div class="row">
               <div class="row" style="justify-content:flex-start">
                 <div class="avatar">#${row.rank}</div>
                 <div>
                   <b>${esc(row.name)}</b>
                   <div class="tiny">${esc(row.headline || row.track)} · ${row.projects} evidence items</div>
                 </div>
               </div>
               <div>
                 ${row.verified_by_institution ? '<span class="status good">VERIFIED</span>' : '<span class="status warn">NOT VERIFIED</span>'}
                 <span class="tag accent">${row.best_proof_score} proof</span>
               </div>
             </div>
           </div>`
             )
             .join('') || '<div class="empty">No candidates yet.</div>'
         }
       </div>
     </div>`;
}

async function recruiterAssignments() {
  const r = await API.get('/api/assessments');
  const assignments = Array.isArray(r.data) ? r.data : [];
  document.getElementById('view').innerHTML =
    pageHeader('Send timed assignments.', 'Create an evidence task and see who has completed it, with integrity signals.') +
    `<div class="grid">
       <div class="card span-5">
         <h2>New assignment</h2>
         <form id="new-assignment-form">
           <label>Title<input name="title" required placeholder="e.g. System design walkthrough"></label>
           <label>Description<textarea name="description" placeholder="What should the candidate produce?"></textarea></label>
           <label>Duration (minutes)<input name="duration_minutes" type="number" value="45" min="5"></label>
           <button class="btn btn-primary">Create assignment →</button>
         </form>
       </div>
       <div class="card span-7">
         <h2>Your assignments</h2>
         <div class="list">
           ${
             assignments
               .map(
                 (a) => `
             <button class="list-item" style="text-align:left" onclick="viewAssignmentAttempts('${a.id}','${esc(a.title)}')">
               <div class="row">
                 <div>
                   <b>${esc(a.title)}</b>
                   <div class="tiny">${a.duration_minutes} min · ${esc(a.status)}</div>
                 </div>
                 <span class="tag accent">View attempts →</span>
               </div>
             </button>`
               )
               .join('') || '<div class="empty">No assignments created yet.</div>'
           }
         </div>
       </div>
     </div>`;

  document.getElementById('new-assignment-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    body.duration_minutes = Number(body.duration_minutes) || 45;
    const r2 = await API.send('/api/assessments', 'POST', body);
    if (r2.ok) {
      alert('Assignment created.');
      recruiterAssignments();
    } else {
      alert(r2.data.error || 'Could not create assignment');
    }
  };
}

window.viewAssignmentAttempts = async (id, title) => {
  const r = await API.get('/api/assessments/' + id + '/attempts');
  const attempts = Array.isArray(r.data) ? r.data : [];
  openModal(`
    <div class="row">
      <h2>${esc(title)} — attempts</h2>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <div class="list" style="margin-top:14px">
      ${
        attempts
          .map(
            (a) => `
        <div class="review-box">
          <div class="row">
            <b>${esc(a.student_name)}</b>
            <span class="tag accent">${a.status}</span>
          </div>
          <div class="tiny">Score: ${a.score ?? '—'} · Integrity: ${a.integrity_score}</div>
        </div>`
          )
          .join('') || '<div class="empty">No attempts yet.</div>'
      }
    </div>`);
};

// ============================================================
// INSTITUTION
// ============================================================
async function institutionTab() {
  const r = await API.get('/api/institution/students');
  const students = Array.isArray(r.data) ? r.data : [];

  if (state.tab === 'students') {
    document.getElementById('view').innerHTML =
      pageHeader('Campus evidence registry.', 'Verify students and see whether their employability evidence is taking shape.') +
      `<div class="card">
         <div class="row">
           <div>
             <h2>${students.length} students</h2>
             <p>Verification is a trust signal, not a quality verdict.</p>
           </div>
           <button class="btn btn-primary" onclick="verifyAll()">Verify all →</button>
         </div>
         <div class="list" style="margin-top:18px">
           ${
             students
               .map(
                 (s) => `
             <div class="list-item">
               <div class="row">
                 <div class="row" style="justify-content:flex-start">
                   <div class="avatar">${initials(s.name)}</div>
                   <div>
                     <b>${esc(s.name)}</b>
                     <div class="tiny">${esc(s.track)} · ${(s.skills || []).slice(0, 4).join(' · ')}</div>
                   </div>
                 </div>
                 <div>
                   ${
                     s.verified_by_institution
                       ? '<span class="status good">VERIFIED</span>'
                       : `<button class="btn btn-ghost" onclick="verifyOne('${s.id}')">Verify</button>`
                   }
                 </div>
               </div>
             </div>`
               )
               .join('') || '<div class="empty">No students onboarded.</div>'
           }
         </div>
       </div>`;
  } else {
    document.getElementById('view').innerHTML =
      pageHeader('Institution control room.', 'Help students become legible to employers without reducing them to one number.') +
      `<div class="grid">
         <div class="card span-4">
           <div class="tiny">VERIFIED</div>
           <div class="metric">${students.filter((s) => s.verified_by_institution).length}<small> / ${students.length}</small></div>
         </div>
         <div class="card span-4">
           <div class="tiny">CALIBRATED</div>
           <div class="metric">${students.filter((s) => s.is_calibrated).length}<small> students</small></div>
         </div>
         <div class="card span-4">
           <div class="tiny">NON-TECH TRACK</div>
           <div class="metric">${students.filter((s) => s.track === 'non-technical').length}<small> students</small></div>
         </div>
         <div class="card span-12">
           <h2>What the institution layer proves</h2>
           <p>Identity and campus affiliation can be verified here. The candidate's actual skills and work remain visible separately, so institutional verification is not mistaken for an endorsement of ability.</p>
         </div>
       </div>`;
  }
}

// ============================================================
// GLOBAL HANDLERS (attached to window so inline onclick works)
// ============================================================
window.showSubmission = async (id) => {
  const r = await API.get('/api/submissions/' + id);
  const d = r.data || {};
  openModal(`
    <div class="row">
      <h2>Evidence file</h2>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <div class="notice">The recruiter sees the same evidence trail you see. No hidden candidate-only score.</div>
    <div class="divider"></div>
    <p><b>GitHub:</b> ${d.github_url ? `<a class="link" href="${esc(d.github_url)}" target="_blank">open repository</a>` : 'Not provided'}</p>
    <p><b>Explanation:</b><br>${esc(d.explanation || '')}</p>
    <p><b>Architecture:</b><br>${esc(d.architecture_doc || '')}</p>
    <p><b>Decisions:</b><br>${esc(d.decisions || '')}</p>
    <p><b>AI analysis:</b> ${esc(d.ai_analysis?.summary || 'Not available')}</p>
  `);
};

window.pickChallenge = (id) => {
  const challenges = state.challenges || [];

  // Highlight the matching card in the list, if one was clicked.
  document.querySelectorAll('[data-challenge]').forEach((b) => {
    b.classList.toggle('active', b.dataset.challenge === id);
  });

  const formEl = document.getElementById('submission-form');
  if (!formEl) return;

  formEl.innerHTML = `
    <h2>Submit evidence</h2>
    <form id="submit-evidence">
      <label>Challenge
        <select name="challenge_id" id="challenge-select">
          ${
            challenges.length
              ? challenges
                  .map((c) => `<option value="${c.id}" ${c.id === id ? 'selected' : ''}>${esc(c.title)}</option>`)
                  .join('')
              : '<option value="">No challenges available — ask an admin to add one</option>'
          }
        </select>
      </label>
      <label>Repository URL<input name="github_url" placeholder="Optional for non-technical work"></label>
      <label>Demo / portfolio URL<input name="demo_url" placeholder="https://..."></label>
      <label>Architecture / method<textarea name="architecture_doc" placeholder="How did you approach the problem?"></textarea></label>
      <label>Decisions &amp; trade-offs<textarea name="decisions" placeholder="What did you choose, and why?"></textarea></label>
      <label>Explanation / reflection<textarea name="explanation" placeholder="What did you learn? What would you improve?"></textarea></label>
      <button class="btn btn-primary">Submit for transparent review →</button>
    </form>`;

  document.getElementById('challenge-select')?.addEventListener('change', (e) => {
    document.querySelectorAll('[data-challenge]').forEach((b) => {
      b.classList.toggle('active', b.dataset.challenge === e.target.value);
    });
  });

  document.getElementById('submit-evidence').onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    if (!body.challenge_id) {
      alert('Pick a challenge first.');
      return;
    }
    const r = await API.send('/api/submissions', 'POST', body);
    if (r.ok) {
      alert('Evidence submitted.');
      state.tab = 'overview';
      document.querySelector('[data-tab="overview"]')?.click();
    } else {
      alert(r.data.error || 'Submission failed');
    }
  };
};

window.loadReviews = async (id) => {
  const r = await API.get('/api/reviews/' + id);
  const reviews = Array.isArray(r.data) ? r.data : [];
  const el = document.getElementById('reviews-' + id);
  if (!el) return;
  el.innerHTML =
    reviews
      .map(
        (x) => `
    <div class="review-box">
      <div class="reviewer">${esc(x.reviewer)} · ${esc(x.reviewer_role)}</div>
      <div class="tiny">Technical ${x.technical}/5 · Architecture ${x.architecture}/5 · Debugging ${x.debugging}/5 · Explanation ${x.explanation}/5</div>
      <blockquote>${esc(x.comments)}</blockquote>
    </div>`
      )
      .join('') || '<div class="notice">No review yet. This is not a rejection; it is simply awaiting review.</div>';
};

window.openMentor = async (id) => {
  state.activeExpert = id;
  const r = await API.get('/api/mentorship/thread/' + id);
  const msgs = Array.isArray(r.data) ? r.data : [];
  const expert = state.experts.find((x) => x.id === id);
  document.getElementById('mentor-pane').innerHTML = `
    <div class="chat">
      <div class="row">
        <div>
          <h2>${esc(expert?.name || 'Mentor')}</h2>
          <div class="tiny">PRIVATE THREAD · ONLY YOU AND THE EXPERT</div>
        </div>
      </div>
      <div id="mentor-log" class="chat-log">
        ${
          msgs
            .map((m) => `<div class="bubble ${m.sender_id === ME.id ? 'me' : 'them'}">${esc(m.message)}</div>`)
            .join('') || '<div class="empty">Start the conversation.</div>'
        }
      </div>
      <div class="chat-form">
        <input id="mentor-input" placeholder="Ask for honest guidance...">
        <button class="btn btn-primary" onclick="sendMentor()">Send</button>
      </div>
    </div>`;
  const log = document.getElementById('mentor-log');
  if (log) log.scrollTop = 999999;
};

window.sendMentor = async () => {
  const input = document.getElementById('mentor-input');
  if (!input || !input.value.trim()) return;
  const r = await API.send('/api/mentorship/message', 'POST', {
    other_id: state.activeExpert,
    message: input.value,
  });
  if (r.ok) {
    input.value = '';
    window.openMentor(state.activeExpert);
  }
};

window.askAI = async () => {
  const i = document.getElementById('ai-input');
  const log = document.getElementById('ai-log');
  if (!i || !log || !i.value.trim()) return;
  const q = i.value;
  log.innerHTML += `<div class="bubble me">${esc(q)}</div>`;
  i.value = '';
  const r = await API.send('/api/chatbot', 'POST', { message: q });
  log.innerHTML += `<div class="bubble them">${esc(r.data.reply || 'No response.')}</div>`;
  log.scrollTop = 999999;
};

window.reviewEvidence = async (id, name, project) => {
  openModal(`
    <div class="row">
      <div>
        <div class="eyebrow">HONEST REVIEW</div>
        <h2>${esc(name)}</h2>
        <div class="tiny">${esc(project)}</div>
      </div>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <form id="review-form" style="margin-top:20px">
      <div class="grid">
        ${['technical', 'architecture', 'debugging', 'explanation']
          .map(
            (k) => `
          <label class="span-6">${k}
            <select name="${k}">
              <option value="1">1 — needs work</option>
              <option value="2">2</option>
              <option value="3" selected>3 — developing</option>
              <option value="4">4</option>
              <option value="5">5 — strong</option>
            </select>
          </label>`
          )
          .join('')}
        <label class="span-12">Comments
          <textarea name="comments" required placeholder="Be specific: what is strong, what is missing, and what should they do next?"></textarea>
        </label>
      </div>
      <button class="btn btn-primary">Publish transparent review →</button>
    </form>`);

  document.getElementById('review-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    ['technical', 'architecture', 'debugging', 'explanation'].forEach((k) => {
      body[k] = Number(body[k]);
    });
    const r = await API.send('/api/reviews/' + id, 'POST', body);
    if (r.ok) {
      document.getElementById('modal').classList.remove('open');
      renderTab();
    } else {
      alert(r.data.error || 'Review failed');
    }
  };
};

window.expertThread = async (sid) => {
  const r = await API.get('/api/mentorship/thread/' + sid);
  const msgs = Array.isArray(r.data) ? r.data : [];
  openModal(`
    <div class="row">
      <h2>Private mentor thread</h2>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <div class="chat">
      <div id="expert-chat" class="chat-log">
        ${msgs
          .map((m) => `<div class="bubble ${m.sender_id === ME.id ? 'me' : 'them'}">${esc(m.message)}</div>`)
          .join('')}
      </div>
      <div class="chat-form">
        <input id="expert-msg" placeholder="Write thoughtful guidance...">
        <button class="btn btn-primary" onclick="sendExpert('${sid}')">Send</button>
      </div>
    </div>`);
};

window.sendExpert = async (sid) => {
  const i = document.getElementById('expert-msg');
  if (!i || !i.value.trim()) return;
  const r = await API.send('/api/mentorship/message', 'POST', { other_id: sid, message: i.value });
  if (r.ok) window.expertThread(sid);
};

window.candidateAI = async (id) => {
  const r = await API.get('/api/recruiter/candidates/' + id);
  const d = r.data || {};
  const c = d.candidate || {};
  const evidence = d.evidence || [];
  openModal(`
    <div class="row">
      <h2>${esc(c.name || 'Candidate')}</h2>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <p>${esc(c.bio || 'No bio provided.')}</p>
    <div class="notice">AI is an aid. It does not decide whether this person should be hired.</div>
    ${evidence
      .map(
        (e) => `
      <div class="review-box">
        <b>${esc(e.project)}</b>
        <p>${esc(e.ai_analysis?.summary || 'No AI analysis available.')}</p>
        ${(e.ai_analysis?.strengths || []).map((s) => `<span class="tag">${esc(s)}</span>`).join('')}
      </div>`
      )
      .join('')}`);
};

// ============================================================
// OPPORTUNITIES (recruiter "directly initiate opportunities" + student inbox)
// ============================================================
window.inviteCandidate = async (studentId, studentName) => {
  const r = await API.get('/api/recruiter/opportunities');
  const opps = Array.isArray(r.data) ? r.data : [];
  openModal(`
    <div class="row">
      <h2>Invite ${esc(studentName)}</h2>
      <button onclick="document.getElementById('modal').classList.remove('open')">×</button>
    </div>
    <div class="notice">This creates a real Invitation the candidate sees in their Opportunities tab and can accept or decline.</div>
    <form id="invite-form">
      ${
        opps.length
          ? `<label>Use an existing opportunity
               <select name="opportunity_id" id="invite-opp-select">
                 <option value="">— create a new one instead —</option>
                 ${opps.map((o) => `<option value="${o.id}">${esc(o.title)}</option>`).join('')}
               </select>
             </label>`
          : ''
      }
      <label>New opportunity title<input name="title" placeholder="e.g. Backend Intern — Winter 2026"></label>
      <label>Description<textarea name="description" placeholder="What the role involves"></textarea></label>
      <label>Personal note to candidate<textarea name="message" placeholder="Why you're reaching out"></textarea></label>
      <button class="btn btn-primary">Send invitation →</button>
    </form>
  `);
  document.getElementById('invite-form').onsubmit = async (e) => {
    e.preventDefault();
    const body = Object.fromEntries(new FormData(e.target).entries());
    if (!body.opportunity_id && !body.title.trim()) {
      alert('Pick an existing opportunity or give the new one a title.');
      return;
    }
    if (!body.opportunity_id) delete body.opportunity_id;
    const r = await API.send('/api/recruiter/candidates/' + studentId + '/invite', 'POST', body);
    if (r.ok) {
      alert('Invitation sent.');
      document.getElementById('modal').classList.remove('open');
    } else {
      alert(r.data.error || 'Could not send invitation');
    }
  };
};

async function studentOpportunities() {
  const r = await API.get('/api/student/invitations');
  const invites = Array.isArray(r.data) ? r.data : [];
  const pending = invites.filter((i) => i.status === 'sent');
  const decided = invites.filter((i) => i.status !== 'sent');

  document.getElementById('view').innerHTML =
    pageHeader('Opportunities that found you.', 'Recruiters invite you directly based on your proof, not a job-board application.') +
    `<div class="grid">
       <div class="card span-4">
         <div class="tiny">PENDING</div>
         <div class="metric">${pending.length}</div>
       </div>
       <div class="card span-4">
         <div class="tiny">ACCEPTED</div>
         <div class="metric">${invites.filter((i) => i.status === 'accepted').length}</div>
       </div>
       <div class="card span-4">
         <div class="tiny">TOTAL RECEIVED</div>
         <div class="metric">${invites.length}</div>
       </div>
       <div class="card span-12">
         <h2>Your invitations</h2>
         <div class="list">
           ${
             invites
               .map(
                 (i) => `
             <div class="list-item">
               <div class="row">
                 <div>
                   <b>${esc(i.opportunity_title)}</b>
                   <div class="tiny">From ${esc(i.recruiter_name)} · ${new Date(i.created_at).toLocaleDateString()}</div>
                   ${i.opportunity_description ? `<p class="tiny">${esc(i.opportunity_description)}</p>` : ''}
                   ${i.message ? `<blockquote>${esc(i.message)}</blockquote>` : ''}
                 </div>
                 <div>
                   ${
                     i.status === 'sent'
                       ? `<button class="btn btn-primary" onclick="respondInvite('${i.id}','accepted')">Accept</button>
                          <button class="btn btn-ghost" onclick="respondInvite('${i.id}','declined')">Decline</button>`
                       : `<span class="status ${i.status === 'accepted' ? 'good' : 'warn'}">${i.status.toUpperCase()}</span>`
                   }
                 </div>
               </div>
             </div>`
               )
               .join('') || '<div class="empty">No invitations yet. Keep building — recruiters discover you through your proof score.</div>'
           }
         </div>
       </div>
     </div>`;
}

window.respondInvite = async (id, status) => {
  const r = await API.send('/api/student/invitations/' + id + '/respond', 'POST', { status });
  if (r.ok) studentOpportunities();
  else alert(r.data.error || 'Could not update invitation');
};

async function recruiterOpportunities() {
  const r = await API.get('/api/recruiter/invitations');
  const invites = Array.isArray(r.data) ? r.data : [];
  const byStatus = { sent: 0, accepted: 0, declined: 0 };
  invites.forEach((i) => (byStatus[i.status] = (byStatus[i.status] || 0) + 1));

  document.getElementById('view').innerHTML =
    pageHeader('Opportunities you have sent.', 'Every invitation you send from the candidate room, tracked in one place.') +
    `<div class="grid">
       <div class="card span-4">
         <div class="tiny">AWAITING RESPONSE</div>
         <div class="metric">${byStatus.sent || 0}</div>
       </div>
       <div class="card span-4">
         <div class="tiny">ACCEPTED</div>
         <div class="metric">${byStatus.accepted || 0}</div>
       </div>
       <div class="card span-4">
         <div class="tiny">DECLINED</div>
         <div class="metric">${byStatus.declined || 0}</div>
       </div>
       <div class="card span-12">
         <h2>Sent invitations</h2>
         <div class="list">
           ${
             invites
               .map(
                 (i) => `
             <div class="list-item">
               <div class="row">
                 <div>
                   <b>${esc(i.student_name)}</b> — ${esc(i.opportunity_title)}
                   <div class="tiny">Sent ${new Date(i.created_at).toLocaleDateString()}</div>
                 </div>
                 <span class="status ${i.status === 'accepted' ? 'good' : i.status === 'declined' ? 'bad' : 'warn'}">${i.status.toUpperCase()}</span>
               </div>
             </div>`
               )
               .join('') || '<div class="empty">No invitations sent yet. Invite a candidate from the Candidate room.</div>'
           }
         </div>
       </div>
     </div>`;
}

window.verifyOne = async (id) => {
  const r = await API.send('/api/institution/students/' + id + '/verify');
  if (r.ok) renderTab();
  else alert(r.data.error || 'Could not verify');
};

window.verifyAll = async () => {
  const r = await API.get('/api/institution/students');
  const students = Array.isArray(r.data) ? r.data : [];
  for (const s of students) {
    if (!s.verified_by_institution) {
      await API.send('/api/institution/students/' + s.id + '/verify');
    }
  }
  renderTab();
};

// ---- Boot ----
layout();
renderTab();
