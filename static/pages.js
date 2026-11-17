/* GitHub Pages transport: generated rules + browser-only persistence. */
"use strict";
(() => {
  const clone = value => JSON.parse(JSON.stringify(value));
  const isObject = value => value !== null && typeof value === "object" && !Array.isArray(value);
  const own = (obj, key) => Object.prototype.hasOwnProperty.call(obj, key);

  function createApi(data, storage, storageKey) {
    const catalog = data.catalog;
    function cleanAnswers(route, answers, complete = false) {
      if (!own(catalog.questions, route)) throw new Error("Choose a supported route.");
      if (!isObject(answers)) throw new Error("Answers must be an object.");
      const questions = catalog.questions[route];
      const known = new Map(questions.map(q => [q.id, q]));
      for (const [key, value] of Object.entries(answers)) {
        if (!known.has(key)) throw new Error("Unknown question.");
        if (!known.get(key).options.some(o => o.value === value)) throw new Error("Invalid answer for " + key + ".");
      }
      const cleaned = {};
      for (const q of questions) {
        if (!Object.entries(q.when).every(([key, values]) => values.includes(answers[key]))) continue;
        if (own(answers, q.id)) cleaned[q.id] = answers[q.id];
        else if (complete) throw new Error("Answer every applicable question before generating a checklist.");
      }
      return cleaned;
    }

    function selection(route, input) {
      input = input ?? {};
      if (!isObject(input) || Object.keys(input).some(k => !["identity", "years"].includes(k))) throw new Error("Invalid points selection.");
      const ids = input.identity ?? [], years = input.years ?? [];
      if (!Array.isArray(ids) || !Array.isArray(years)) throw new Error("Invalid points selection.");
      if (route === "fbr") {
        if (ids.length || years.length) throw new Error("Foreign Births Registration does not use points.");
        return {identity: [], years: []};
      }
      const card = data.scorecards[route];
      if (ids.some(id => typeof id !== "string" || !card.identity.some(d => d.id === id))) throw new Error("Unknown identity document.");
      if (new Set(ids).size !== ids.length) throw new Error("Select each document option only once.");
      if (years.length > card.years) throw new Error("Too many residence years.");
      const rows = years.map(row => {
        if (!isObject(row) || Object.keys(row).some(k => !["a", "b"].includes(k))) throw new Error("Invalid residence year.");
        const cleaned = {};
        for (const kind of ["a", "b"]) {
          const value = row[kind] ?? "";
          if (typeof value !== "string" || (value && !card["type_" + kind].some(d => d.id === value))) throw new Error("Choose a document from the correct residence category.");
          cleaned[kind] = value;
        }
        return cleaned;
      });
      while (rows.length < card.years) rows.push({a: "", b: ""});
      return {identity: [...ids], years: rows};
    }

    function evaluate(route, input, choices) {
      const answers = cleanAnswers(route, input, true);
      let node = data.nodes[data.roots[route]];
      while (own(node, "question")) node = data.nodes[node.branches[answers[node.question]]];
      const leaf = data.results[node.result];
      const selected = selection(route, choices);
      const card = leaf.scorecard ? data.scorecards[route] : null;
      let totals = null;
      if (card) {
        const identity = card.identity.filter(d => selected.identity.includes(d.id)).reduce((sum, d) => sum + d.points, 0);
        const annual = selected.years.map(row => (row.a ? 100 : 0) + (row.b ? 50 : 0));
        totals = {identity, identity_met: identity >= 150,
          passport_overlap: card.identity.filter(d => selected.identity.includes(d.id) && d.family === "passport").length > 1,
          years: annual, residence_met: annual.every(n => n === 150)};
      }
      return clone({version: catalog.version, route, answers, status: leaf.status,
        documents: leaf.documents.map(id => data.documents[id]),
        notices: leaf.notices.map(id => data.notices[id]), reviewed: catalog.reviewed,
        scorecard: card, selection: selected, totals});
    }

    function draft(method, body) {
      if (method === "DELETE") {
        storage.removeItem(storageKey);
        return {deleted: true};
      }
      if (method === "GET") {
        const raw = storage.getItem(storageKey);
        if (raw === null) return {draft: null, outdated: false};
        const saved = JSON.parse(raw);
        if (!isObject(saved) || !own(catalog.questions, saved.route)) throw new Error("Saved progress could not be read. Use your browser’s site-data settings to clear this site’s saved data.");
        // Old-version answers are reviewed from scratch by the UI before reuse.
        if (saved.version === catalog.version) validateDraft(saved);
        return {draft: saved, outdated: saved.version !== catalog.version};
      }
      const saved = validateDraft(body);
      storage.setItem(storageKey, JSON.stringify(saved));
      return {saved: true, updated: saved.updated};
    }

    function validateDraft(body) {
      if (!isObject(body)) throw new Error("Expected an object.");
      const stage = body.stage ?? "questions";
      if (!["questions", "review", "checklist"].includes(stage)) throw new Error("Invalid stage.");
      const route = body.route;
      const answers = cleanAnswers(route, body.answers ?? {}, stage !== "questions");
      const choices = selection(route, body.selection);
      let checked = body.checked ?? [];
      if (!Array.isArray(checked) || checked.length > 100 || checked.some(id => typeof id !== "string")) throw new Error("Invalid document progress.");
      if (stage === "checklist") {
        const valid = new Set(evaluate(route, answers, choices).documents.map(d => d.id));
        checked = [...new Set(checked.filter(id => valid.has(id)))];
      } else checked = [];
      return {route, answers, selection: choices, checked, stage, version: catalog.version, updated: new Date().toISOString()};
    }

    return async function api(path, method = "GET", body) {
      if (path === "/api/catalog" && method === "GET") return clone(catalog);
      if (path === "/api/health" && method === "GET") return {status: "ok", version: catalog.version};
      if (path === "/api/evaluate" && method === "POST") {
        if (!isObject(body)) throw new Error("Expected an object.");
        return evaluate(body.route, body.answers, body.selection);
      }
      if (path === "/api/draft" && ["GET", "PUT", "DELETE"].includes(method)) {
        try { return draft(method, body); }
        catch (error) {
          if (error.name === "QuotaExceededError" || error.name === "SecurityError") throw new Error("Your browser blocked saved progress. Allow site storage or continue without saving.");
          if (error instanceof SyntaxError) throw new Error("Saved progress is damaged. Clear this site’s saved data in your browser settings.");
          throw error;
        }
      }
      throw new Error("Not found.");
    };
  }

  // Export the same runtime for Node tests; browsers load only public rule data.
  if (typeof module !== "undefined" && module.exports) module.exports = {createApi};
  if (typeof window !== "undefined") {
    const storage = {
      getItem: key => window.localStorage.getItem(key),
      setItem: (key, value) => window.localStorage.setItem(key, value),
      removeItem: key => window.localStorage.removeItem(key),
    };
    const base = new URL("./", window.location.href);
    const ready = fetch(new URL("pages-data.json", base)).then(response => {
      if (!response.ok) throw new Error("Could not load the checklist rules. Refresh and try again.");
      return response.json();
    }).then(data => createApi(data, storage, "passport-agent:pages:v1:" + base.pathname));
    window.PassportAgentPages = {api: async (...args) => (await ready)(...args)};
  }
})();
