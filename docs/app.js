"use strict";
const $ = (s) => document.querySelector(s);
const escapeHTML = (value) => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
let catalog, saved, result;
let state = {route:null, answers:{}, checked:[], selection:{identity:[],years:[]}, stage:"home", index:0};
let savingEnabled = false, saveQueue = Promise.resolve(), busy = false;
const main = $("#main");

async function api(path, method="GET", body) {
  if (globalThis.PassportAgentPages) return globalThis.PassportAgentPages.api(path, method, body);
  const response = await fetch(path, {
    method, credentials:"same-origin",
    headers: {"Content-Type":"application/json", "X-Passport-Agent":"local"},
    ...(body === undefined ? {} : {body:JSON.stringify(body)})
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong. Please try again.");
  return data;
}
function toast(message) {
  $("#toast").textContent = message;
  $("#toast").classList.add("visible");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => $("#toast").classList.remove("visible"), 5000);
}
function modal(title, content) {
  $("#modal-content").innerHTML = `<p class="eyebrow">PASSPORT AGENT</p><h2 id="modal-title">${escapeHTML(title)}</h2>${content}`;
  $("#modal").showModal();
}
function sourceLink(key, label) {
  const s = catalog.sources[key];
  return `<a class="source-link" href="${escapeHTML(s.url)}" target="_blank" rel="noopener noreferrer">${escapeHTML(label || s.title)} <span aria-hidden="true">↗</span></a>`;
}
function routeInfo() { return catalog.routes.find(r => r.id === state.route); }
function activeQuestions() {
  return catalog.questions[state.route].filter(q => Object.entries(q.when).every(([key, values]) => values.includes(state.answers[key])));
}
function pruneAnswers() {
  const keys = new Set(activeQuestions().map(q => q.id));
  for (const key of Object.keys(state.answers)) if (!keys.has(key)) delete state.answers[key];
}
function focusHeading() {
  requestAnimationFrame(() => {
    const heading = main.querySelector("h1, legend, h2");
    if (heading) { heading.tabIndex = -1; heading.focus({preventScroll:true}); }
    window.scrollTo({top:0, behavior:"instant"});
  });
}
function stepper(step) {
  return `<ol class="steps" aria-label="Application progress">${["Choose your route","Answer a few questions","Your document checklist"].map((label,i) =>
    `<li class="${step===i ? "active" : step>i ? "done" : ""}" ${step===i ? 'aria-current="step"' : ""}><span>${step>i ? "✓" : `0${i+1}`}</span>${label}</li>`).join("")}</ol>`;
}
function render() {
  $("#home-nav").classList.toggle("selected", state.stage !== "sources");
  $("#sources-nav").classList.toggle("selected", state.stage === "sources");
  if (state.stage === "home") renderHome();
  else if (state.stage === "questions") renderQuestion();
  else if (state.stage === "review") renderReview();
  else if (state.stage === "checklist") renderChecklist();
  else if (state.stage === "sources") renderSources();
  focusHeading();
}
function renderHome() {
  main.innerHTML = `
    <section class="hero">
      <div class="hero-copy"><p class="eyebrow"><span class="small-line"></span> IRISH CITIZENSHIP, MADE CLEARER</p>
        <h1>Your next chapter.<br><em>A clearer path.</em></h1>
        <p class="hero-description">Know which documents you need, why you need them, and what to do next. One personalised checklist for your journey to Irish citizenship.</p>
        <div class="hero-notes"><span><b>✓</b> Based on official guidance</span><span><b>✓</b> No document uploads</span></div>
      </div>
      <div class="hero-art" aria-hidden="true">
        <div class="orbit orbit-one"></div><div class="orbit orbit-two"></div><span class="star star-one">✳</span>
        <div class="passport-book"><div class="book-top">ÉIRE <span>IRELAND</span></div><div class="harp">♧</div><div class="book-bottom">YOUR NEXT CHAPTER<br><span>PASSPORT AGENT</span></div></div>
        <div class="floating-note"><span class="note-check">✓</span><div>A little less paperwork.<br><strong>A lot more clarity.</strong></div></div>
        <span class="art-caption">A JOURNEY WORTH PREPARING FOR</span>
      </div>
    </section>
    ${saved ? `<section class="resume-strip"><div><span class="status-dot"></span><strong>Your saved journey is here.</strong> <span>${escapeHTML(catalog.routes.find(r=>r.id===saved.route)?.subtitle || "Saved checklist")}</span></div><div><button class="text-button danger" data-action="delete">Delete</button><button class="button small" data-action="resume">Continue journey <span>↗</span></button></div></section>` : ""}
    <section class="route-section" aria-labelledby="route-heading">
      <div class="section-heading"><div><p class="eyebrow">LET’S START WITH YOUR ROUTE</p><h2 id="route-heading">What brings you here?</h2></div><p>Choose the route that fits your circumstances.<br>We’ll take it one question at a time.</p></div>
      <div class="route-grid">${catalog.routes.map(r => `<button class="route-card" data-route="${r.id}"><div class="card-top"><span class="route-icon" aria-hidden="true">${r.id==="fbr" ? "♧" : r.id==="residence" ? "⌂" : "♡"}</span><span class="route-number">${r.number}</span></div><span class="tag">${escapeHTML(r.tag)}</span><h3>${escapeHTML(r.title)}</h3><p>${escapeHTML(r.description)}</p><span class="card-bottom">${escapeHTML(r.subtitle)} <span aria-hidden="true">↗</span></span></button>`).join("")}</div>
      <div class="route-help"><span>Not sure where to begin?</span> <button class="text-button" data-action="finder">Help me find a route <span aria-hidden="true">→</span></button><button class="text-button other-routes" data-action="other">Looking for another route?</button></div>
    </section>
    <section class="how-strip"><div><span>01</span><div><h3>Choose your route</h3><p>Start with your circumstances.</p></div></div><div><span>02</span><div><h3>Answer a few questions</h3><p>Only what shapes your checklist.</p></div></div><div><span>03</span><div><h3>Get your documents ready</h3><p>Clear instructions. Official sources.</p></div></div></section>
    <p class="scope-note">Currently covers standard adult applications. Special cases are directed to official guidance. A checklist helps you prepare; it does not confirm eligibility.</p>`;
}
function renderQuestion() {
  const qs = activeQuestions();
  state.index = Math.min(state.index, qs.length-1);
  const q = qs[state.index];
  main.innerHTML = `${stepper(1)}<div class="workspace">
    <aside class="journey-aside"><p class="eyebrow">YOUR CHOSEN ROUTE</p><h2>${escapeHTML(routeInfo().title)}</h2><p>${escapeHTML(routeInfo().subtitle)}</p><button class="text-button" data-action="change-route">Change route ↗</button>
      <div class="aside-note"><span aria-hidden="true">◎</span><h3>A checklist that fits you.</h3><p>Your answers help us include the right documents and flag anything that needs a closer look.</p><p>No names, passport numbers or document uploads needed.</p></div>${sourceLink(routeInfo().source)}</aside>
    <section class="question-panel"><div class="question-meta"><span>QUESTION ${String(state.index+1).padStart(2,"0")} OF ${String(qs.length).padStart(2,"0")}</span><span>${Math.round((state.index/qs.length)*100)}% through</span></div><progress value="${state.index}" max="${qs.length}" aria-label="Question progress"></progress>
      <form id="question-form"><fieldset><legend>${escapeHTML(q.title)}</legend><p class="question-help">${escapeHTML(q.help)}</p>
      <div class="answer-options">${q.options.map(o=>`<label class="answer-option ${state.answers[q.id]===o.value ? "chosen" : ""}"><input type="radio" name="answer" value="${escapeHTML(o.value)}" ${state.answers[q.id]===o.value ? "checked" : ""} required><span>${escapeHTML(o.label)}</span></label>`).join("")}</div></fieldset>
      <div class="question-actions"><button class="text-button" type="button" data-action="back">← Back</button><button class="button" type="submit">${state.index===qs.length-1 ? "Review answers" : "Continue"} <span>→</span></button></div></form>
      <div class="save-row"><span>Stored only if you choose to save.</span><button class="text-button" data-action="save">${savingEnabled ? "Save progress ✓" : "Save for later"}</button></div></section></div>`;
}
function renderReview() {
  main.innerHTML = `${stepper(1)}<section class="review-page"><p class="eyebrow">${escapeHTML(routeInfo().subtitle)}</p><h1>Let’s check the details.</h1><p class="page-description">Check your answers, then see the documents and points you need.</p>
    <div class="review-list">${activeQuestions().map((q,i)=>`<div class="review-row"><div><p>${escapeHTML(q.title)}</p><strong>${escapeHTML(q.options.find(o=>o.value===state.answers[q.id])?.label || "Not answered")}</strong></div><button class="text-button" data-edit="${i}">Change<span class="sr-only"> ${escapeHTML(q.title)}</span></button></div>`).join("")}</div>
    <div class="question-actions"><button class="text-button" data-action="back">← Back</button><button class="button" data-action="generate">Build my checklist <span>→</span></button></div></section>`;
}
function noticesHTML() {
  if (!result.notices.length) return "";
  return `<section class="notice-panel"><h2>${result.documents.length ? "A few things to clarify" : "This route needs a closer look"}</h2>${result.notices.map(n=>`<p>${escapeHTML(n.text)} ${sourceLink(n.source,"Official guidance")}</p>`).join("")}</section>`;
}
function requirementsOverview() {
  if (!result.documents.length) return "";
  if (!result.scorecard) return `<section class="requirements-overview"><h2>No points system for this route</h2><p>Foreign Births Registration uses a fixed document list. Provide every required record and choose an accepted ID where alternatives are listed.</p></section>`;
  const c = result.scorecard;
  return `<section class="requirements-overview"><h2>What you need to provide</h2><div class="requirements-grid"><a href="#required-documents"><strong>Required records</strong><span>Prepare each applicable item</span><small>Needed separately from the points targets</small></a><a href="#identity-options"><strong>150 identity points</strong><span>Once for your application</span><small>Choose one or combine alternatives</small></a><a href="#residence-options"><strong>150 residence points</strong><span>For EACH of ${c.years} qualifying years</span><small>100-point document + 50-point document</small></a></div><p>${escapeHTML(c.period)} Identity points and different years cannot be combined.</p></section>`;
}
function plannedTotals() {
  const c = result.scorecard;
  const selection = state.selection || {identity:[],years:[]};
  return {identity:c.identity.filter(d=>selection.identity.includes(d.id)).reduce((sum,d)=>sum+d.points,0),
    years:Array.from({length:c.years},(_,i)=> {
      const row = selection.years[i] || {};
      return (c.type_a.find(d=>d.id===row.a)?.points || 0) + (c.type_b.find(d=>d.id===row.b)?.points || 0);
    })};
}
function scoreLabel(total) {
  return `${total} / 150 points${total >= 150 ? " · Points target reached" : ` · ${150-total} more needed`}`;
}
function identitySelectionNote() {
  const selected = state.selection?.identity || [];
  const passports = result.scorecard.identity.filter(d=>selected.includes(d.id) && d.family==="passport");
  return passports.length > 1 ? "Multiple passport categories selected. The total adds every selected row; confirm with ISD which passport evidence can be counted together." : "The total adds the points shown for every selected row.";
}
function yearLabel(index) { return index===0 ? "12 months before applying" : `Earlier qualifying year ${index}`; }
function updatePointTotals() {
  const total = plannedTotals();
  $("#identity-total").textContent = scoreLabel(total.identity);
  $("#identity-selection-note").textContent = identitySelectionNote();
  total.years.forEach((value,i)=> { $("#year-total-"+i).textContent = scoreLabel(value); });
}
function evidenceTable(items, caption, identity=false) {
  const chosen = state.selection?.identity || [];
  return `<div class="table-scroll" tabindex="0" role="region" aria-label="${escapeHTML(caption)}"><table class="evidence-table"><caption>${escapeHTML(caption)}</caption><thead><tr>${identity ? '<th scope="col">Use</th>' : ''}<th scope="col">Document you can use</th><th scope="col">Points</th><th scope="col">Requirements</th></tr></thead><tbody>${items.map(d=>`<tr>${identity ? `<td><input type="checkbox" data-identity="${d.id}" aria-label="Use ${escapeHTML(d.title)} for identity" ${chosen.includes(d.id)?"checked":""}></td>` : ''}<th scope="row">${escapeHTML(d.title)}</th><td><span class="point-value">${d.points===null ? "Confirm" : d.points}</span></td><td>${escapeHTML(d.note)}<br>${sourceLink(d.source,"Source")}</td></tr>`).join("")}</tbody></table></div>`;
}
function pointsHTML() {
  const c=result.scorecard;
  if (!c) return "";
  const total=plannedTotals();
  const optionTags = (items,value) => `<option value="">Choose a document</option>${items.map(d=>`<option value="${d.id}" ${d.id===value ? "selected" : ""}>${escapeHTML(d.title)} — ${d.points} points</option>`).join("")}`;
  return `<section id="identity-options" class="points-section"><p class="eyebrow">CHOOSE YOUR IDENTITY EVIDENCE</p><h2>Identity: 150 points once</h2><p>Choose enough documents to reach 150 points. A current passport is enough on its own. Another combination is a recently expired passport (75) plus a certified IRP (75).</p><p class="score-total" id="identity-total" role="status" aria-live="polite">${scoreLabel(total.identity)}</p><p class="small-copy">Select as many documents as you want, even after reaching 150 points. Nothing is automatically deselected.</p><p class="small-copy" id="identity-selection-note" role="status" aria-live="polite">${escapeHTML(identitySelectionNote())}</p>${evidenceTable(c.identity,"Identity document options",true)}</section>
    <section id="residence-options" class="points-section"><p class="eyebrow">CHOOSE EVIDENCE FOR EACH YEAR</p><h2>Residence: 150 points per year</h2><p>For each of your ${c.years} qualifying years, choose <strong>one Type A document (100 points)</strong> and <strong>one Type B document (50 points)</strong>. You do not need every document in these tables. Three 50-point documents do not replace the Type A requirement.</p><p>${escapeHTML(c.period)}</p><p>Use evidence from each claimed year, showing your name, address and date. Do not reuse one year's file for another year.</p>
    ${evidenceTable(c.type_a,"Type A · choose ONE per year · 100 points")}${evidenceTable(c.type_b,"Type B · choose ONE per year · 50 points")}
    <h3>Plan your evidence for each year</h3><p class="small-copy">Each row is a separate period. These rows do not calculate whether your time in Ireland qualifies.</p><div class="year-planner">${total.years.map((value,i)=>`<fieldset class="year-row"><legend>${yearLabel(i)}</legend><label>Type A — 100 points<select data-year="${i}" data-kind="a" aria-label="${yearLabel(i)}: Type A">${optionTags(c.type_a,state.selection?.years?.[i]?.a)}</select></label><label>Type B — 50 points<select data-year="${i}" data-kind="b" aria-label="${yearLabel(i)}: Type B">${optionTags(c.type_b,state.selection?.years?.[i]?.b)}</select></label><p id="year-total-${i}" role="status" aria-live="polite">${scoreLabel(value)}</p></fieldset>`).join("")}</div>
    <h3>Other published options — confirm before using</h3><p>These appear in older scorecards or general guidance. Their current individual score is not confirmed, so they are excluded from the tracker.</p>${evidenceTable(c.other_residence,"Other evidence and historical points — confirmation needed")}
    <div class="final-note"><h3>Missing documents or not enough points?</h3><p>Provide the evidence you have and contact ISD about alternatives. A sworn identity or residence affidavit is an exceptional option where records cannot reasonably be obtained; it does not automatically add points or guarantee acceptance.</p>${sourceLink("proofs","Read the evidence alternatives")}</div></section>`;
}
function pointsText() {
  if (!result.scorecard) return ["POINTS: Foreign Births Registration has no points system.", ""];
  const c=result.scorecard, total=plannedTotals();
  const lines=["IDENTITY: 150 points once",`Planned: ${scoreLabel(total.identity)}`,"Multiple selections are allowed above 150 points.",identitySelectionNote()];
  for (const d of c.identity) lines.push(`${state.selection?.identity?.includes(d.id)?"[selected] ":""}${d.title}: ${d.points} points. ${d.note}\nSource: ${catalog.sources[d.source].url}`);
  lines.push("",`RESIDENCE: 150 points for EACH of ${c.years} qualifying years.`,c.period,"Choose one Type A (100) + one Type B (50) for each year.");
  for (const [title,items] of [["TYPE A OPTIONS",c.type_a],["TYPE B OPTIONS",c.type_b],["OTHER OPTIONS — confirm current score; excluded from tracker",c.other_residence]]) {
    lines.push("",title);
    for (const d of items) lines.push(`${d.title}: ${d.points===null?"Points unconfirmed":d.points+" points"}. ${d.note}\nSource: ${catalog.sources[d.source].url}`);
  }
  lines.push("","YOUR YEAR-BY-YEAR PLAN");
  total.years.forEach((value,i)=> {
    const row=state.selection?.years?.[i] || {};
    lines.push(`${yearLabel(i)}: ${scoreLabel(value)}`,`Type A: ${c.type_a.find(d=>d.id===row.a)?.title || "Not selected"}`,`Type B: ${c.type_b.find(d=>d.id===row.b)?.title || "Not selected"}`);
  });
  lines.push("","Points totals are a preparation aid, not verification of evidence or eligibility.","");
  return lines;
}

function renderChecklist() {
  const checked = new Set(state.checked);
  const ready = result.documents.filter(d=>checked.has(d.id)).length;
  const groups = [...new Set(result.documents.map(d=>d.owner))];
  main.innerHTML = `${stepper(2)}<section class="checklist-header"><div><p class="eyebrow">${escapeHTML(routeInfo().subtitle)}</p><h1>${result.documents.length ? "Your document checklist" : "Let’s find the right next step."}</h1><p class="page-description">${result.documents.length ? "Required records, document choices and points — all in one place." : "We won’t give you a checklist that misses your circumstances."}</p></div>
      <div class="toolbar"><button class="button secondary" data-action="edit">Edit answers</button>${result.documents.length ? '<button class="button" data-action="print">Print / PDF ↗</button>' : ""}</div></section>
    ${requirementsOverview()}
    ${noticesHTML()}
    ${result.documents.length ? `<div class="checklist-layout"><aside class="progress-card"><p class="eyebrow">YOUR PREPARATION</p><p class="progress-number"><strong id="ready-count">${ready}</strong><span> / ${result.documents.length}</span></p><p>required items marked ready</p><progress id="document-progress" value="${ready}" max="${result.documents.length}" aria-label="Documents ready"></progress><p class="small-copy">Tick a document when you have prepared it. This tracks your progress, not official verification.</p>
      <button class="button full" data-action="save">${savingEnabled ? "Save progress" : "Save this checklist"}</button><button class="text-button download" data-action="download">Download as text ↓</button><hr><p class="small-copy">Guidance checked ${escapeHTML(result.reviewed)}<br>Rules ${escapeHTML(result.version)}</p><button class="text-button" data-action="sources">View official sources ↗</button></aside>
      <div class="document-groups"><section id="required-documents" class="section-intro"><h2>Required documents</h2><p>Prepare each applicable item below. These are needed separately from meeting the points targets.</p></section>${groups.map(owner=>`<section class="document-group"><h2>${escapeHTML(owner)} <span>${result.documents.filter(d=>d.owner===owner).length} documents</span></h2>${result.documents.filter(d=>d.owner===owner).map(d=>`<article class="document ${checked.has(d.id) ? "is-ready" : ""}">
        <div class="document-heading"><input type="checkbox" data-document="${d.id}" id="doc-${d.id}" ${checked.has(d.id) ? "checked" : ""} aria-label="Mark ${escapeHTML(owner)}: ${escapeHTML(d.title)} ready"><div><label for="doc-${d.id}">${escapeHTML(d.title)}</label><div class="document-tags"><span>${escapeHTML(d.format)}</span>${d.conditional ? '<span class="conditional">Confirm if needed</span>' : '<span>Required</span>'}<span>${escapeHTML(d.points_label || "Not scored")}</span></div></div></div>
        <div class="document-body"><p>${escapeHTML(d.detail)}</p><p class="document-reason"><strong>Why it’s here:</strong> ${escapeHTML(d.reason)}</p>${sourceLink(d.source)}</div></article>`).join("")}</section>`).join("")}
      ${pointsHTML()}<section class="final-note"><h3>Before you apply</h3><p>Compare this list with the current official application form, including its witness and upload instructions. The receiving authority may request further evidence. This app has not verified your eligibility or documents.</p></section></div></div>` :
      `<div class="empty-actions"><button class="button" data-action="change-route">Explore the other routes →</button></div>`}`;
}
function renderSources() {
  main.innerHTML = `<section class="sources-page"><p class="eyebrow">CLEAR GUIDANCE. TRACEABLE SOURCES.</p><h1>Go straight to the source.</h1><p class="page-description">Every checklist item links to the official instructions behind it. These are the sources used in this edition.</p><div class="source-grid">${Object.entries(catalog.sources).map(([key,s])=>`<article class="source-card"><span class="tag">OFFICIAL SOURCE</span><h2>${escapeHTML(s.title)}</h2><p>${escapeHTML(s.section)}</p><p class="small-copy">Reviewed ${escapeHTML(s.reviewed)}</p>${sourceLink(key,"Read official instructions")}</article>`).join("")}</div><div class="final-note"><h3>What this edition covers</h3><p>Standard adult Foreign Births Registration through a grandparent, a registered parent or a naturalised parent; standard adult residence naturalisation; and spouse or civil partner naturalisation using Republic of Ireland residence evidence.</p><p>Children, adoption, refugee or stateless applications, dependent young adults, Northern Ireland residence evidence, and unusual family connections need a separate review. Online guidance may change after our review date.</p></div><button class="button secondary" data-action="return">← Back to your journey</button></section>`;
}
function saveProgress(explicit=false) {
  if (!state.route || !["questions","review","checklist"].includes(state.stage)) return Promise.resolve();
  const payload = JSON.parse(JSON.stringify({route:state.route, answers:state.answers, checked:state.checked, stage:state.stage, selection:state.selection || {identity:[],years:[]}}));
  saveQueue = saveQueue.catch(()=>{}).then(async () => {
    await api("/api/draft","PUT",payload);
    savingEnabled = true;
    saved = {...payload, version:catalog.version};
    if (explicit) toast("Progress saved. Come back in this browser to continue.");
  });
  return saveQueue;
}
function autosave() {
  if (savingEnabled) saveProgress().catch(e=>toast("Progress was not saved: "+e.message));
}
async function generate() {
  result = await api("/api/evaluate", "POST", {route:state.route, answers:state.answers, selection:state.selection || {identity:[],years:[]}});
  state.answers = result.answers;
  state.selection = result.selection || {identity:[],years:[]};
  const valid = new Set(result.documents.map(d=>d.id));
  state.checked = state.checked.filter(id=>valid.has(id));
  state.stage = "checklist";
  autosave();
  render();
}
function chooseRoute(route) {
  state = {route, answers:{}, checked:[], selection:{identity:[],years:[]}, stage:"questions", index:0};
  result = null;
  savingEnabled = false;
  render();
}
let previousStage = "home";
function showSources() {
  if (state.stage !== "sources") previousStage = state.stage;
  state.stage = "sources";
  render();
}
function download() {
  const lines = ["PASSPORT AGENT", routeInfo().subtitle, `Guidance reviewed: ${result.reviewed} | Rules: ${result.version}`, "",
    "Preparation checklist. Eligibility and documents have not been verified.", "",
    ...result.notices.map(n => `CHECK: ${n.text}\n${catalog.sources[n.source].url}`), ""];
  for (const d of result.documents) lines.push(`[${state.checked.includes(d.id) ? "x" : " "}] ${d.owner}: ${d.title}`,
    `Status: ${d.conditional ? "Confirm if needed" : "Required"} | Points: ${d.points_label || "Not scored"} | Format: ${d.format}`, d.detail, `Why: ${d.reason}`, `Source: ${catalog.sources[d.source].url}`, "");
  lines.push(...pointsText());
  lines.push("Compare this list with the current official application instructions before submitting.");
  const url = URL.createObjectURL(new Blob([lines.join("\n")], {type:"text/plain;charset=utf-8"}));
  const a = document.createElement("a");
  a.href = url; a.download = `passport-agent-${state.route}-checklist.txt`; a.click();
  setTimeout(()=>URL.revokeObjectURL(url),1000);
}
main.addEventListener("submit", event => {
  if (event.target.id !== "question-form") return;
  event.preventDefault();
  const q = activeQuestions()[state.index];
  state.answers[q.id] = new FormData(event.target).get("answer");
  pruneAnswers();
  state.checked = [];
  if (state.index === activeQuestions().length-1) state.stage = "review";
  else state.index++;
  autosave(); render();
});
main.addEventListener("change", event => {
  if (event.target.dataset.identity) {
    const item = result.scorecard.identity.find(d => d.id === event.target.dataset.identity);
    const selected = state.selection ||= {identity:[],years:[]};
    selected.identity = selected.identity.filter(id => id !== item.id);
    if (event.target.checked) selected.identity.push(item.id);
    main.querySelectorAll("[data-identity]").forEach(el => { el.checked = selected.identity.includes(el.dataset.identity); });
    updatePointTotals(); autosave();
  }
  if (event.target.dataset.year !== undefined) {
    const selected = state.selection ||= {identity:[],years:[]};
    const index = Number(event.target.dataset.year);
    while (selected.years.length <= index) selected.years.push({a:"",b:""});
    selected.years[index][event.target.dataset.kind] = event.target.value;
    updatePointTotals(); autosave();
  }
  if (event.target.name === "answer") {
    main.querySelectorAll(".answer-option").forEach(label => label.classList.toggle("chosen", label.querySelector("input").checked));
    const q = activeQuestions()[state.index];
    state.answers[q.id] = event.target.value;
    pruneAnswers();
    state.checked = [];
    autosave();
  }
  if (event.target.dataset.document) {
    const id = event.target.dataset.document;
    state.checked = state.checked.filter(x=>x!==id);
    if (event.target.checked) state.checked.push(id);
    event.target.closest(".document").classList.toggle("is-ready",event.target.checked);
    $("#ready-count").textContent = state.checked.length;
    $("#document-progress").value = state.checked.length;
    autosave();
  }
});
main.addEventListener("click", async event => {
  const button = event.target.closest("button");
  if (!button || busy) return;
  try {
    if (button.dataset.route) return chooseRoute(button.dataset.route);
    if (button.dataset.edit !== undefined) {
      state.index = Number(button.dataset.edit); state.stage = "questions"; return render();
    }
    const action = button.dataset.action;
    if (action === "generate" || action === "resume" || action === "save" || action === "delete") {
      busy = true; button.disabled = true;
    }
    if (action === "back") {
      if (state.stage === "review") { state.stage="questions"; state.index=activeQuestions().length-1; }
      else if (state.index>0) state.index--;
      else state.stage="home";
      render();
    } else if (action === "generate") await generate();
    else if (action === "save") await saveProgress(true);
    else if (action === "edit") { state.stage="review"; render(); }
    else if (action === "change-route") { state.stage="home"; render(); }
    else if (action === "sources") showSources();
    else if (action === "return") { state.stage=previousStage; render(); }
    else if (action === "print") window.print();
    else if (action === "download") download();
    else if (action === "resume") {
      state = {...saved, index:0};
      savingEnabled = true;
      if (saved.version !== catalog.version) {
        state.stage="questions"; state.checked=[]; state.selection={identity:[],years:[]};
        state.answers={};
        toast("Guidance has changed. Review your answers to rebuild the checklist.");
      }
      if (state.stage === "checklist") await generate();
      else {
        const first = activeQuestions().findIndex(q=>!state.answers[q.id]);
        state.index = Math.max(0,first);
        render();
      }
    } else if (action === "delete") {
      if (confirm("Delete your saved answers and checklist?")) {
        await saveQueue.catch(()=>{});
        await api("/api/draft","DELETE");
        saved=null; savingEnabled=false; toast("Saved progress deleted."); render();
      }
    } else if (action === "finder") {
      modal("Start with your connection.", `<div class="finder-options"><p><strong>Have an Irish parent or grandparent?</strong><br>Check citizenship by birth or descent first. You may already be Irish. ${sourceLink("birth")}</p><p><strong>Applying based on time in Ireland?</strong><br>Explore “Living in Ireland”.</p><p><strong>Married to an Irish citizen?</strong><br>Explore “Married to an Irish citizen”.</p><p>These are starting points. The official guidance determines whether the route fits your circumstances.</p></div>`);
    } else if (action === "other") {
      modal("Every journey is different.", `<p>Children, adoption, Irish associations, refugees, stateless people, and former citizens have different requirements. Personalised lists for these cases are not yet available.</p><p>${sourceLink("guide","Explore the official citizenship guide")}</p><p>${sourceLink("birth","Check citizenship by birth or descent")}</p>`);
    }
  } catch (error) { toast(error.message); }
  finally { busy=false; button.disabled=false; }
});
$("#home-nav").addEventListener("click",()=>{if (catalog) {state.stage="home";render();}});
$("#sources-nav").addEventListener("click",()=>catalog && showSources());
$("#close-modal").addEventListener("click",()=>$("#modal").close());
function privacyContent() {
  if (catalog?.hosting?.mode === "browser") return "<p>Your answers are processed in this browser. They are saved only when you choose Save, using this browser’s storage on this device. Further changes to a saved journey are saved automatically.</p><p>Your answers and checklist are not sent to GitHub or a PythonAnywhere server. Clearing this site’s browser data deletes the saved journey. Delete saved progress from the home page whenever you want.</p><p>There are no document uploads or application accounts. Official-source links open government websites. GitHub Pages records normal website request information under GitHub’s privacy policy.</p>";
  const storage = catalog?.hosting?.mode === "hosted" ? "on the website’s server" : "on this computer";
  return `<p>Answers stay in this browser’s memory until you choose Save. Saved progress is kept ${storage} and linked to this browser by a cookie.</p><p>No analytics, accounts, or document uploads. Official-source links open external government websites. Delete saved progress from the home page whenever you want.</p><p>Once you save, further changes to that journey are saved automatically. Clearing browser cookies removes access to the saved journey but does not delete its database record.</p>`;
}
$("#privacy-button").addEventListener("click",()=>modal("About saved progress", privacyContent()));

async function init() {
  try {
    const [c,d] = await Promise.all([api("/api/catalog"),api("/api/draft").catch(error=>({draft:null,loadError:error.message}))]);
    catalog=c; saved=d.draft;
    if (["hosted", "browser"].includes(catalog.hosting?.mode)) $(".local-badge").innerHTML = "<i></i> Irish citizenship";
    render();
    if (d.loadError) toast(d.loadError);
  } catch (error) {
    main.innerHTML=`<section class="error-page"><h1>We couldn’t load your journey.</h1><p>${escapeHTML(error.message)}</p><p>Refresh this page to try again. If the problem continues, check that the application is running.</p><a class="button" href="./">Try again</a></section>`;
  }
}
init();
