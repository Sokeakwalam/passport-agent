"""JavaScriptCore rendering smoke test; not a substitute for browser/layout QA."""
import ctypes
import json
from pathlib import Path
import sys
import unittest

from rules import catalog, evaluate
from tests.test_rules import answers


@unittest.skipUnless(sys.platform == "darwin", "Uses macOS system JavaScriptCore")
class FrontendTests(unittest.TestCase):
    def test_script_parses_and_renders_all_primary_states(self):
        lib = ctypes.CDLL("/System/Library/Frameworks/JavaScriptCore.framework/JavaScriptCore")
        ptr = ctypes.c_void_p
        lib.JSGlobalContextCreate.argtypes = [ptr]
        lib.JSGlobalContextCreate.restype = ptr
        lib.JSStringCreateWithUTF8CString.argtypes = [ctypes.c_char_p]
        lib.JSStringCreateWithUTF8CString.restype = ptr
        lib.JSEvaluateScript.argtypes = [ptr, ptr, ptr, ptr, ctypes.c_int, ctypes.POINTER(ptr)]
        lib.JSEvaluateScript.restype = ptr
        lib.JSValueToStringCopy.argtypes = [ptr, ptr, ctypes.POINTER(ptr)]
        lib.JSValueToStringCopy.restype = ptr
        lib.JSStringGetMaximumUTF8CStringSize.argtypes = [ptr]
        lib.JSStringGetMaximumUTF8CStringSize.restype = ctypes.c_size_t
        lib.JSStringGetUTF8CString.argtypes = [ptr, ptr, ctypes.c_size_t]
        lib.JSStringGetUTF8CString.restype = ctypes.c_size_t
        lib.JSStringRelease.argtypes = [ptr]
        lib.JSGlobalContextRelease.argtypes = [ptr]
        app = (Path(__file__).resolve().parents[1] / "static" / "app.js").read_text()
        app = app.rsplit("\ninit();", 1)[0]
        fixtures = {
            "catalog": catalog(),
            "answers": {r: answers(r) for r in ["fbr", "residence", "spouse"]},
            "results": {r: evaluate(r, answers(r)) for r in ["fbr", "residence", "spouse"]},
        }
        harness = """
        const elements = {};
        function element(key) {
          if (!elements[key]) elements[key] = {
            innerHTML:"", textContent:"", classList:{toggle(){},add(){},remove(){}},
            addEventListener(type,fn){(this.listeners ||= {})[type]=fn;}, focus(){}, showModal(){}, close(){},
            querySelector(s){return element(s)}
          };
          return elements[key];
        }
        const document = {querySelector:element};
        const window = {scrollTo(){}};
        const requestAnimationFrame = f => f();
        function assert(value, message) { if (!value) throw new Error(message); }
        """
        checks = """
        catalog=fixtures.catalog;
        render();
        assert(main.innerHTML.includes('data-route="fbr"'), "Missing family route");
        assert(main.innerHTML.includes('data-route="residence"'), "Missing residence route");
        assert(main.innerHTML.includes('data-route="spouse"'), "Missing partner route");
        for (const route of ["fbr","residence","spouse"]) {
          state={route,answers:fixtures.answers[route],checked:[],stage:"questions",index:0};
          render();
          assert(main.innerHTML.includes("Are you 18 or older?"), "Missing initial question");
          state.stage="review";render();
          assert(main.innerHTML.includes("Build my checklist"), "Missing review action");
          result=fixtures.results[route];state.stage="checklist";render();
          for(const d of result.documents) {
            assert(main.innerHTML.includes('data-document="'+d.id+'"'), "Missing document "+d.id);
            assert(main.innerHTML.includes(catalog.sources[d.source].url), "Missing source");
          }
        }
        state={route:"residence",answers:fixtures.answers.residence,checked:[],selection:{identity:[],years:[]},stage:"checklist",index:0};
        result=fixtures.results.residence; render();
        assert(main.innerHTML.includes("Identity: 150 points once"), "Identity target missing");
        assert(main.innerHTML.includes("Residence: 150 points per year"), "Annual target missing");
        for (const category of ["identity","type_a","type_b","other_residence"]) {
          for (const d of result.scorecard[category]) assert(main.innerHTML.includes(escapeHTML(d.title)), "Missing alternative "+d.title);
        }
        main.querySelectorAll=()=>[];
        main.listeners.change({target:{dataset:{identity:"passport_recent"},checked:true}});
        main.listeners.change({target:{dataset:{identity:"irp_identity"},checked:true}});
        assert(plannedTotals().identity===150, "Alternative identity total incorrect");
        main.listeners.change({target:{dataset:{identity:"passport_valid"},checked:true}});
        assert(state.selection.identity.includes("passport_recent"), "Earlier selection was removed");
        assert(plannedTotals().identity===300, "Above-target total incorrect");
        main.listeners.change({target:{dataset:{identity:"psc"},checked:true}});
        assert(plannedTotals().identity===325 && state.selection.identity.length===4, "Cannot select above target");
        main.listeners.change({target:{dataset:{identity:"passport_valid"},checked:false}});
        assert(plannedTotals().identity===175 && state.selection.identity.includes("passport_recent"), "Unchecking lost other selections");
        main.listeners.change({target:{dataset:{identity:"passport_old"},checked:true}});
        main.listeners.change({target:{dataset:{identity:"driving"},checked:true}});
        assert(plannedTotals().identity===235, "Screenshot selection must total 235");
        assert(identitySelectionNote().includes("Multiple passport categories"), "Passport overlap note missing");
        main.listeners.change({target:{dataset:{year:"0",kind:"b"},value:"rent"}});
        assert(plannedTotals().years[0]===50, "Type B total incorrect");
        main.listeners.change({target:{dataset:{year:"0",kind:"a"},value:"bank"}});
        assert(plannedTotals().years[0]===150 && plannedTotals().years[1]===0, "Years mixed together");
        const exported=pointsText().join("\\n");
        assert(exported.includes("Public Services Card: 25 points"), "Export misses alternatives");
        assert(exported.includes("TYPE B OPTIONS"), "Export misses Type B");
        state={route:"fbr",answers:fixtures.answers.fbr,checked:[],stage:"questions",index:0};
        state.answers.connection="parent_fbr";
        state.answers.parent_before="yes";
        pruneAnswers();
        assert(!("grandparent_alive" in state.answers), "Stale conditional answer retained");
        state.stage="sources";render();
        assert(main.innerHTML.includes("Go straight to the source."), "Sources missing");
        assert(escapeHTML('<img onerror="x">').includes("&lt;"), "Unsafe HTML");
        "ok";
        """
        script = harness + "\n" + app + "\nconst fixtures=" + json.dumps(fixtures) + ";\n" + checks
        context = lib.JSGlobalContextCreate(None)
        source = lib.JSStringCreateWithUTF8CString(script.encode())
        exception = ptr()
        value = lib.JSEvaluateScript(context, source, None, None, 1, ctypes.byref(exception))
        text = lib.JSValueToStringCopy(context, exception.value or value, None)
        size = lib.JSStringGetMaximumUTF8CStringSize(text)
        buffer = ctypes.create_string_buffer(size)
        lib.JSStringGetUTF8CString(text, buffer, size)
        output = buffer.value.decode()
        lib.JSStringRelease(text)
        lib.JSStringRelease(source)
        lib.JSGlobalContextRelease(context)
        self.assertFalse(exception.value, output)
        self.assertEqual(output, "ok")
