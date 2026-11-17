/* Execute the real Pages runtime against Python-generated reference cases. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const crypto = require("node:crypto");
const vm = require("node:vm");
const {createApi} = require("../static/pages.js");
const data = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const fixtures = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
function canonical(value) {
  if (Array.isArray(value)) return value.map(canonical);
  if (value !== null && typeof value === "object") return Object.fromEntries(Object.keys(value).sort().map(k => [k, canonical(value[k])]));
  return value;
}
const memory = new Map();
const storage = {
  getItem: key => memory.get(key) ?? null,
  setItem: (key, value) => memory.set(key, value),
  removeItem: key => memory.delete(key),
};
async function main() {
  const api = createApi(data, storage, "test:passport-agent");
  for (const f of fixtures) {
    const actual = await api("/api/evaluate", "POST", {route: f.route, answers: f.answers});
    const digest = crypto.createHash("sha256").update(JSON.stringify(canonical(actual))).digest("hex");
    assert.equal(digest, f.digest, JSON.stringify(f.answers));
  }
  const base = fixtures.find(f => f.route === "residence" && f.answers.adult === "yes" && f.answers.special === "standard" && f.answers.location === "state");
  const payload = {route: base.route, answers: base.answers, stage: "checklist", checked: ["birth", "not-a-document"],
    selection: {identity: ["passport_recent", "passport_old", "irp_identity", "driving", "psc"], years: [{a: "bank", b: "rent"}]}};
  const evaluated = await api("/api/evaluate", "POST", payload);
  assert.equal(evaluated.totals.identity, 235);
  assert.equal(evaluated.totals.passport_overlap, true);
  assert.deepEqual(evaluated.totals.years, [150, 0, 0, 0, 0]);
  await api("/api/draft", "PUT", payload);
  const reloaded = createApi(data, storage, "test:passport-agent");
  const resumed = await reloaded("/api/draft");
  assert.deepEqual(resumed.draft.checked, ["birth"]);
  assert.deepEqual(resumed.draft.selection.identity, payload.selection.identity);
  assert.equal(resumed.outdated, false);
  assert.deepEqual(await createApi(data, storage, "other-project")("/api/draft"), {draft: null, outdated: false});
  await reloaded("/api/draft", "DELETE");
  assert.equal((await api("/api/draft")).draft, null);
  for (const invalid of [
    {...payload, selection: {identity: ["irp_identity", "irp_identity"]}},
    {...payload, selection: {years: [{a: "phone", b: "rent"}]}},
    {...payload, answers: {}},
    {...payload, route: "__proto__"},
  ]) await assert.rejects(api("/api/evaluate", "POST", invalid));
  await assert.rejects(api("/api/draft", "PUT", {...payload, stage: "invented"}));
  await assert.rejects(api("/api/draft", "PUT", {...payload, checked: "birth"}));
  const old = {...payload, version: "older-guidance"};
  storage.setItem("test:passport-agent", JSON.stringify(old));
  assert.equal((await api("/api/draft")).outdated, true);
  const denied = new Error("blocked"); denied.name = "SecurityError";
  const deniedStorage = {getItem(){throw denied;}, setItem(){throw denied;}, removeItem(){throw denied;}};
  const blocked = createApi(data, deniedStorage, "test");
  await assert.rejects(blocked("/api/draft"), /browser blocked/);
  assert.equal((await blocked("/api/evaluate", "POST", payload)).totals.identity, 235);
  // Run both real scripts together, including their load order and UI events.
  // DOM stubs exercise the application flow; they do not test visual layout.
  const browserStorage = new Map();
  async function browser(denyStorage = false) {
    const elements = new Map(), requests = [];
    function element(id) {
      if (!elements.has(id)) elements.set(id, {innerHTML: "", textContent: "", listeners: {},
        classList: {toggle(){}, add(){}, remove(){}},
        addEventListener(type, fn){this.listeners[type] = fn;},
        querySelector: element, querySelectorAll: () => [], focus(){}, showModal(){}, close(){}});
      return elements.get(id);
    }
    const context = {
      URL, console, location: {href: "https://example.github.io/passport-agent/"},
      localStorage: {
        getItem(key){ if (denyStorage) throw denied; return browserStorage.get(key) ?? null; },
        setItem(key,value){ if (denyStorage) throw denied; browserStorage.set(key,value); },
        removeItem(key){ if (denyStorage) throw denied; browserStorage.delete(key); },
      },
      document: {querySelector: element},
      fetch: async url => {
        requests.push(String(url));
        assert.equal(String(url), "https://example.github.io/passport-agent/pages-data.json");
        return {ok: true, json: async () => JSON.parse(JSON.stringify(data))};
      },
      FormData: class {constructor(form){this.form=form;} get(){return this.form.answer;}},
      requestAnimationFrame: fn => fn(), scrollTo(){}, setTimeout: () => 1, clearTimeout(){},
      confirm: () => true,
    };
    context.window = context;
    vm.createContext(context);
    vm.runInContext(fs.readFileSync(require.resolve("../static/pages.js"), "utf8"), context);
    await vm.runInContext(fs.readFileSync(require.resolve("../static/app.js"), "utf8"), context);
    async function action(name) {
      await element("#main").listeners.click({target: {closest: () => ({dataset: {action: name}})}});
    }
    return {context, element, requests, action};
  }
  const ui = await browser();
  assert.ok(ui.element("#main").innerHTML.includes('data-route="residence"'));
  vm.runInContext('chooseRoute("residence")', ui.context);
  while (vm.runInContext("state.stage", ui.context) === "questions") {
    const id = vm.runInContext("activeQuestions()[state.index].id", ui.context);
    ui.element("#main").listeners.submit({target:{id:"question-form", answer:base.answers[id]}, preventDefault(){}});
  }
  assert.equal(vm.runInContext("state.stage", ui.context), "review");
  await ui.action("generate");
  assert.ok(ui.element("#main").innerHTML.includes("Identity: 150 points once"));
  for (const id of payload.selection.identity) {
    ui.element("#main").listeners.change({target:{dataset:{identity:id},checked:true}});
  }
  assert.ok(ui.element("#identity-total").textContent.startsWith("235 / 150"));
  await ui.action("save");
  const resumedUI = await browser();
  assert.ok(resumedUI.element("#main").innerHTML.includes("Your saved journey is here."));
  await resumedUI.action("resume");
  assert.equal(vm.runInContext("plannedTotals().identity", resumedUI.context), 235);
  assert.ok(vm.runInContext("privacyContent()", resumedUI.context).includes("browser’s storage"));
  await resumedUI.action("change-route");
  await resumedUI.action("delete");
  assert.ok(!resumedUI.element("#main").innerHTML.includes("Your saved journey is here."));
  const noStorageUI = await browser(true);
  assert.ok(noStorageUI.element("#main").innerHTML.includes('data-route="residence"'));
  assert.ok(noStorageUI.element("#toast").textContent.includes("browser blocked"));
  console.log(`Pages runtime matches Python for all ${fixtures.length.toLocaleString()} answer combinations; save, reload, delete and points tests pass.`);
}
main().catch(error => { console.error(error); process.exitCode = 1; });
