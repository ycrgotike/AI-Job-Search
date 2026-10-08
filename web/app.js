// AI Job Search Dashboard Client Logic

let allJobs = [];
let allTracker = [];
let currentCategory = 'all';
let currentTier = 'all';
let currentDateFilter = 'all';
let currentStatusFilter = 'all';
let currentPortalFilter = 'all';
let serverToday = '';
let searchQuery = '';
let currentSort = 'score_desc';
let currentTrackerFilter = 'all';
let trackerSearchQuery = '';

// Portal Helpers
function normalizePortalKey(portal) {
  if (!portal) return 'other';
  const s = String(portal).toLowerCase().trim();
  if (s.includes('linkedin')) return 'linkedin';
  if (s.includes('stepstone')) return 'stepstone';
  if (s.includes('arbeitsagentur') || s.includes('arbeitsamt') || s.includes('bundesagentur')) return 'arbeitsagentur';
  if (s.includes('freehire') || s.includes('whatjobs') || s.includes('4dayweek')) return 'freehire';
  if (s.includes('xing')) return 'xing';
  return s.replace(/-search$/, '');
}

function formatPortalName(portal) {
  const key = normalizePortalKey(portal);
  switch (key) {
    case 'linkedin': return 'LinkedIn';
    case 'stepstone': return 'StepStone';
    case 'arbeitsagentur': return 'Arbeitsagentur';
    case 'freehire': return 'FreeHire';
    case 'xing': return 'XING';
    default:
      if (!portal) return 'Portal';
      const clean = String(portal).replace(/-search$/, '');
      return clean.charAt(0).toUpperCase() + clean.slice(1);
  }
}

// Elements
const jobsGrid = document.getElementById('jobs-grid');
const trackerTableBody = document.getElementById('tracker-table-body');
const inputSearch = document.getElementById('input-search');
const selectSort = document.getElementById('select-sort');
const categoryPills = document.querySelectorAll('#category-pills .pill');
const tierPills = document.querySelectorAll('#tier-pills .pill');

const tabJobs = document.getElementById('tab-jobs');
const tabTracker = document.getElementById('tab-tracker');
const tabGenerator = document.getElementById('tab-generator');
const viewJobs = document.getElementById('view-jobs');
const viewTracker = document.getElementById('view-tracker');
const viewGenerator = document.getElementById('view-generator');
const btnHeaderGenerator = document.getElementById('btn-header-generator');

// Custom Generator Studio Elements
const customGenCompany = document.getElementById('custom-gen-company');
const customGenTitle = document.getElementById('custom-gen-title');
const customGenLocation = document.getElementById('custom-gen-location');
const customGenContact = document.getElementById('custom-gen-contact');
const customGenUrl = document.getElementById('custom-gen-url');
const customGenDesc = document.getElementById('custom-gen-desc');
const customGenWordCounter = document.getElementById('custom-gen-word-counter');
const customGenErrorBanner = document.getElementById('custom-gen-error-banner');
const btnCustomGenerateSubmit = document.getElementById('btn-custom-generate-submit');

const btnGenAutoDetect = document.getElementById('btn-gen-auto-detect');
const btnGenPasteClipboard = document.getElementById('btn-gen-paste-clipboard');
const btnGenSampleDe = document.getElementById('btn-gen-sample-de');
const btnGenSampleAi = document.getElementById('btn-gen-sample-ai');
const btnGenClear = document.getElementById('btn-gen-clear');

const studioLiveRadar = document.getElementById('studio-live-radar');
const studioProgressCard = document.getElementById('studio-progress-card');
const studioResultsCard = document.getElementById('studio-results-card');

const radarFitScore = document.getElementById('radar-fit-score');
const radarCategoryBadge = document.getElementById('radar-category-badge');
const radarHeadlineBadge = document.getElementById('radar-headline-badge');
const radarGateGerman = document.getElementById('radar-gate-german');
const radarGermanStatus = document.getElementById('radar-german-status');
const radarGateDg = document.getElementById('radar-gate-dg');
const radarKwCount = document.getElementById('radar-kw-count');
const radarKeywordsList = document.getElementById('radar-keywords-list');

const progressStatusText = document.getElementById('progress-status-text');

const resultsCompanyRole = document.getElementById('results-company-role');
const badgeCvPages = document.getElementById('badge-cv-pages');
const badgeClPages = document.getElementById('badge-cl-pages');
const btnPreviewCv = document.getElementById('btn-preview-cv');
const btnDownloadCv = document.getElementById('btn-download-cv');
const btnPreviewCl = document.getElementById('btn-preview-cl');
const btnDownloadCl = document.getElementById('btn-download-cl');
const btnViewInTracker = document.getElementById('btn-view-in-tracker');
const btnTabPdfCv = document.getElementById('btn-tab-pdf-cv');
const btnTabPdfCl = document.getElementById('btn-tab-pdf-cl');
const studioPdfFrame = document.getElementById('studio-pdf-frame');

const summaryCompanyRole = document.getElementById('summary-company-role');
const summaryContact = document.getElementById('summary-contact');
const summaryArchiveDir = document.getElementById('summary-archive-dir');
const summaryMatchedKw = document.getElementById('summary-matched-kw');
const summaryWarningsBox = document.getElementById('summary-warnings-box');

let currentGeneratedCv = '';
let currentGeneratedCl = '';
let jdAnalysisTimeout = null;

const statTotalJobs = document.getElementById('stat-total-jobs');
const statTodayJobs = document.getElementById('stat-today-jobs');
const statCardToday = document.getElementById('stat-card-today');
const statStrongFits = document.getElementById('stat-strong-fits');
const statAppliedCount = document.getElementById('stat-applied-count');
const statAppliedDesc = document.getElementById('stat-applied-desc');
const statAvgScore = document.getElementById('stat-avg-score');

const tabBadgeJobs = document.getElementById('tab-badge-jobs');
const tabBadgeTracker = document.getElementById('tab-badge-tracker');

const countJobsToday = document.getElementById('count-jobs-today');
const countJobsYesterday = document.getElementById('count-jobs-yesterday');
const countJobsUnapplied = document.getElementById('count-jobs-unapplied');
const countJobsApplied = document.getElementById('count-jobs-applied');

const countTrackerAll = document.getElementById('count-tracker-all');
const countTrackerApplied = document.getElementById('count-tracker-applied');
const countTrackerDrafted = document.getElementById('count-tracker-drafted');
const inputTrackerSearch = document.getElementById('input-tracker-search');

// Date Helpers
function getTodayString() {
  if (serverToday) return serverToday;
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function getYesterdayString() {
  if (serverToday) {
    const parts = serverToday.split('-').map(Number);
    if (parts.length === 3) {
      const d = new Date(parts[0], parts[1] - 1, parts[2]);
      d.setDate(d.getDate() - 1);
      return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
    }
  }
  const d = new Date();
  d.setDate(d.getDate() - 1);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function isJobToday(job) {
  if (job.is_today !== undefined) return Boolean(job.is_today);
  const pDate = (job.posted_date || '').slice(0, 10);
  return pDate === getTodayString();
}

function isJobYesterday(job) {
  if (job.is_yesterday !== undefined) return Boolean(job.is_yesterday);
  const pDate = (job.posted_date || '').slice(0, 10);
  return pDate === getYesterdayString();
}

function updateFilterCounts() {
  const todayCount = allJobs.filter(isJobToday).length;
  const yesterdayCount = allJobs.filter(isJobYesterday).length;
  const unappliedCount = allJobs.filter(j => !j.is_applied).length;
  const appliedCount = allJobs.filter(j => j.is_applied).length;

  if (countJobsToday) countJobsToday.textContent = todayCount;
  if (countJobsYesterday) countJobsYesterday.textContent = yesterdayCount;
  if (countJobsUnapplied) countJobsUnapplied.textContent = unappliedCount;
  if (countJobsApplied) countJobsApplied.textContent = appliedCount;
  if (statTodayJobs) {
    statTodayJobs.textContent = todayCount > 0 ? todayCount : yesterdayCount;
    const todayLabel = document.getElementById('stat-today-label');
    if (todayLabel) {
      todayLabel.textContent = todayCount > 0 ? '⚡ Posted Today' : '⚡ Posted Yesterday (Oct 2)';
    }
    const todayDesc = document.getElementById('stat-today-desc');
    if (todayDesc) {
      todayDesc.textContent = todayCount > 0
        ? `${todayCount} freshly posted today · ${yesterdayCount} yesterday`
        : `${yesterdayCount} fresh opportunities from Oct 2 · Click to view`;
    }
  }

  // Portal counts
  const portalCounts = {
    all: allJobs.length,
    linkedin: 0,
    stepstone: 0,
    arbeitsagentur: 0,
    freehire: 0,
    xing: 0
  };
  allJobs.forEach(j => {
    const key = normalizePortalKey(j.portal);
    if (portalCounts[key] !== undefined) {
      portalCounts[key]++;
    }
  });

  const cAll = document.getElementById('count-portal-all');
  const cLi = document.getElementById('count-portal-linkedin');
  const cSs = document.getElementById('count-portal-stepstone');
  const cAa = document.getElementById('count-portal-arbeitsagentur');
  const cFh = document.getElementById('count-portal-freehire');
  const cXi = document.getElementById('count-portal-xing');

  if (cAll) cAll.textContent = portalCounts.all;
  if (cLi) cLi.textContent = portalCounts.linkedin;
  if (cSs) cSs.textContent = portalCounts.stepstone;
  if (cAa) cAa.textContent = portalCounts.arbeitsagentur;
  if (cFh) cFh.textContent = portalCounts.freehire;
  if (cXi) cXi.textContent = portalCounts.xing;
}

// Modals
const pdfModal = document.getElementById('pdf-modal');
const pdfFrame = document.getElementById('pdf-frame');
const btnClosePdf = document.getElementById('btn-close-pdf');
const modalTitle = document.getElementById('modal-title');

const scrapeModal = document.getElementById('scrape-modal');
const btnOpenScrape = document.getElementById('btn-open-scrape');
const btnCloseScrape = document.getElementById('btn-close-scrape');
const formScrape = document.getElementById('form-scrape');
const btnSubmitScrape = document.getElementById('btn-submit-scrape');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
  loadData();
  setupEventListeners();
});

async function loadData() {
  try {
    const [jobsRes, trackerRes, statsRes] = await Promise.all([
      fetch('/api/jobs').then(r => r.json()),
      fetch('/api/tracker').then(r => r.json()),
      fetch('/api/stats').then(r => r.json())
    ]);

    allJobs = jobsRes;
    allTracker = trackerRes;
    
    updateStats(statsRes);
    renderJobs();
    renderTracker();
  } catch (err) {
    showToast('Failed to load dashboard data. Ensure server is running.', 'error');
    console.error(err);
  }
}

function updateStats(stats) {
  if (!stats) return;
  if (stats.today) {
    serverToday = stats.today;
  }
  statTotalJobs.textContent = stats.stored_jobs ?? stats.total_jobs ?? 0;
  if (statTodayJobs) {
    const todayCount = stats.posted_today ?? allJobs.filter(isJobToday).length;
    const yCount = stats.posted_yesterday ?? allJobs.filter(isJobYesterday).length;
    statTodayJobs.textContent = todayCount > 0 ? todayCount : yCount;
    const todayLabel = document.getElementById('stat-today-label');
    if (todayLabel) {
      todayLabel.textContent = todayCount > 0 ? '⚡ Posted Today' : '⚡ Posted Yesterday (Oct 2)';
    }
    const todayDesc = document.getElementById('stat-today-desc');
    if (todayDesc) {
      todayDesc.textContent = todayCount > 0
        ? `${todayCount} freshly posted today · ${yCount} yesterday`
        : `${yCount} fresh opportunities from Oct 2 · Click to view`;
    }
  }
  const jobsDesc = document.getElementById('stat-jobs-desc');
  if (jobsDesc) {
    const hidden = stats.hidden_reasons || {};
    const parts = [
      `${hidden.date ?? 0} outside date window or undated`,
      `${hidden.repost ?? 0} reposted`,
      `${hidden.language ?? 0} language requirement`
    ];
    if (hidden.easy_apply) {
      parts.push(`${hidden.easy_apply} Easy Apply`);
    }
    jobsDesc.textContent = `${stats.total_jobs ?? 0} visible · ${stats.hidden_jobs ?? 0} hidden (${parts.join(', ')}). Tracked applications stay visible.`;
  }
  statStrongFits.textContent = stats.strong_matches || 0;
  statAppliedCount.textContent = stats.applied_count || 0;
  if (statAppliedDesc) {
    const applied = stats.tracker_applied ?? 0;
    const drafted = stats.tracker_drafted ?? 0;
    statAppliedDesc.textContent = `${applied} Applied · ${drafted} Not Yet Applied`;
  }
  statAvgScore.innerHTML = `${stats.avg_score || 0}<span>%</span>`;

  tabBadgeJobs.textContent = stats.total_jobs || 0;
  tabBadgeTracker.textContent = stats.applied_count || 0;
  updateFilterCounts();
}

function filterAndSortJobs() {
  let list = allJobs.filter(job => {
    // Filter out LinkedIn Easy Apply postings
    if (job.easy_apply === true || job.is_easy_apply === true) {
      return false;
    }

    // Portal / Site filter
    if (currentPortalFilter !== 'all') {
      const p = normalizePortalKey(job.portal);
      if (p !== currentPortalFilter) {
        return false;
      }
    }

    // Date Posted filter
    if (currentDateFilter === 'today' && !isJobToday(job)) {
      return false;
    }
    if (currentDateFilter === 'yesterday' && !isJobYesterday(job)) {
      return false;
    }

    // Application status filter
    if (currentStatusFilter === 'unapplied' && job.is_applied) {
      return false;
    }
    if (currentStatusFilter === 'applied' && !job.is_applied) {
      return false;
    }

    // Category match
    if (currentCategory !== 'all' && job.category !== currentCategory) {
      return false;
    }
    // Tier match
    if (currentTier !== 'all' && job.tier !== currentTier) {
      return false;
    }
    // Text search match
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      const matchTitle = (job.clean_title || job.title).toLowerCase().includes(q);
      const matchComp = (job.company || '').toLowerCase().includes(q);
      const matchTags = (job.tags || []).some(t => t.toLowerCase().includes(q));
      if (!matchTitle && !matchComp && !matchTags) return false;
    }
    return true;
  });

  // Sorting: to be applied on top, applied goes down
  list.sort((a, b) => {
    const aApplied = Boolean(a.status && a.status.toLowerCase() === 'applied');
    const bApplied = Boolean(b.status && b.status.toLowerCase() === 'applied');

    if (aApplied !== bApplied) {
      return aApplied ? 1 : -1;
    }

    // In "All Recent (<= 2 Days)", show latest date first (18th above 17th), sorted by match score
    if (currentSort === 'score_desc' || currentSort === 'day_before_first') {
      if (currentDateFilter === 'all') {
        const aDate = (a.posted_date || '').slice(0, 10);
        const bDate = (b.posted_date || '').slice(0, 10);
        if (aDate && !bDate) return -1;
        if (!aDate && bDate) return 1;
        if (aDate && bDate && aDate !== bDate) {
          // Newer date (18th) above older date (17th)
          return bDate.localeCompare(aDate);
        }
      }
      return b.score - a.score;
    }

    if (currentSort === 'score_pure') return b.score - a.score;
    if (currentSort === 'date_desc') return (b.posted_date || '').localeCompare(a.posted_date || '');
    if (currentSort === 'date_asc') return (a.posted_date || '').localeCompare(b.posted_date || '');
    if (currentSort === 'company_asc') return (a.company || '').localeCompare(b.company || '');
    return 0;
  });

  return list;
}

function renderJobs() {
  const filtered = filterAndSortJobs();
  jobsGrid.innerHTML = '';

  if (filtered.length === 0) {
    const isPortalFiltered = currentPortalFilter !== 'all';
    const portalName = isPortalFiltered ? formatPortalName(currentPortalFilter) : '';
    jobsGrid.innerHTML = `
      <div style="grid-column: 1 / -1; text-align: center; padding: 60px 20px; color: var(--text-dim);">
        <p style="font-size: 20px; margin-bottom: 8px;">No matching opportunities found${isPortalFiltered ? ` on ${portalName}` : ''}</p>
        <p style="font-size: 13px; margin-bottom: 16px;">Try relaxing your search query or switching filters.</p>
        ${isPortalFiltered ? `
          <button class="btn-primary" onclick="openScrapeForPortal('${escapeAttr(currentPortalFilter)}')" style="display: inline-flex; margin: 0 auto;">
            ⚡ Scrape ${portalName} Jobs Now
          </button>
        ` : ''}
      </div>
    `;
    return;
  }

  let lastDateGroup = null;

  filtered.forEach(job => {
    // If viewing All Recent, insert a date group divider on date change (for unapplied jobs)
    if (currentDateFilter === 'all' && (currentSort === 'score_desc' || currentSort === 'day_before_first')) {
      const isApplied = Boolean(job.status && job.status.toLowerCase() === 'applied');
      if (!isApplied) {
        const pDate = (job.posted_date || '').slice(0, 10);
        const groupKey = isJobToday(job) ? 'today' : (pDate || 'other');

        if (groupKey !== lastDateGroup) {
          lastDateGroup = groupKey;
          const divider = document.createElement('div');
          const isTodayGroup = isJobToday(job);
          divider.className = `date-group-divider ${isTodayGroup ? 'divider-today' : 'divider-day-before'}`;

          let label = `📅 Opportunities from ${escapeHtml(pDate || 'Recent')}`;
          if (isTodayGroup) {
            label = `⚡ Opportunities Posted Today (${escapeHtml(pDate || 'Today')})`;
          } else if (isJobYesterday(job)) {
            label = `🕒 Opportunities from Yesterday (${escapeHtml(pDate || 'Yesterday')})`;
          } else {
            label = `📅 Opportunities from ${escapeHtml(pDate || 'the Day Before')}`;
          }

          divider.innerHTML = `
            <div class="date-group-title">${label}</div>
            <div class="date-group-count">Ordered by Match Score (High to Low)</div>
          `;
          jobsGrid.appendChild(divider);
        }
      }
    }

    const card = document.createElement('article');
    card.className = 'job-card';

    let tierClass = 'tier-mod';
    if (job.score >= 75) tierClass = 'tier-strong';
    else if (job.score >= 60) tierClass = 'tier-good';

    const tagsHtml = (job.tags || [])
      .map(tag => `<span class="tech-tag">${tag}</span>`)
      .join('');

    const isTracked = Boolean(job.is_applied);
    const isApplied = Boolean(job.status && job.status.toLowerCase() === 'applied');

    let statusHtml = '';
    if (!isTracked) {
      statusHtml = `<span class="status-badge status-new">● UNAPPLIED</span>`;
    } else if (isApplied) {
      statusHtml = `<span class="status-badge status-applied">● APPLIED</span>`;
    } else {
      statusHtml = `<span class="status-badge status-drafted">● DRAFTED</span>`;
    }

    let actionsHtml = `
      <button class="btn-accent btn-generate" id="btn-gen-${escapeAttr(job.key)}" onclick="generateDocuments(this, '${escapeStr(job.key)}', '${escapeStr(job.company)}', '${escapeStr(job.clean_title || job.title)}', '${escapeStr(job.url)}')">
        <svg width="14" height="14" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
        Generate CV &amp; Cover Letter
      </button>
      <button class="btn-applied-toggle-sm not-applied" onclick="toggleAppliedStatus(this, '${escapeStr(job.company)}', '${escapeStr(job.clean_title || job.title)}', 'applied', '${escapeStr(job.url || '')}', '${escapeStr(job.key || '')}')" title="Quickly mark as Applied without generating CV">
        ○ Mark Applied
      </button>
    `;

    if (job.is_applied) {
      actionsHtml = `
        ${job.cv_file ? `<button class="btn-secondary" onclick="viewPdf('${job.cv_file}', '${escapeStr(job.company)} CV')">📄 CV</button>` : ''}
        ${job.cover_letter_file ? `<button class="btn-secondary" onclick="viewPdf('${job.cover_letter_file}', '${escapeStr(job.company)} Letter')">✉️ Letter</button>` : ''}
        <button class="btn-applied-toggle-sm ${isApplied ? 'is-applied' : 'not-applied'}" onclick="toggleAppliedStatus(this, '${escapeStr(job.company)}', '${escapeStr(job.clean_title || job.title)}', '${isApplied ? 'drafted' : 'applied'}', '${escapeStr(job.url || '')}', '${escapeStr(job.key || '')}')" title="${isApplied ? 'Application is marked Applied. Click to toggle Not Applied' : 'Application is Drafted. Click to mark Applied'}">
          ${isApplied ? '✓ Applied' : '○ Not Applied'}
        </button>
        <button class="btn-secondary btn-generate" style="font-size: 11px; padding: 6px 10px;" id="btn-gen-${escapeAttr(job.key)}" onclick="generateDocuments(this, '${escapeStr(job.key)}', '${escapeStr(job.company)}', '${escapeStr(job.clean_title || job.title)}', '${escapeStr(job.url)}')">
          🔄 Regenerate
        </button>
      `;
    }

    const contactHtml = job.contact_person
      ? `<div class="contact-badge"><span>👤 Contact: <strong>${escapeHtml(job.contact_person)}</strong></span></div>`
      : '';

    const isToday = isJobToday(job);
    const isYesterday = isJobYesterday(job);
    let dateBadgeHtml = '';
    if (isToday) {
      dateBadgeHtml = `<span class="badge-today">⚡ TODAY</span>`;
    } else if (isYesterday) {
      dateBadgeHtml = `<span class="badge-yesterday">🕒 YESTERDAY</span>`;
    } else if (job.posted_date) {
      dateBadgeHtml = `<span class="badge-yesterday" style="background: rgba(100, 116, 139, 0.2); border-color: rgba(148, 163, 184, 0.4); color: #cbd5e1;">📅 ${escapeHtml(job.posted_date.slice(5))}</span>`;
    }

    let dateDisplay = escapeHtml(job.posted_date || 'Recently');
    if (isToday) {
      dateDisplay = `<strong>Today</strong> (${escapeHtml(job.posted_date || '')})`;
    } else if (isYesterday) {
      dateDisplay = `<strong>Yesterday</strong> (${escapeHtml(job.posted_date || '')})`;
    }

    card.innerHTML = `
      <div>
        <div class="card-top">
          <div class="company-meta">
            <div class="company-name">
              <span>${escapeHtml(job.company)}</span>
              ${statusHtml}
              ${dateBadgeHtml}
            </div>
            <h2 class="job-title">${escapeHtml(job.clean_title || job.title)}</h2>
          </div>
          <div class="score-badge ${tierClass}">
            <div class="score-num">${job.score}%</div>
            <div class="score-tier">${job.tier}</div>
          </div>
        </div>

        <div class="tags-list" style="margin-top: 14px;">
          ${tagsHtml}
        </div>
        ${contactHtml}
      </div>

      <div class="card-footer">
        <div class="footer-meta">
          <span>📅 ${dateDisplay}</span>
          <span class="portal-badge portal-${normalizePortalKey(job.portal)}" onclick="filterByPortal('${normalizePortalKey(job.portal)}')" title="Filter dashboard to ${formatPortalName(job.portal)} postings">🌐 ${escapeHtml(formatPortalName(job.portal))}</span>
        </div>
        <div class="card-btns">
          <a href="${job.url}" target="_blank" rel="noopener noreferrer" class="btn-secondary" title="View official listing">
            Open Link ↗
          </a>
          ${actionsHtml}
        </div>
      </div>
    `;

    jobsGrid.appendChild(card);
  });
  updateFilterCounts();
}

function renderTracker() {
  trackerTableBody.innerHTML = '';
  if (!allTracker || allTracker.length === 0) {
    trackerTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-dim);">
          No applications recorded yet. Generate your first application from Scraped Opportunities!
        </td>
      </tr>
    `;
    if (countTrackerAll) countTrackerAll.textContent = '0';
    if (countTrackerApplied) countTrackerApplied.textContent = '0';
    if (countTrackerDrafted) countTrackerDrafted.textContent = '0';
    return;
  }

  // Count stats across all tracker entries
  const totalCount = allTracker.length;
  const appliedCount = allTracker.filter(a => (a.status || '').toLowerCase() === 'applied').length;
  const draftedCount = totalCount - appliedCount;

  if (countTrackerAll) countTrackerAll.textContent = totalCount;
  if (countTrackerApplied) countTrackerApplied.textContent = appliedCount;
  if (countTrackerDrafted) countTrackerDrafted.textContent = draftedCount;

  // Filter tracker items
  const filtered = allTracker.filter(app => {
    const isApplied = (app.status || '').toLowerCase() === 'applied';
    if (currentTrackerFilter === 'applied' && !isApplied) return false;
    if (currentTrackerFilter === 'not-applied' && isApplied) return false;

    if (trackerSearchQuery) {
      const q = trackerSearchQuery.toLowerCase();
      const matchComp = (app.company || '').toLowerCase().includes(q);
      const matchRole = (app.role || '').toLowerCase().includes(q);
      const matchContact = (app.contact_person || '').toLowerCase().includes(q);
      if (!matchComp && !matchRole && !matchContact) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    trackerTableBody.innerHTML = `
      <tr>
        <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-dim);">
          No applications match the current filter.
        </td>
      </tr>
    `;
    return;
  }

  filtered.forEach(app => {
    const isApplied = (app.status || '').toLowerCase() === 'applied';
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${app.date || '--'}</td>
      <td style="font-weight: 600; color: #fff;">${escapeHtml(app.company)}</td>
      <td>${escapeHtml(app.role)}</td>
      <td>
        <button class="btn-applied-toggle ${isApplied ? 'is-applied' : 'not-applied'}"
                onclick="toggleAppliedStatus(this, '${escapeStr(app.company)}', '${escapeStr(app.role)}', '${isApplied ? 'drafted' : 'applied'}', '${escapeStr(app.source || '')}')"
                title="${isApplied ? 'Status: Applied. Click to mark as Not Applied (Drafted)' : 'Status: Not Applied. Click to mark as Applied'}">
          <span class="toggle-dot"></span>
          <span class="toggle-text">${isApplied ? '✓ Applied' : '○ Not Applied'}</span>
        </button>
      </td>
      <td style="font-weight: 700; color: var(--accent-green);">${app.fit_rating ? app.fit_rating + '%' : '--'}</td>
      <td>
        <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
          <span>${app.contact_person ? `<strong style="color: #fff;">👤 ${escapeHtml(app.contact_person)}</strong>` : `<span style="color: var(--text-muted);">Hiring Team</span>`}</span>
          <button class="btn-edit-contact" title="Edit Contact Person" onclick="editContactPerson('${escapeStr(app.company)}', '${escapeStr(app.role)}', '${escapeStr(app.contact_person || '')}')">✏️</button>
        </div>
      </td>
      <td>
        <div style="display: flex; gap: 8px;">
          ${app.cv_file ? `<button class="btn-secondary" onclick="viewPdf('${app.cv_file}', '${escapeStr(app.company)} CV')">📄 CV</button>` : ''}
          ${app.cover_letter_file ? `<button class="btn-secondary" onclick="viewPdf('${app.cover_letter_file}', '${escapeStr(app.company)} Cover Letter')">✉️ Cover Letter</button>` : ''}
          ${app.source ? `<a href="${app.source}" target="_blank" class="btn-secondary">🔗 Link</a>` : ''}
        </div>
      </td>
    `;
    trackerTableBody.appendChild(tr);
  });
}

window.toggleAppliedStatus = async function(btn, company, role, targetStatus, url = '', key = '') {
  if (btn) {
    btn.disabled = true;
    btn.classList.add('loading');
  }

  const isMarkingApplied = targetStatus.toLowerCase() === 'applied';
  showToast(`${isMarkingApplied ? '🚀 Marking' : '↩️ Reverting'} ${company} as ${isMarkingApplied ? 'Applied' : 'Not Applied'}...`);

  try {
    const res = await fetch('/api/tracker/update_status', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, role, status: targetStatus, url, key })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`✅ ${company} is now marked as ${isMarkingApplied ? 'Applied' : 'Not Applied'}!`);
      await loadData();
    } else {
      showToast(`❌ Failed to update status: ${data.error || 'Unknown error'}${data.diagnostics_file ? ' — Error report: ' + data.diagnostics_file : ''}`, 'error');
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('loading');
      }
    }
  } catch (err) {
    showToast(`❌ Network error: ${err.message}`, 'error');
    if (btn) {
      btn.disabled = false;
      btn.classList.remove('loading');
    }
  }
};

window.editContactPerson = async function(company, role, current) {
  const newVal = prompt(`Specify contact person for ${company} (${role}):`, current || '');
  if (newVal === null) return;

  try {
    const res = await fetch('/api/tracker/update_contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ company, role, contact_person: newVal.trim() })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`✅ Contact person updated for ${company}!`);
      await loadData();
    } else {
      showToast(`❌ Error updating contact: ${data.error || 'Unknown error'}`);
    }
  } catch (err) {
    showToast(`❌ Network error: ${err.message}`);
  }
};

// Global Actions
window.generateDocuments = async function(btn, jobKey, company, title, url) {
  if (btn.disabled) return;

  const originalHtml = btn.innerHTML;
  btn.disabled = true;
  btn.classList.add('loading');
  btn.innerHTML = `
    <svg class="spinner-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
    </svg>
    Generating…
  `;

  showToast(`⚙️ Generating tailored CV & Cover Letter for ${company}…`);

  try {
    const res = await fetch('/api/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: jobKey, company: company, title: title, url: url })
    });
    const data = await res.json();

    if (data.success) {
      const kwInfo = data.matched_keywords && data.matched_keywords.length > 0
        ? ` (Tailored to: ${data.matched_keywords.slice(0, 3).join(', ')})`
        : '';
      showToast(`Drafts generated for ${company}. CV: ${data.cv_pages}p, Letter: ${data.cl_pages}p. Review before submission.${data.required_attachments?.length ? " Required: " + data.required_attachments.join("; ") : ""}`);
      btn.classList.remove('loading');
      btn.disabled = false;
      btn.innerHTML = `✓ Generated`;
      btn.style.borderColor = 'rgba(16, 185, 129, 0.6)';
      btn.style.color = '#6ee7b7';
      btn.style.background = 'rgba(16, 185, 129, 0.15)';

      // Reload data to reflect new status
      setTimeout(() => loadData(), 800);
    } else {
      showToast(`❌ Generation failed: ${data.error || 'Unknown error'}${data.diagnostics_file ? ' — Error report: ' + data.diagnostics_file : ''}`, 'error');
      btn.classList.remove('loading');
      btn.disabled = false;
      btn.innerHTML = originalHtml;
    }
  } catch (err) {
    showToast(`❌ Network error: ${err.message}`, 'error');
    btn.classList.remove('loading');
    btn.disabled = false;
    btn.innerHTML = originalHtml;
  }
};

window.viewPdf = function(filePath, title) {
  if (!filePath) return;
  modalTitle.textContent = title || 'Document Preview';
  pdfFrame.src = `/${filePath}?v=${Date.now()}`;
  pdfModal.showModal();
};

function setupEventListeners() {
  // Search input
  inputSearch.addEventListener('input', (e) => {
    searchQuery = e.target.value.trim();
    renderJobs();
  });

  // Sort select
  selectSort.addEventListener('change', (e) => {
    currentSort = e.target.value;
    renderJobs();
  });

  // Category pills
  categoryPills.forEach(pill => {
    pill.addEventListener('click', () => {
      categoryPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentCategory = pill.dataset.category;
      renderJobs();
    });
  });

  // Tier pills
  tierPills.forEach(pill => {
    pill.addEventListener('click', () => {
      tierPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentTier = pill.dataset.tier;
      renderJobs();
    });
  });

  // Date Posted pills
  const datePills = document.querySelectorAll('#date-pills .pill');
  datePills.forEach(pill => {
    pill.addEventListener('click', () => {
      datePills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentDateFilter = pill.dataset.date;
      renderJobs();
    });
  });

  // Application Status pills
  const statusPills = document.querySelectorAll('#status-pills .pill');
  statusPills.forEach(pill => {
    pill.addEventListener('click', () => {
      statusPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentStatusFilter = pill.dataset.status;
      renderJobs();
    });
  });

  // Clickable Stat Card: Posted Today / Yesterday
  if (statCardToday) {
    statCardToday.addEventListener('click', () => {
      if (!tabJobs.classList.contains('active')) {
        tabJobs.click();
      }
      const todayCount = allJobs.filter(isJobToday).length;
      const targetDate = todayCount > 0 ? 'today' : 'yesterday';
      datePills.forEach(p => {
        if (p.dataset.date === targetDate) {
          p.classList.add('active');
        } else {
          p.classList.remove('active');
        }
      });
      currentDateFilter = targetDate;
      renderJobs();
      document.querySelector('.controls-panel')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      if (targetDate === 'yesterday') {
        const yCount = allJobs.filter(isJobYesterday).length;
        showToast(`⚡ Filtered to ${yCount} opportunities posted yesterday (Oct 2)!`);
      } else {
        showToast('⚡ Filtered to opportunities posted today!');
      }
    });
  }

  // Tracker filter pills
  const trackerPills = document.querySelectorAll('#tracker-status-pills .pill');
  trackerPills.forEach(pill => {
    pill.addEventListener('click', () => {
      trackerPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentTrackerFilter = pill.dataset.trackerFilter;
      renderTracker();
    });
  });

  // Tracker search input
  if (inputTrackerSearch) {
    inputTrackerSearch.addEventListener('input', (e) => {
      trackerSearchQuery = e.target.value.trim();
      renderTracker();
    });
  }

  // Main View / Tab switching
  function switchMainView(viewName) {
    tabJobs.classList.toggle('active', viewName === 'jobs');
    tabTracker.classList.toggle('active', viewName === 'tracker');
    if (tabGenerator) tabGenerator.classList.toggle('active', viewName === 'generator');

    viewJobs.style.display = viewName === 'jobs' ? 'block' : 'none';
    viewTracker.style.display = viewName === 'tracker' ? 'block' : 'none';
    if (viewGenerator) viewGenerator.style.display = viewName === 'generator' ? 'block' : 'none';

    if (viewName === 'generator') {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      if (customGenDesc && !customGenDesc.value && customGenCompany) {
        customGenCompany.focus();
      }
    }
  }

  tabJobs.addEventListener('click', () => switchMainView('jobs'));
  tabTracker.addEventListener('click', () => switchMainView('tracker'));
  if (tabGenerator) tabGenerator.addEventListener('click', () => switchMainView('generator'));
  if (btnHeaderGenerator) btnHeaderGenerator.addEventListener('click', () => switchMainView('generator'));

  // Real-time Job Description Analysis Scanner
  async function analyzePastedJd(autoFill = false) {
    if (!customGenDesc) return;
    const desc = customGenDesc.value.trim();
    const comp = customGenCompany ? customGenCompany.value.trim() : '';
    const role = customGenTitle ? customGenTitle.value.trim() : '';

    const words = desc ? desc.split(/\s+/).filter(Boolean).length : 0;
    const chars = desc.length;
    if (customGenWordCounter) {
      customGenWordCounter.textContent = `${words} words · ${chars} chars`;
    }

    if (desc.length < 20) {
      if (radarFitScore) radarFitScore.innerHTML = `--<span class="radar-gauge-pct">%</span>`;
      if (radarCategoryBadge) radarCategoryBadge.textContent = 'Role Category: Waiting for input';
      if (radarHeadlineBadge) radarHeadlineBadge.textContent = 'Koblenz, Germany | Data Engineer';
      if (radarKwCount) radarKwCount.textContent = '0 detected';
      if (radarKeywordsList) {
        radarKeywordsList.innerHTML = `<span class="radar-kw-placeholder">Paste a job description to see detected technologies (Azure, Databricks, PySpark, RAG, SQL, etc.)</span>`;
      }
      if (radarGateGerman) {
        radarGateGerman.className = 'radar-gate-card';
        if (radarGermanStatus) radarGermanStatus.textContent = 'German B2 / English C1 compatible (No German C1/C2 required)';
      }
      if (radarGateDg) radarGateDg.style.display = 'none';
      return;
    }

    try {
      const res = await fetch('/api/analyze_jd', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ description: desc, company: comp, title: role })
      });
      const data = await res.json();
      if (!data.success) return;

      if (radarFitScore) {
        radarFitScore.innerHTML = `${data.fit_score}<span class="radar-gauge-pct">%</span>`;
      }
      if (radarCategoryBadge) {
        radarCategoryBadge.textContent = `Role Category: ${data.category}`;
      }
      if (radarHeadlineBadge) {
        radarHeadlineBadge.textContent = `Koblenz, Germany | ${data.headline}`;
      }

      if (radarGateGerman && radarGermanStatus) {
        if (data.german_gate?.requires_c1_c2) {
          radarGateGerman.className = 'radar-gate-card warning';
          radarGermanStatus.textContent = `⚠️ Caution: ${data.german_gate.warning}`;
        } else {
          radarGateGerman.className = 'radar-gate-card success';
          radarGermanStatus.textContent = `✓ German B2 / English C1 compatible (Safe to apply)`;
        }
      }

      if (radarGateDg) {
        if (data.data_governance?.detected) {
          radarGateDg.style.display = 'flex';
          radarGateDg.className = 'radar-gate-card active-highlight';
        } else {
          radarGateDg.style.display = 'none';
        }
      }

      if (radarKeywordsList) {
        const allLabels = data.keywords?.all_labels || [];
        if (allLabels.length > 0) {
          radarKeywordsList.innerHTML = allLabels.map(k => `
            <span class="radar-kw-pill">${escapeHtml(k)}</span>
          `).join('');
          if (radarKwCount) radarKwCount.textContent = `${allLabels.length} detected`;
        } else {
          radarKeywordsList.innerHTML = `<span class="radar-kw-placeholder">No specific tech keywords recognized yet. Mention Python, SQL, Databricks, Spark, RAG, etc.</span>`;
          if (radarKwCount) radarKwCount.textContent = '0 detected';
        }
      }

      if (autoFill) {
        let filledCount = 0;
        if (customGenCompany && !customGenCompany.value && data.detected_company) {
          customGenCompany.value = data.detected_company;
          filledCount++;
        }
        if (customGenTitle && !customGenTitle.value && data.detected_title) {
          customGenTitle.value = data.detected_title;
          filledCount++;
        }
        if (customGenLocation && !customGenLocation.value && data.detected_location) {
          customGenLocation.value = data.detected_location;
          filledCount++;
        }
        if (customGenContact && !customGenContact.value && data.detected_contact_person) {
          customGenContact.value = data.detected_contact_person;
          filledCount++;
        }
        if (filledCount > 0) {
          showToast(`⚡ Auto-filled ${filledCount} field(s) from job description!`);
        } else {
          showToast('✓ Job description analyzed.');
        }
      }
    } catch (err) {
      console.error('JD analysis error:', err);
    }
  }

  // Textarea input listeners for live analysis with debounce
  if (customGenDesc) {
    customGenDesc.addEventListener('input', () => {
      clearTimeout(jdAnalysisTimeout);
      const desc = customGenDesc.value.trim();
      const words = desc ? desc.split(/\s+/).filter(Boolean).length : 0;
      if (customGenWordCounter) {
        customGenWordCounter.textContent = `${words} words · ${desc.length} chars`;
      }
      jdAnalysisTimeout = setTimeout(() => analyzePastedJd(false), 450);
    });
  }

  if (customGenCompany) {
    customGenCompany.addEventListener('input', () => {
      clearTimeout(jdAnalysisTimeout);
      jdAnalysisTimeout = setTimeout(() => analyzePastedJd(false), 600);
    });
  }
  if (customGenTitle) {
    customGenTitle.addEventListener('input', () => {
      clearTimeout(jdAnalysisTimeout);
      jdAnalysisTimeout = setTimeout(() => analyzePastedJd(false), 600);
    });
  }

  // Sample Loaders
  if (btnGenSampleDe) {
    btnGenSampleDe.addEventListener('click', () => {
      if (customGenCompany) customGenCompany.value = 'Celonis SE';
      if (customGenTitle) customGenTitle.value = 'Senior Data Engineer (Azure / Databricks)';
      if (customGenLocation) customGenLocation.value = 'Munich, Germany';
      if (customGenContact) customGenContact.value = 'Julia Weber (Talent Acquisition Lead)';
      if (customGenUrl) customGenUrl.value = 'https://www.celonis.com/careers/data-engineer-10492';
      if (customGenDesc) {
        customGenDesc.value = `About Celonis:
Celonis is the pioneer and global market leader in Process Mining and Process Intelligence.
Location: Munich, Germany | Remote within Germany available.
Contact: Julia Weber is your talent acquisition partner.

Your Responsibilities:
- Design, build and maintain highly scalable enterprise data pipelines using Azure Databricks, Apache Spark and Delta Lake.
- Implement medallion lakehouse architecture (Bronze, Silver, Gold layers) and optimize PySpark workloads.
- Establish automated data quality frameworks, data governance checks, and schema validation.
- Collaborate with platform and DevOps teams to deliver CI/CD pipelines via Docker and GitHub Actions.
- Ensure end-to-end data pipeline reliability and monitoring with sub-30-minute processing latency.

Your Profile:
- Bachelor's or Master's degree in Computer Science, Data Science, or related field.
- 4+ years of hands-on experience in Data Engineering, Python, SQL, and PySpark.
- Proven expertise in cloud data architectures (Azure, Azure Data Factory, Databricks).
- Hands-on experience with Lakehouse, Delta Lake, ETL/ELT pipelines, and data modeling.
- Fluent in English (C1); German B2 is an advantage.`;
      }
      analyzePastedJd(false);
      showToast('🧪 Loaded Azure Data Engineer sample for Celonis SE');
    });
  }

  if (btnGenSampleAi) {
    btnGenSampleAi.addEventListener('click', () => {
      if (customGenCompany) customGenCompany.value = 'Siemens AG';
      if (customGenTitle) customGenTitle.value = 'AI / Machine Learning Engineer (RAG & Agentic Systems)';
      if (customGenLocation) customGenLocation.value = 'Erlangen, Germany';
      if (customGenContact) customGenContact.value = 'Markus Becker (Engineering Manager)';
      if (customGenUrl) customGenUrl.value = 'https://jobs.siemens.com/careers/ai-engineer-88219';
      if (customGenDesc) {
        customGenDesc.value = `About Siemens:
Siemens AG is a leading technology company focused on industry, infrastructure, and mobility.
Location: Erlangen, Germany.
Contact: For questions regarding this role, contact Markus Becker.

Your Tasks:
- Design, build, and deploy production-grade GenAI and LLM applications using RAG architectures and multi-agent frameworks.
- Implement vector databases, retrieval pipelines, semantic caching, and prompt engineering.
- Build automated ML pipelines and data pipelines using Python, PyTorch, and Docker.
- Implement model evaluation, latency benchmarks, and safety guardrails.
- Ensure automated data governance, data quality assurance, and compliance in enterprise AI deployments.

Your Qualifications:
- Master's degree in Computer Science, Machine Learning, or related field.
- 3+ years of experience with Python, LLMs, LangChain, RAG architectures, and agentic workflows.
- Strong knowledge of PyTorch/TensorFlow, REST APIs, and containerized deployment (Docker).
- Fluent English proficiency (C1); German B2 is welcome.`;
      }
      analyzePastedJd(false);
      showToast('🧪 Loaded AI / ML Engineer sample for Siemens AG');
    });
  }

  // Paste from clipboard
  if (btnGenPasteClipboard) {
    btnGenPasteClipboard.addEventListener('click', async () => {
      try {
        const text = await navigator.clipboard.readText();
        if (text && customGenDesc) {
          customGenDesc.value = text;
          analyzePastedJd(true);
          showToast('📋 Pasted job description from clipboard!');
        } else {
          showToast('Clipboard was empty or contained no text.', 'error');
        }
      } catch (err) {
        showToast('Clipboard permission not granted. Please paste directly into the box (Ctrl+V / Cmd+V).', 'error');
      }
    });
  }

  // Clear Studio
  if (btnGenClear) {
    btnGenClear.addEventListener('click', () => {
      if (customGenCompany) customGenCompany.value = '';
      if (customGenTitle) customGenTitle.value = '';
      if (customGenLocation) customGenLocation.value = '';
      if (customGenContact) customGenContact.value = '';
      if (customGenUrl) customGenUrl.value = '';
      if (customGenDesc) customGenDesc.value = '';
      if (customGenErrorBanner) customGenErrorBanner.style.display = 'none';
      if (studioResultsCard) studioResultsCard.style.display = 'none';
      if (studioProgressCard) studioProgressCard.style.display = 'none';
      if (studioLiveRadar) studioLiveRadar.style.display = 'block';
      analyzePastedJd(false);
      showToast('Cleared all studio fields.');
    });
  }

  // Auto-detect button
  if (btnGenAutoDetect) {
    btnGenAutoDetect.addEventListener('click', () => {
      analyzePastedJd(true);
    });
  }

  // Generate Submission Handler
  if (btnCustomGenerateSubmit) {
    btnCustomGenerateSubmit.addEventListener('click', async () => {
      const company = customGenCompany ? customGenCompany.value.trim() : '';
      const title = customGenTitle ? customGenTitle.value.trim() : '';
      const location = customGenLocation ? customGenLocation.value.trim() : '';
      const contact = customGenContact ? customGenContact.value.trim() : '';
      const url = customGenUrl ? customGenUrl.value.trim() : '';
      const desc = customGenDesc ? customGenDesc.value.trim() : '';

      if (!company) {
        if (customGenErrorBanner) {
          customGenErrorBanner.textContent = '⚠️ Please specify Company Name (e.g. "BMW Group", "Celonis", "Siemens").';
          customGenErrorBanner.style.display = 'block';
        }
        customGenCompany?.focus();
        return;
      }
      if (!title) {
        if (customGenErrorBanner) {
          customGenErrorBanner.textContent = '⚠️ Please specify Role Title (e.g. "Senior Data Engineer", "AI Engineer").';
          customGenErrorBanner.style.display = 'block';
        }
        customGenTitle?.focus();
        return;
      }
      if (!desc || desc.length < 25) {
        if (customGenErrorBanner) {
          customGenErrorBanner.textContent = '⚠️ Please paste a substantive job description so Antigravity can analyze requirements and tailor your application.';
          customGenErrorBanner.style.display = 'block';
        }
        customGenDesc?.focus();
        return;
      }

      if (customGenErrorBanner) customGenErrorBanner.style.display = 'none';
      btnCustomGenerateSubmit.disabled = true;

      // Switch right column to Progress Panel
      if (studioLiveRadar) studioLiveRadar.style.display = 'none';
      if (studioResultsCard) studioResultsCard.style.display = 'none';
      if (studioProgressCard) studioProgressCard.style.display = 'flex';

      const steps = [
        { id: 'pstep-1', text: 'Extracting keywords & matching candidate achievements…' },
        { id: 'pstep-2', text: 'Writing tailored 4-line summary & ModernCV sections…' },
        { id: 'pstep-3', text: 'Composing evidence-led XeLaTeX Cover Letter…' },
        { id: 'pstep-4', text: 'Compiling via LuaLaTeX and XeLaTeX engines…' },
        { id: 'pstep-5', text: 'Verifying 2-page CV & 1-page Letter ATS compliance…' }
      ];

      let currentStepIdx = 0;
      const updateStepUi = (idx) => {
        steps.forEach((s, i) => {
          const el = document.getElementById(s.id);
          if (!el) return;
          if (i < idx) {
            el.className = 'progress-step completed';
          } else if (i === idx) {
            el.className = 'progress-step active';
          } else {
            el.className = 'progress-step';
          }
        });
        if (progressStatusText && steps[idx]) {
          progressStatusText.textContent = steps[idx].text;
        }
      };

      updateStepUi(0);
      const stepTimer = setInterval(() => {
        if (currentStepIdx < steps.length - 1) {
          currentStepIdx++;
          updateStepUi(currentStepIdx);
        }
      }, 3500);

      showToast(`⚙️ Tailoring and compiling application for ${company}…`);

      try {
        const res = await fetch('/api/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            company: company,
            title: title,
            location: location,
            contact_person: contact,
            url: url,
            description: desc,
            is_custom: true
          })
        });
        clearInterval(stepTimer);

        const data = await res.json();

        if (data.success) {
          steps.forEach(s => {
            const el = document.getElementById(s.id);
            if (el) el.className = 'progress-step completed';
          });

          currentGeneratedCv = data.cv_file;
          currentGeneratedCl = data.cover_letter_file;

          if (resultsCompanyRole) resultsCompanyRole.textContent = `${data.company} — ${data.role}`;
          if (badgeCvPages) badgeCvPages.textContent = `CV: ${data.cv_pages} Pages ✓`;
          if (badgeClPages) badgeClPages.textContent = `Letter: ${data.cl_pages} Page ✓`;

          if (summaryCompanyRole) summaryCompanyRole.textContent = `${data.company} — ${data.role}`;
          if (summaryContact) summaryContact.textContent = data.contact_person || 'Hiring Team';
          if (summaryArchiveDir) summaryArchiveDir.textContent = data.archive_dir || `documents/applications/${company}_${title}`;
          if (summaryMatchedKw) summaryMatchedKw.textContent = data.matched_keywords?.join(', ') || 'Keywords grounded';

          if (summaryWarningsBox) {
            if (data.tailoring_warnings?.length) {
              summaryWarningsBox.style.display = 'block';
              summaryWarningsBox.textContent = `ℹ️ ${data.tailoring_warnings.join(' · ')}`;
            } else {
              summaryWarningsBox.style.display = 'none';
            }
          }

          if (studioPdfFrame) {
            studioPdfFrame.src = `/${data.cv_file}?v=${Date.now()}`;
          }
          if (btnTabPdfCv) btnTabPdfCv.classList.add('active');
          if (btnTabPdfCl) btnTabPdfCl.classList.remove('active');

          if (btnDownloadCv) {
            btnDownloadCv.href = `/${data.cv_file}?v=${Date.now()}`;
            btnDownloadCv.setAttribute('download', data.cv_file.split('/').pop());
          }
          if (btnDownloadCl) {
            btnDownloadCl.href = `/${data.cover_letter_file}?v=${Date.now()}`;
            btnDownloadCl.setAttribute('download', data.cover_letter_file.split('/').pop());
          }

          if (studioProgressCard) studioProgressCard.style.display = 'none';
          if (studioResultsCard) studioResultsCard.style.display = 'block';
          btnCustomGenerateSubmit.disabled = false;

          showToast(`🎉 Generated 2-page CV & 1-page Cover Letter for ${data.company}!`);
          setTimeout(() => loadData(), 800);
        } else {
          clearInterval(stepTimer);
          if (studioProgressCard) studioProgressCard.style.display = 'none';
          if (studioLiveRadar) studioLiveRadar.style.display = 'block';
          if (customGenErrorBanner) {
            customGenErrorBanner.textContent = `❌ Generation failed: ${data.error || 'Unknown compilation error'}`;
            customGenErrorBanner.style.display = 'block';
          }
          showToast(`❌ Generation failed: ${data.error || 'Unknown error'}${data.diagnostics_file ? ' — Error report: ' + data.diagnostics_file : ''}`, 'error');
          btnCustomGenerateSubmit.disabled = false;
        }
      } catch (err) {
        clearInterval(stepTimer);
        if (studioProgressCard) studioProgressCard.style.display = 'none';
        if (studioLiveRadar) studioLiveRadar.style.display = 'block';
        if (customGenErrorBanner) {
          customGenErrorBanner.textContent = `❌ Network or server error: ${err.message}`;
          customGenErrorBanner.style.display = 'block';
        }
        showToast(`❌ Network error: ${err.message}`, 'error');
        btnCustomGenerateSubmit.disabled = false;
      }
    });
  }

  // Studio PDF Tab toggles
  if (btnTabPdfCv) {
    btnTabPdfCv.addEventListener('click', () => {
      btnTabPdfCv.classList.add('active');
      if (btnTabPdfCl) btnTabPdfCl.classList.remove('active');
      if (currentGeneratedCv && studioPdfFrame) {
        studioPdfFrame.src = `/${currentGeneratedCv}?v=${Date.now()}`;
      }
    });
  }

  if (btnTabPdfCl) {
    btnTabPdfCl.addEventListener('click', () => {
      btnTabPdfCl.classList.add('active');
      if (btnTabPdfCv) btnTabPdfCv.classList.remove('active');
      if (currentGeneratedCl && studioPdfFrame) {
        studioPdfFrame.src = `/${currentGeneratedCl}?v=${Date.now()}`;
      }
    });
  }

  // Results action buttons
  if (btnPreviewCv) {
    btnPreviewCv.addEventListener('click', () => {
      if (currentGeneratedCv) viewPdf(currentGeneratedCv, 'Tailored ModernCV');
    });
  }
  if (btnPreviewCl) {
    btnPreviewCl.addEventListener('click', () => {
      if (currentGeneratedCl) viewPdf(currentGeneratedCl, 'Tailored Cover Letter');
    });
  }
  if (btnViewInTracker) {
    btnViewInTracker.addEventListener('click', () => {
      switchMainView('tracker');
    });
  }

  // PDF Modal
  btnClosePdf.addEventListener('click', () => {
    pdfModal.close();
    pdfFrame.src = '';
  });

  // Scrape Modal
  btnOpenScrape.addEventListener('click', () => {
    scrapeModal.showModal();
  });

  btnCloseScrape.addEventListener('click', () => {
    scrapeModal.close();
  });

  // Close modals on backdrop click
  [pdfModal, scrapeModal].forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.close();
        if (modal === pdfModal) pdfFrame.src = '';
      }
    });
  });

  // Portal / Site filter pills
  const portalPills = document.querySelectorAll('#portal-pills .pill');
  portalPills.forEach(pill => {
    pill.addEventListener('click', () => {
      portalPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      currentPortalFilter = pill.dataset.portal;
      renderJobs();
    });
  });

  // Portal checkboxes helpers in Scrape Modal
  const btnSelectAllPortals = document.getElementById('btn-select-all-portals');
  const btnClearPortals = document.getElementById('btn-clear-portals');
  if (btnSelectAllPortals) {
    btnSelectAllPortals.addEventListener('click', () => {
      document.querySelectorAll('input[name="scrape-portals"]').forEach(cb => cb.checked = true);
    });
  }
  if (btnClearPortals) {
    btnClearPortals.addEventListener('click', () => {
      document.querySelectorAll('input[name="scrape-portals"]').forEach(cb => cb.checked = false);
    });
  }

  // Scrape form submit
  formScrape.addEventListener('submit', async (e) => {
    e.preventDefault();
    const q = document.getElementById('scrape-query').value.trim();
    const l = document.getElementById('scrape-location').value.trim();
    const n = parseInt(document.getElementById('scrape-limit').value, 10);
    const age = parseInt(document.getElementById('scrape-jobage').value, 10) || 2;

    const checkedBoxes = Array.from(document.querySelectorAll('input[name="scrape-portals"]:checked'));
    if (checkedBoxes.length === 0) {
      showToast('Please select at least one portal/site to scrape.', 'error');
      return;
    }
    const selectedPortals = checkedBoxes.map(cb => cb.value);
    const portalsArg = selectedPortals.length === 5 ? 'all' : selectedPortals.join(',');
    const portalNames = selectedPortals.map(formatPortalName).join(', ');

    btnSubmitScrape.disabled = true;
    btnSubmitScrape.textContent = 'Running Scraper...';

    showToast(`Searching [${portalNames}]${q ? ` for "${q}"` : ""} in ${l} (max ${age} days old)...`);

    try {
      const res = await fetch('/api/scrape', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: q, location: l, limit: n, jobage: age, portals: portalsArg })
      });
      const data = await res.json();
      if (data.success) {
        showToast(data.warning || 'Scrape complete! Reloading newly discovered positions...', data.warning ? 'error' : 'success');
        scrapeModal.close();
        await loadData();
      } else {
        showToast('Scrape warning: ' + (data.error || 'Failed'), 'error');
      }
    } catch (err) {
      showToast('Error triggering scraper: ' + err.message, 'error');
    } finally {
      btnSubmitScrape.disabled = false;
      btnSubmitScrape.textContent = 'Start Scraper Run';
    }
  });
}

// Global actions for portal interaction
window.filterByPortal = function(portalKey) {
  currentPortalFilter = portalKey;
  const portalPills = document.querySelectorAll('#portal-pills .pill');
  portalPills.forEach(p => {
    if (p.dataset.portal === portalKey) {
      p.classList.add('active');
    } else {
      p.classList.remove('active');
    }
  });
  renderJobs();
  const name = formatPortalName(portalKey);
  showToast(`Filtered opportunities to ${name}!`);
};

window.openScrapeForPortal = function(portalKey) {
  const checkboxes = document.querySelectorAll('input[name="scrape-portals"]');
  checkboxes.forEach(cb => {
    cb.checked = (cb.value === portalKey);
  });
  scrapeModal.showModal();
};

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.style.borderColor = type === 'error' ? 'var(--accent-rose)' : 'var(--primary)';
  toast.textContent = msg;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function escapeStr(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'");
}

function escapeAttr(str) {
  if (!str) return '';
  return String(str).replace(/[^a-zA-Z0-9_-]/g, '_');
}
