"""Board frontend: no innerHTML or external resources, files ship as package data."""
import fnmatch
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path
from unittest.mock import patch

import helpers  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "omi" / "board" / "web"
FILES = ("index.html", "app.css", "app.js", "favicon.svg")
AXE = ROOT / "tests" / "board_screens" / "vendor" / "axe-core-4.11.0"


def test_browser_qa_config() -> None:
    docker = (ROOT / "src/omi/template/docker/Dockerfile").read_text(encoding="utf-8")
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    pins = [re.findall(r"playwright@(\d+\.\d+\.\d+)(?![\w.-])", text) for text in (docker, ci)]
    assert pins[0] == pins[1] and len(pins[0]) == 1, pins
    for text in (docker, ci):
        assert "install --with-deps --only-shell chromium" in text
    for line in ("ENV PLAYWRIGHT_BROWSERS_PATH=/opt/ms-playwright",
                 "ENV NODE_PATH=/usr/local/lib/node_modules", "ENV OMI_BROWSER_REQUIRED=1",
                 f"RUN npm install -g playwright@{pins[0][0]}"):
        assert f"# {line}" in docker  # Opt-in; other projects keep their lean image.
        assert docker.index(line) < docker.index("USER node")
    assert 'OMI_BROWSER_REQUIRED: "1"' in ci
    assert 'node-version: "24.11.0"' in ci
    # This workflow uses two-space indentation: job env is at four spaces,
    # whereas step env is deeper. The runner context is unavailable in job env.
    job_envs = re.findall(r"(?m)^    env:[^\n]*(?:\n(?: {6}[^\n]*|[ \t]*$))*", ci)
    for env in job_envs:
        assert not re.search(r"\$\{\{[^}]*\brunner\s*\.", env), env
    test_step = ci.split("      - name: Run tests\n", 1)[1].split("\n      - ", 1)[0]
    assert "        env:\n          OMI_BOARD_SCREENS: ${{ runner.temp }}/board-screens" in test_step
    assert "if: always()" in ci and "uses: actions/upload-artifact@" in ci
    assert "path: ${{ runner.temp }}/board-screens" in ci
    assert "if-no-files-found: error" in ci


def test_vendored_axe() -> None:
    manifest = AXE / "SHA256SUMS"
    assert manifest.is_file(), f"Missing pinned axe-core vendor files: {AXE}"
    hashes = dict(line.split()[::-1] for line in manifest.read_text(encoding="utf-8").splitlines())
    assert set(hashes) == {"axe.min.js", "LICENSE"}
    for name, expected in hashes.items():
        assert re.fullmatch(r"[0-9a-f]{64}", expected), name
        assert hashlib.sha256((AXE / name).read_bytes()).hexdigest() == expected, name
    assert re.search(r'''version\s*[:=]\s*["']4\.11\.0["']''',
                     (AXE / "axe.min.js").read_text(encoding="utf-8"))
    license_text = (AXE / "LICENSE").read_text(encoding="utf-8")
    assert "Mozilla Public License" in license_text and "2.0" in license_text


def test_files_safe() -> None:
    for name in FILES[:3]:
        text = (WEB / name).read_text(encoding="utf-8")
        assert not re.search(r"https?://|//cdn|@import|@font-face", text), name
    js = (WEB / "app.js").read_text(encoding="utf-8")
    assert not re.search(r"innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(", js)
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'lang="vi"' in html and 'name="viewport"' in html
    assert not re.search(r"<script(?![^>]*\bsrc=)|<style|style=", html)
    assert "@media (min-width: 768px)" in (WEB / "app.css").read_text(encoding="utf-8")


def test_package_data() -> None:
    # setuptools may be absent; check that the package-data globs cover every web file.
    patterns = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["setuptools"]["package-data"]["omi"]
    for name in FILES:
        rel = f"board/web/{name}"
        assert (WEB / name).is_file() and any(fnmatch.fnmatch(rel, p) for p in patterns), name


def test_wheel_ships_web() -> None:
    if subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True).returncode:
        print("skip test_wheel_ships_web: pip missing")
        return
    with tempfile.TemporaryDirectory() as tmp:
        build = Path(tmp) / "source"
        build.mkdir()
        shutil.copy2(ROOT / "pyproject.toml", build)
        shutil.copytree(ROOT / "src", build / "src", ignore=shutil.ignore_patterns("__pycache__"))
        run = subprocess.run([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", tmp],
                             cwd=build, capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        wheel = next(Path(tmp).glob("*.whl"))
        with zipfile.ZipFile(wheel) as archive:
            for name in FILES:
                assert archive.read(f"omi/board/web/{name}") == (WEB / name).read_bytes(), name
        target = Path(tmp) / "installed"
        run = subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(target), str(wheel)],
                             capture_output=True, text=True)
        assert run.returncode == 0, run.stderr
        for name in FILES:
            assert (target / "omi" / "board" / "web" / name).read_bytes() == (WEB / name).read_bytes(), name


def test_app_js_behaviors() -> None:
    js = (WEB / "app.js").read_text(encoding="utf-8")
    for needle in ("Thử lại", "Cập nhật lần cuối", "document.hidden", "pollVersion"):
        assert needle in js, needle
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'role="status"' in html and 'id="refresh"' in html and "Làm mới" in html
    for removed in ("auto-refresh", "countdown", "localStorage", "30000", "Làm mới sau"):
        assert removed not in js + html + (WEB / "app.css").read_text(encoding="utf-8"), removed
    assert "setInterval(pollVersion, 3000)" in js


def test_mockup_layout() -> None:
    css = (WEB / "app.css").read_text(encoding="utf-8")
    # The approved desktop structures and phone adaptation must remain present.
    for cls in ("bar", "brand", "tools", "wrap", "panel", "ph", "stats", "stat", "plan",
                "kanban", "col", "colh", "card", "grid2", "feed", "fi", "po", "poi",
                "projects", "pc", "counts", "layout", "main", "side", "steps", "sn", "crit", "ck"):
        assert re.search(r"\." + cls + r"[\s.{:]", css), cls
    for token in ("#f6f6f4", "#1f2421", "#0f6e6e", "prefers-color-scheme: dark", "max-width:767px",
                  "repeat(2,minmax(0,1fr))", "min(340px,100%)", ":focus-visible", "prefers-reduced-motion",
                  "position:sticky;top:0", "scroll-padding-top:", ".usage-summary", ".merged-empty"):
        assert token in css, token
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'class="skip"' in html and 'href="#main"' in html and '<main ' in html


def test_empty_column_contrast() -> None:
    def luminance(value: str) -> float:
        rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in rgb]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    css = (WEB / "app.css").read_text(encoding="utf-8")
    themes = re.findall(r":root\{([^}]+)", css)
    assert len(themes) == 2  # Light and dark themes.
    for theme in themes:
        colors = dict(re.findall(r"--(empty|column):#([0-9a-f]{6})", theme))
        dark, light = sorted(luminance(colors[key]) for key in ("empty", "column"))
        assert (light + 0.05) / (dark + 0.05) >= 4.5, colors


def test_semantic_palette_and_approved_mockups() -> None:
    css = (WEB / "app.css").read_text(encoding="utf-8")
    def luminance(value: str) -> float:
        rgb = [int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)]
        return sum((v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4) * w
                   for v, w in zip(rgb, (.2126, .7152, .0722)))
    for theme in re.findall(r":root\{([^}]+)", css):
        pairs = dict(re.findall(r"--([a-z]+-(?:fg|bg)):#([a-f0-9]{6})", theme))
        for token in ("planned", "planning", "design", "working", "review", "qa", "po", "blocked", "done",
                      "milestone", "epic", "fr", "nfr", "task"):
            low, high = sorted(luminance(pairs[f"{token}-{suffix}"]) for suffix in ("fg", "bg"))
            assert (high + .05) / (low + .05) >= 4.5, token
    mockups = ROOT / ".omi/tasks/TASK-125-mockup"
    for name in ("projects", "dashboard", "task", "dashboard-phone", "task-phone", "spec"):
        assert (mockups / f"{name}.html").is_file(), name
    assert "max-width:390px" in (mockups / "task-phone.html").read_text(encoding="utf-8")


def test_runtime() -> None:
    node = shutil.which("node")
    if not node:
        print("skip test_runtime: node missing (DOM behavior unverified)")
        return
    run = subprocess.run([node, "-e", RUNTIME_TEST, str(WEB / "app.js")], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    print(run.stdout.strip())


def test_browser_layout_and_keyboard() -> None:
    node = shutil.which("node")
    if not node:
        assert not os.environ.get("OMI_BROWSER_REQUIRED"), "Browser QA required: node missing"
        print("skip test_browser_layout_and_keyboard: node missing")
        return
    # Hook checkouts can be read-only; use the system temp directory for screenshots.
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "OMI_BOARD_SCREENS": os.environ.get("OMI_BOARD_SCREENS") or tmp}
        run = subprocess.run([node, "-e", BROWSER_TEST, str(WEB), str(AXE)],
                             cwd=ROOT, env=env, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    print(run.stdout.strip())


def test_browser_screenshot_directory() -> None:
    for configured in ("", "/ci/board-screens"):
        with patch.dict(os.environ, {"OMI_BOARD_SCREENS": configured}), \
                patch("shutil.which", return_value="node"), patch("subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, stdout="", stderr="")
            test_browser_layout_and_keyboard()
            destination = Path(run.call_args.kwargs["env"]["OMI_BOARD_SCREENS"])
            if configured:
                assert destination == Path(configured)
            else:
                assert not destination.is_relative_to(ROOT), destination
                assert not destination.exists()  # Temporary screenshots are cleaned up.


def test_browser_dependency_policy() -> None:
    with patch("shutil.which", return_value=None), patch.dict(os.environ, {"OMI_BROWSER_REQUIRED": "1"}):
        try:
            test_browser_layout_and_keyboard()
        except AssertionError as exc:
            assert "node missing" in str(exc)
        else:
            raise AssertionError("Required browser checks must fail without node")
    with patch("shutil.which", return_value=None), patch.dict(os.environ, {"OMI_BROWSER_REQUIRED": ""}), patch("builtins.print") as output:
        test_browser_layout_and_keyboard()
        output.assert_called_once_with("skip test_browser_layout_and_keyboard: node missing")
    node = shutil.which("node")
    if not node:
        print("skip test_browser_dependency_policy JS cases: node missing")
        return
    # Simulate unavailable dependencies even on CI workers where they are installed.
    stub = r"""
const Module = require('node:module');
const load = Module._load;
Module._load = function(name, ...args) {
  if(name === 'playwright') {
    if(process.env.OMI_TEST_MISSING === 'chromium')
      return {chromium:{launch:async()=>{throw Error('chromium missing');}}};
    throw Object.assign(Error("Cannot find module '"+process.env.OMI_TEST_MISSING+"'"), {code:'MODULE_NOT_FOUND'});
  }
  return load.call(this, name, ...args);
};
"""
    for missing, required, fails in (("playwright", "", False), ("playwright", "1", True),
                                     ("nested-dependency", "", True), ("chromium", "", True)):
        env = {**os.environ, "OMI_BROWSER_REQUIRED": required, "OMI_TEST_MISSING": missing}
        run = subprocess.run([node, "-e", stub + BROWSER_TEST, str(WEB), str(AXE)],
                             cwd=ROOT, env=env, capture_output=True, text=True)
        assert (run.returncode != 0) == fails, run.stdout + run.stderr
        assert ("skip test_browser" in run.stdout) == (not fails), run.stdout + run.stderr
        assert missing in run.stdout + run.stderr


def main() -> None:
    test_files_safe()
    test_package_data()
    test_wheel_ships_web()
    test_app_js_behaviors()
    test_mockup_layout()
    test_empty_column_contrast()
    test_semantic_palette_and_approved_mockups()
    test_browser_qa_config()
    test_browser_screenshot_directory()
    test_browser_dependency_policy()
    test_runtime()
    # Check the pinned auditor's integrity before evaluating it in the browser.
    test_vendored_axe()
    test_browser_layout_and_keyboard()


API_FIXTURES = r"""
const remoteSource={repo:'https:'+'//github.com/omi-teams/omi-state',sha:'abc123456789',fetched_at:'2026-10-30T12:00:00Z',stale:false};
const frontmatter={title:'<img src=x onerror=evil()>',status:'in-progress',step:'build',plan:'PLAN-006',model:'sonnet',effort:'medium',depends:'TASK-114',workflow:'feature'};
const detail={type:'task',parent:null,children:[],status:'in-progress',phase:{key:'working',label:'Đang làm'},step_index:3,step_count:6,review_round:2,source:remoteSource,id:'TASK-115',frontmatter,goal:'Ship the board',criteria:[{text:'Safe <script> text',checked:true},{text:'Responsive',checked:false}],checkpoint:'Next: review',steps:'- build started',reports:'2026-10-30 14:00 engineer (claude):\n> DONE first\n2026-10-30 15:00 Coordinator (review) FAIL:\n> fix round',usage:{rows:[{role:'engineer',output:'1234',duration:'30s'}],runs:1,review_rounds:0}};
const counts={planned:2,'in-progress':1,review:0,blocked:0,done:4};
const plan={id:'PLAN-006',title:'Board',status:'active',done:4,total:7};
const summary={source:remoteSource,name:'omi',branch:'main',plans:[plan],task_counts:counts,po_waiting_count:1};
const totals={runs:1,input:10,output:1234,cache:5000,review_rounds:0};
const dashboard={...summary,kanban:{planned:[], 'in-progress':[detail],review:[],blocked:[],done:[]},po_waiting:[{id:'TASK-115',reason:'po_gate',text:'accept'}],activity:[{id:'TASK-115',text:'build done',time:'2026-10-30 14:52'}],decisions:['- 2026-10-30: Approved'],usage:{totals,models:{sonnet:totals}}};
const workflowDetail={...detail,current_step:'review',workflow_steps:['plan','design','build','review',{id:'accept',gate:'po'},'qa']};
const crowded={...dashboard,kanban:{...dashboard.kanban,done:Array.from({length:4},(_,i)=>({...detail,id:`TASK-${110+i}`,status:'done',phase:{key:'done',label:'Xong'},frontmatter:{...frontmatter,status:'done'}}))}};
const hierarchy={...crowded,kanban:{...crowded.kanban,'in-progress':[
  {...detail,parent:'FR-001'},
  {...detail,id:'MILESTONE-001',type:'milestone',children:['EPIC-001']},
  {...detail,id:'EPIC-001',type:'epic',parent:'MILESTONE-001',children:['FR-001']},
  {...detail,id:'FR-001',type:'fr',parent:'EPIC-001',children:['TASK-115']}
]}};

"""


RUNTIME_TEST = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.attrs = {}; this.listeners = {}; this.checked = true; this.text = ''; this.style = {}; }
  scrollIntoView() { this.scrolled = true; }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(''); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  getAttribute(k) { return this.attrs[k] ?? null; }
  contains(node) { return all(this).includes(node); }
  querySelectorAll(selector) { return all(this).slice(1).filter(n => selector.split(',').map(s => s.trim()).includes(n.tagName)); }
  get isConnected() { return this === document.body || Object.values(elements).some(root => root.contains(this)); }
  append(...kids) { this.children.push(...kids); }
  replaceChildren(...kids) { this.text = ''; this.children = kids; this.replacements = (this.replacements || 0) + 1; }
  addEventListener(k, f) { this.listeners[k] = f; }
  focus() { document.activeElement = this; }
}
const elements = Object.fromEntries(['view','nav','status','err','refresh','main','source'].map(id => [id,new Element('div')]));
function all(root) { return [root, ...root.children.flatMap(all)]; }
function find(root, cls) { return all(root).filter(n => (n.attrs.class || '').split(' ').includes(cls)); }
const document = {
  body: new Element('body'), hidden:false, listeners:{},
  createElement: tag => new Element(tag),
  getElementById: id => elements[id] || all(elements.view).find(n => n.attrs.id === id),
  addEventListener(k,f) { this.listeners[k]=f; }
};
document.activeElement = document.body;
let interval, intervalMs, calls=0, versionCalls=0, versionSha='abc123456789', fail=false, pending=null;
let now=0;
class Clock extends Date { static now() { return now; } }
const window={scrollY:0,scrolled:null,scrollTo(x,y){this.scrolled=y;},listeners:{},addEventListener(k,f){this.listeners[k]=f;}};
const location={hash:'#/'};
""" + API_FIXTURES + r"""
let data={projects:[summary],source:remoteSource};
let projectData=dashboard;
let timeouts=[];
async function fetch(path,opts) {
  if((location.hash==='#/' || location.hash.includes('/t/')) && path==='/api/projects/omi') return {ok:true,text:async()=>JSON.stringify(projectData)};
  if(path.endsWith('/version')) versionCalls++; else calls++;
  if(pending) return pending(path,opts);
  if(fail) throw Error('offline');
  return {ok:true,text:async()=>JSON.stringify(path.endsWith('/version') ? {sha:versionSha} : data)};
}
const context=vm.createContext({document,window,location,fetch,console,Date:Clock,AbortController,
  setTimeout:(f,ms)=>{const t={f,ms};timeouts.push(t);return t;},clearTimeout:t=>{timeouts=timeouts.filter(x=>x!==t);},
  setInterval:(f,ms)=>{interval=f;intervalMs=ms;return 1;},clearInterval:()=>{interval=null;}});
const source=fs.readFileSync(process.argv[1],'utf8');
vm.runInContext(source,context);
const invoke=code=>vm.runInContext(code,context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function advance(polls) {
  for(let i=0;i<polls;i++) { now+=intervalMs;if(interval) interval();await flush(); }
}
(async()=>{
  assert.equal(elements.view.attrs['aria-busy'],'true');
  assert.equal(elements.refresh.disabled,true);
  assert.equal(find(elements.view,'skeleton').length,1);
  await flush();
  assert.equal(elements.view.attrs['aria-busy'],'false');
  assert.equal(elements.refresh.disabled,false);
  assert.equal(find(elements.view,'pc').length,1);
  assert.equal(find(elements.view,'counts')[0].children.length,5);
  assert.equal(all(elements.view).find(n=>n.tagName==='progress').attrs.value,'4');
  assert(elements.view.textContent.includes('1 dự án'));
  assert(!elements.view.textContent.includes('/state/projects/omi'));
  assert.equal(elements.source.textContent,'github.com/omi-teams/omi-state @ abc1234');
  assert(!elements.view.textContent.includes('✓ Sạch'));
  for(const repo of ['https:'+'//example.org/team/state','ssh:'+'//example.org/team/state.git','example.org:team/state.git']) {
    invoke(`updated({repo:${JSON.stringify(repo)},sha:'def567890',stale:false})`);
    assert.equal(elements.source.textContent,repo.replace(/^[a-z]+:\/\//i,'')+' @ def5678');
  }
  invoke(`updated(${JSON.stringify(remoteSource)})`);
  const unknown=invoke('home([{name:"unknown",plans:[],task_counts:{},po_waiting_count:0}])');
  assert(unknown[1].textContent.includes('Nhánh: Chưa rõ'));
  assert(!unknown[1].textContent.includes('Đồng bộ'));
  assert.equal(intervalMs,3000);
  const original=elements.view.children[0];
  const focused=find(elements.view,'pc')[0];focused.focus();
  const initialCalls=calls;
  const replacements=[elements.view.replacements,elements.nav.replacements,elements.status.replacements];
  await advance(5);
  assert.equal(calls,initialCalls);assert.equal(versionCalls,5);
  assert.deepEqual([elements.view.replacements,elements.nav.replacements,elements.status.replacements],replacements);
  assert.equal(document.activeElement,focused);
  // The matching freshly rendered link gets focus; stale attributes stay on
  // the detached old node rather than leaking into the new render.
  focused.setAttribute('open','stale');
  focused.setAttribute('aria-label','stale label');
  window.scrollY=210;
  versionSha='changed';data={...data,source:{...remoteSource,sha:versionSha}};
  await advance(1);assert.equal(calls,initialCalls+1);
  const newFocused=find(elements.view,'pc')[0];
  assert.notEqual(newFocused,focused);
  assert.equal(document.activeElement,newFocused);
  assert.equal(focused.isConnected,false);
  assert.equal(newFocused.getAttribute('href'),focused.getAttribute('href'));
  assert.equal(newFocused.textContent,focused.textContent);
  assert.equal(newFocused.getAttribute('open'),null);
  assert.equal(newFocused.getAttribute('aria-label'),null);
  assert.equal(window.scrolled,210);
  await advance(2);assert.equal(calls,initialCalls+1);
  assert.equal(elements.status.replacements,replacements[2]+1);
  fail=true;await advance(1);
  assert(elements.err.textContent.includes('Thử lại'));
  const errorReplacements=elements.err.replacements;
  await advance(2);assert.equal(elements.err.replacements,errorReplacements);
  assert.equal(calls,initialCalls+1);
  fail=false;await advance(1);assert.equal(calls,initialCalls+2);assert.equal(elements.err.textContent,'');
  const before=versionCalls;document.hidden=true;document.listeners.visibilitychange();
  assert.equal(interval,null);await advance(60);assert.equal(versionCalls,before);
  document.hidden=false;document.listeners.visibilitychange();await flush();assert.equal(versionCalls,before+1);
  await elements.refresh.listeners.click();assert.equal(calls,initialCalls+3);
  let completeRefresh;
  pending=()=>new Promise(resolve=>{completeRefresh=resolve;});
  const slow=elements.refresh.listeners.click();await advance(5);
  assert.equal(elements.refresh.disabled,true);assert.equal(calls,initialCalls+4);
  assert.equal(versionCalls,before+1);
  pending=null;completeRefresh({ok:true,text:async()=>JSON.stringify(data)});await slow;
  assert.equal(elements.refresh.disabled,false);
  pending=(path,opts)=>new Promise((_,reject)=>opts.signal.addEventListener('abort',()=>reject(Object.assign(Error('aborted'),{name:'AbortError'}))));
  const hung=invoke('pollVersion()');await flush();
  assert.equal(timeouts.length,1);assert.equal(timeouts[0].ms,10000);
  timeouts[0].f();await hung;
  assert(elements.err.textContent.includes('quá thời gian chờ'));
  pending=null;await advance(1);assert.equal(elements.err.textContent,'');
  // With no matching new control, focus stays in the current view context.
  find(elements.view,'pc')[0].focus();
  versionSha='removed';data={projects:[],source:{...remoteSource,sha:versionSha}};
  await advance(1);
  assert.equal(document.activeElement,elements.view);
  assert.equal(find(elements.view,'pc').length,0);
  assert.equal(window.scrolled,210);
  data=dashboard;location.hash='#/p/omi';await invoke('route()');
  assert.equal(find(elements.view,'stat').length,4);
  assert.deepEqual(find(elements.view,'stat').map(n=>find(n,'l')[0].textContent),
    ['Chờ PO','Đang làm · task lá','Bị chặn · task lá','Task lá đã xong']);
  for(const note of ['Chỉ task lá · thứ tự pha cố định · cột trống thu gọn',
    'Trạng thái cha tổng hợp từ con trực tiếp; mở một hàng để xem cấp dưới.'])
    assert(elements.view.textContent.includes(note));
  const blockedLeaf={...detail,id:'TASK-BLOCKED',status:'blocked',children:[]};
  const blockedParent={...blockedLeaf,id:'FR-BLOCKED',type:'fr',children:['TASK-BLOCKED']};
  const blockedStats=invoke(`dashboard('omi',${JSON.stringify({...dashboard,kanban:{blocked:[blockedLeaf,blockedParent]}})})`);
  assert.equal(find(blockedStats[2],'stat')[2].textContent,'1Bị chặn · task lá');
  assert.equal(find(elements.view,'col').length,9);
  assert.equal(find(elements.view,'empty-phases').length,1);
  assert.equal(find(elements.view,'poi').length,1);
  assert.equal(find(elements.view,'card').length,1);
  assert(find(elements.view,'card')[0].textContent.includes(frontmatter.title));
  assert.equal(all(elements.view).filter(n=>n.tagName==='img'||n.tagName==='script').length,0);
  assert.equal(find(elements.view,'card')[0].children[1].attrs.href,'#/p/omi/t/TASK-115');
  for(const text of ['Hoạt động','Quyết định','Sử dụng','abc1234','1.234']) assert(elements.view.textContent.includes(text),text);
  assert(!elements.view.textContent.includes('/state/projects/omi'));
  for(const text of ['✓ Sạch','Trước ','Sau ','Commit cuối']) assert(!elements.view.textContent.includes(text),text);
  assert.equal(find(elements.view,'usage-summary')[0].textContent,'1 lượt · 1.234 output');
  data=crowded;await invoke('route()');
  assert.equal(find(elements.view,'col-done')[0].children.filter(n=>n.tagName==='article').length,4);
  assert.equal(find(elements.view,'card').length,5);
  assert(find(elements.view,'card')[0].textContent.includes('bước 3/6'));
  assert(find(elements.view,'card')[0].textContent.includes('Vòng review: 2'));
  data=dashboard;await invoke('route()');
  const old=elements.view.children[0];data={...dashboard,usage:null};await invoke('route()');
  assert.equal(elements.view.children[0],old);assert(elements.err.textContent);
  // Identical response must retry rendering after a failed render.
  const brokenSeen=invoke('seen');assert.notEqual(brokenSeen,JSON.stringify(data));
  await invoke('route()');assert(elements.err.textContent);
  data=dashboard;await invoke('route()');assert.equal(elements.err.textContent,'');
  data=detail;location.hash='#/p/omi/t/TASK-115';await invoke('route()');
  assert.equal(document.activeElement.attrs.id,'title');
  assert.equal(find(elements.view,'layout').length,1);
  assert.equal(find(elements.view,'main').length,1);assert.equal(find(elements.view,'side').length,1);
  assert.equal(find(elements.view,'ck').length,2);assert.equal(find(elements.view,'checked').length,1);
  const reps=all(elements.view).filter(n=>n.tagName==='details');assert.equal(reps.length,2);
  assert.equal(reps[0].attrs.open,'');assert.equal(reps[1].attrs.open,undefined);
  assert(reps[0].children[0].textContent.startsWith('2026-10-30 15:00 Coordinator (review) FAIL'));
  assert(reps[1].children[0].textContent.includes('engineer (claude)')&&reps[1].children[0].textContent.includes('DONE'));
  assert(elements.view.textContent.includes('Báo cáo (2)'));
  // Background refresh keeps opened reports and the scroll position of the same task page.
  reps[1].open=true;reps[1].listeners.toggle();window.scrollY=420;
  const oldSummary=reps[1].children[0];oldSummary.setAttribute('open','stale');oldSummary.focus();
  data={...detail,goal:'Changed goal'};await invoke('route()');
  const again=all(elements.view).filter(n=>n.tagName==='details');
  assert.equal(again[0].attrs.open,'');assert.equal(again[1].attrs.open,'');assert.equal(window.scrolled,420);
  assert.notEqual(again[1].children[0],oldSummary);
  assert.equal(document.activeElement,again[1].children[0]);
  assert.equal(again[1].children[0].getAttribute('open'),null);
  assert.equal(oldSummary.isConnected,false);
  reps[0].open=false;reps[0].listeners.toggle();data={...detail,goal:'Changed again'};await invoke('route()');
  assert.equal(all(elements.view).filter(n=>n.tagName==='details')[0].attrs.open,undefined);
  data=detail;
  assert.equal(find(elements.view,'steps').length,0);assert(elements.view.textContent.includes('Chưa có định nghĩa quy trình.'));
  data=workflowDetail;await invoke('route()');
  const stepper=find(elements.view,'steps')[0];assert.equal(stepper.children.length,6);
  assert.equal(stepper.children[3].attrs['aria-current'],'step');assert(stepper.textContent.includes('PO duyệt'));
  assert(elements.view.textContent.includes('Bước 4/6'));
  assert.equal(find(stepper,'done').length,3);
  data={...workflowDetail,current_step:'unknown',frontmatter:{...frontmatter,step:'unknown'}};await invoke('route()');
  assert(!elements.view.textContent.includes('Bước 0/'));
  assert(elements.view.textContent.includes('Không xác định bước hiện tại.'));
  assert.equal(find(elements.view,'done').length,0);
  data={...workflowDetail,frontmatter:{...frontmatter,status:'done'}};await invoke('route()');
  assert.equal(find(elements.view,'done').length,6);
  assert.equal(all(find(elements.view,'steps')[0]).filter(n=>n.attrs['aria-current']).length,0);
  assert.equal(find(elements.view,'task-usage').length,1);
  assert(find(elements.view,'task-usage')[0].textContent.includes('Tổng1 lượt · Output: 1.234'));
  assert.equal(find(find(elements.view,'side')[0],'scroll').length,0);
  // Leaf-only totals, direct-child rollup progress, and persistent native disclosures.
  const leaf={...detail,id:'TASK-001',status:'done',frontmatter:{...frontmatter,status:'done'}};
  const parent={...detail,id:'FR-001',type:'fr',parent:'EPIC-001',children:['TASK-001'],status:'done'};
  const epic={...detail,id:'EPIC-001',type:'epic',children:['FR-001'],status:'in-progress'};
  leaf.parent='FR-001';
  data={...dashboard,kanban:{planned:[],done:[leaf,parent], 'in-progress':[epic]}};
  location.hash='#/p/omi';await invoke('route()');
  assert.equal(find(elements.view,'card').length,1);
  assert.equal(find(elements.view,'stat')[3].textContent,'1 / 1Task lá đã xong');
  const tree=find(elements.view,'tree')[0];
  assert.equal(all(tree).filter(n=>n.tagName==='details').length,2);
  assert.equal(all(tree).filter(n=>n.tagName==='details')[1].attrs.open,undefined);
  assert(tree.textContent.includes('tổng hợp'));
  assert.deepEqual(all(tree).filter(n=>n.tagName==='progress').map(n=>n.attrs.value),['1','1']);
  const branch=all(tree).find(n=>n.tagName==='details');
  branch.open=false;branch.listeners.toggle();
  data={...data,decisions:[]};await invoke('route()');
  assert.equal(all(find(elements.view,'tree')[0]).find(n=>n.tagName==='details').attrs.open,undefined);
  const parentPage=invoke(`taskPage('omi','FR-001',${JSON.stringify({...workflowDetail,type:'fr',status:'done',children:['TASK-001'],frontmatter:{...frontmatter,status:'planned'}})})`);
  assert(parentPage[0].textContent.includes('✓ Xong · tổng hợp'));
  assert(parentPage[1].textContent.includes('Quy trình riêng'));
  assert.equal(invoke('stepText({frontmatter:{},step_index:null,step_count:7})'),'bước ?/7 · —');
  // A child-only change must invalidate the combined task/project cache key.
  data={...detail,id:'FR-001'};projectData={...dashboard,kanban:{done:[parent,leaf]}};
  location.hash='#/p/omi/t/FR-001';await invoke('route()');
  assert(elements.view.children[0].textContent.includes('✓ Xong · tổng hợp'));
  const parentView=elements.view.children[0];
  const unchangedDetail=JSON.stringify(data);
  projectData={...dashboard,kanban:{blocked:[{...parent,status:'blocked',type:'nfr'}, {...leaf,status:'blocked'}]}};
  versionSha='child-blocked';await invoke('pollVersion()');
  assert.equal(JSON.stringify(data),unchangedDetail);
  assert.notEqual(elements.view.children[0],parentView);
  assert(elements.view.children[0].textContent.includes('✖ Bị chặn · tổng hợp'));
  assert(elements.view.children[0].textContent.includes('NFR'));
  const refreshedParent=elements.view.children[0];await invoke('route()');
  assert.equal(elements.view.children[0],refreshedParent);
  // Removing the last child also refreshes the parent's derived metadata.
  projectData={...dashboard,kanban:{blocked:[{...parent,status:'blocked',children:[]}]}};
  await invoke('route()');assert(!elements.view.children[0].textContent.includes('tổng hợp'));
  // The same unchanged-primary-response case applies to home leaf counts.
  data={projects:[summary],source:remoteSource};location.hash='#/';
  projectData=dashboard;await invoke('route()');
  const homeView=elements.view.children[0];const unchangedHome=JSON.stringify(data);
  assert.equal(find(elements.view,'counts')[0].children[1].children[0].textContent,'1');
  projectData={...dashboard,kanban:{blocked:[{...detail,status:'blocked'}]}};
  versionSha='home-child-blocked';await invoke('pollVersion()');
  assert.equal(JSON.stringify(data),unchangedHome);
  assert.notEqual(elements.view.children[0],homeView);
  assert.equal(find(elements.view,'counts')[0].children[1].children[0].textContent,'0');
  assert.equal(find(elements.view,'counts')[0].children[3].children[0].textContent,'1');
  const refreshedHome=elements.view.children[0];await invoke('route()');
  assert.equal(elements.view.children[0],refreshedHome);
  projectData=dashboard;
  // Late responses from another route cannot replace the current route.
  let finish;
  pending=()=>new Promise(resolve=>{finish=resolve;});const late=invoke('route()');await flush();
  pending=null;data={projects:[],source:remoteSource};location.hash='#/';await invoke('route()');
  finish({ok:true,text:async()=>JSON.stringify(detail)});await late;
  assert(elements.view.textContent.includes('Chưa có dự án.'));
  data={projects:[summary],source:remoteSource};await elements.refresh.listeners.click();assert.equal(find(elements.view,'pc').length,1);
  data={...dashboard,po_waiting:[],plans:[],activity:[],decisions:[]};location.hash='#/p/omi';await invoke('route()');
  for(const text of ['Không có việc chờ PO.','Chưa có kế hoạch.','Chưa có hoạt động.','Chưa có quyết định.']) assert(elements.view.textContent.includes(text));
  data={...data,source:{...remoteSource,stale:true}};await invoke('route()');
  assert(elements.err.textContent.startsWith('Dữ liệu cũ - không kết nối được GitHub (lúc '));
  await invoke('route()');assert(elements.err.textContent.startsWith('Dữ liệu cũ - không kết nối được GitHub'));
  data={...data,source:remoteSource};await invoke('route()');assert.equal(elements.err.textContent,'');
  fail=true;location.hash='#/p/missing';await invoke('route()');
  assert(elements.err.textContent.includes('Thử lại'));
  assert.equal(find(elements.view,'skeleton').length,0);
  assert.equal(elements.view.textContent,'missing');
  // Cost page: text only, tokens-only note without prices, badges not by colour alone.
  const row=(o)=>({input:10,output:5,cache:1,runs:2,tokens:16,cost:null,review_rounds:3,fails:0,top:null,...o});
  const costData={has_prices:false,tasks:[row({id:'TASK-1',title:'<b>x</b>',plan:'P',tool:'claude',model:'m',top:1,fails:2})],
    plans:[row({plan:'P'})],tools:[row({tool:'claude'})],models:[row({model:'m'})],totals:row({})};
  const page=invoke(`costPage('omi',${JSON.stringify(costData)})`);
  const pageText=page.map(n=>n.textContent).join('|');
  assert(pageText.includes('Chỉ hiển thị token'));assert(!pageText.includes('US$'));
  assert(pageText.includes('↑ Top 1')&&pageText.includes('✕ 2 lần FAIL')&&pageText.includes('<b>x</b>'));
  assert.equal(find(page[page.length-4],'hatch').length,2);  // legend swatch + the Top 1 bar
  assert(pageText.includes('P · claude / m')&&pageText.includes('chỉ đọc')&&pageText.includes('Các task còn lại'));
  assert.equal(find(page[1],'btn').length,4);
  find(page[1],'btn')[1].listeners.click();
  const priced=invoke(`costPage('omi',${JSON.stringify({...costData,has_prices:true,totals:row({cost:null})})})`).map(n=>n.textContent).join('|');
  assert(priced.includes('Thiếu giá')&&priced.includes('chưa đủ giá'));
  console.log('ok: API views, mockup DOM, safe text, version changes/unchanged/hidden, polling, recovery, focus, races');
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


BROWSER_TEST = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
let chromium;
try { ({chromium}=require('playwright')); }
catch(e) {
  if(process.env.OMI_BROWSER_REQUIRED || e.code!=='MODULE_NOT_FOUND' ||
     !e.message.startsWith("Cannot find module 'playwright'")) throw e;
  console.log('skip test_browser_layout_and_keyboard: playwright missing (layout, keyboard, axe and print unverified)');
  process.exit(0);
}
""" + API_FIXTURES + r"""
(async()=>{
  // If Playwright is installed, a missing browser is a test failure, not a silent skip.
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage({colorScheme:'light'});
    const axeSource=fs.readFileSync(path.join(process.argv[2],'axe.min.js'),'utf8');
    const screens=process.env.OMI_BOARD_SCREENS;
    if(screens) fs.mkdirSync(screens,{recursive:true});
    async function audit(label) {
      // Theme changes transition link colors/backgrounds for 200ms. Audit the
      // settled theme rather than a mixture of old and new palette values.
      await page.evaluate(()=>Promise.all(document.getAnimations().map(animation=>animation.finished)));
      const violations=await page.evaluate(async()=>{
        const results=await axe.run(document,{resultTypes:['violations']});
        return results.violations.filter(v=>['serious','critical'].includes(v.impact));
      });
      // Finish the page/width matrix so CI also retains evidence for later pages
      // when an accessibility violation is found on an earlier page.
      for(const violation of violations)
        errors.push(`axe ${label}: ${violation.id} (${violation.impact}): ${violation.nodes.map(n=>n.html).join(', ')}`);
    }
    const row=(o)=>({input:100,output:50,cache:50,runs:2,tokens:200,cost:1.5,review_rounds:3,fails:0,top:null,...o});
    const tasks=[row({id:'TASK-1',title:'A',plan:'P1',tool:'claude',model:'m',tokens:400,cost:3,top:1,fails:2}),row({id:'TASK-2',title:'B',plan:'P1',tool:'codex',model:'n',cost:null,top:2})];
    const base={name:'omi',tasks,plans:[row({plan:'P1',tokens:600})],tools:[row({tool:'claude',tokens:400}),row({tool:'codex'})],models:[row({model:'m',tokens:400}),row({model:'n'})]};
    const costFixture={priced:{...base,has_prices:true,tasks:[tasks[0],{...tasks[1],cost:1.5}],totals:row({tokens:600,cost:4.5})},
      tokens:{...base,has_prices:false,tasks:tasks.map(t=>({...t,cost:null})),totals:row({tokens:600,cost:null})},
      partial:{...base,has_prices:true,totals:row({tokens:600,cost:null})}};
    let costMode='priced';
    const errors=[];page.on('pageerror', e=>errors.push(e.message));
    page.on('console', msg=>{if(msg.type()==='error') errors.push(msg.text());});
    await page.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if(url.origin!=='http://omi.test' || route.request().method()!=='GET') {
        errors.push(`Unexpected request: ${route.request().method()} ${url}`);
        return route.abort();
      }
      if(url.pathname.startsWith('/api/')) {
        if(url.pathname==='/api/projects/omi/cost') return route.fulfill({json:{...costFixture[costMode],source:remoteSource}});
        const data=url.pathname.endsWith('/version')?{sha:remoteSource.sha}:url.pathname.endsWith('/tasks/TASK-115')?workflowDetail:url.pathname==='/api/projects/omi'?hierarchy:{projects:[summary],source:remoteSource};
        return route.fulfill({json:data});
      }
      const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      const types={'index.html':'text/html','app.css':'text/css','app.js':'application/javascript','favicon.svg':'image/svg+xml'};
      assert(types[name],name);
      await route.fulfill({body:fs.readFileSync(path.join(process.argv[1],name)),contentType:types[name],
        headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'"}});
    });
    for(const width of [320,360,390,768,1280]) {
      await page.setViewportSize({width,height:900});
      for(const hash of ['#/','#/p/omi','#/p/omi/t/TASK-115']) {
        await page.goto(`http://omi.test/?width=${width}&page=${encodeURIComponent(hash)}${hash}`);
        await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
        assert.equal(await page.locator('h1').count(),1);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width} ${hash}`);
        assert.equal(await page.locator('[style]').count(),0);
        assert.equal(await page.locator('#view script, #view img').count(),0);
        const pageName=hash==='#/'?'projects':hash.includes('/t/')?'task':'dashboard';
        if(screens) await page.screenshot({path:path.join(screens,`${pageName}-${width}.png`),fullPage:true});
        // Inject the vendored auditor through automation; the app still uses its strict CSP.
        await page.evaluate(axeSource);
        await audit(`${pageName} ${width} light`);
        const header=await page.locator('.top').boundingBox();
        assert.equal(await page.locator('#countdown, #auto, .switch').count(),0);
        assert(await page.getByRole('button',{name:'Làm mới',exact:true}).isVisible());
        assert.equal(await page.locator('.top').evaluate(n=>getComputedStyle(n).position),'sticky');
        assert(await page.locator('html').evaluate(n=>parseFloat(getComputedStyle(n).scrollPaddingTop))>header.height);
        // The timestamp wraps onto its own line on phones.
        if(width<768) assert(header.height<160,`compact phone header ${width} ${hash}: ${header.height}px`);
        if(hash==='#/p/omi') {
          const columns=await page.locator('.col:visible').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().x));
          assert.equal(new Set(columns).size,width<768?1:2);
          assert.equal(columns.length,2);
          assert.equal(await page.locator('.col-done .card:visible').count(),4);
          const parent=page.locator('.tree details').first();
          const summary=parent.locator(':scope > summary');
          assert.equal(await parent.getAttribute('open'),'');
          await summary.focus();await page.keyboard.press('Space');
          assert.equal(await parent.getAttribute('open'),null);
          await page.evaluate(()=>{seen=null;return route();});
          assert.equal(await page.locator('.tree details').first().getAttribute('open'),null);
          await page.locator('.tree details>summary').first().focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('.tree details').first().getAttribute('open'),'');
          assert.equal(await page.locator('.tree progress').first().getAttribute('max'),'1');
          const empty=page.locator('.empty-phases>summary');
          await empty.focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('.col:visible').count(),9);
          await page.keyboard.press('Enter');
          assert.equal(await page.locator('.col:visible').count(),2);
        }
        // Native keyboard controls and the skip link must work in the real DOM.
        await page.locator('.skip').focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.evaluate(()=>document.activeElement.id),'main');
        assert((await page.locator('#main').boundingBox()).y>=(await page.locator('.top').boundingBox()).height,'skip target clears header');
        await page.locator('#refresh').focus();
        await page.keyboard.press('Enter');
        await page.waitForFunction(()=>!document.getElementById('refresh').disabled);
        // An unchanged poll preserves all nodes and the timestamp; a changed
        // revision reloads the view and focuses the matching freshly rendered control.
        const target=page.locator(hash==='#/'?'.pc':hash.includes('/t/')?'details summary':'.card a').first();
        await target.focus();
        await target.evaluate(n=>{window.savedControl=n;window.savedView=document.getElementById('view').firstChild;window.savedStatus=document.getElementById('status').firstChild;});
        await page.evaluate(()=>pollVersion());
        assert(await page.evaluate(()=>window.savedView===document.getElementById('view').firstChild && window.savedStatus===document.getElementById('status').firstChild));
        remoteSource.sha=`change-${width}-${pageName}`;
        await page.evaluate(()=>pollVersion());
        assert(await page.evaluate(()=>window.savedView!==document.getElementById('view').firstChild));
        assert(await page.evaluate(()=>{
          const focused=document.activeElement;
          return window.savedControl!==focused && !window.savedControl.isConnected && focused.isConnected &&
            focused.tagName===window.savedControl.tagName && focused.getAttribute('href')===window.savedControl.getAttribute('href') &&
            focused.textContent===window.savedControl.textContent;
        }));
        const initial=await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor);
        await page.emulateMedia({colorScheme:'dark'});
        assert.notEqual(await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor),initial);
        await audit(`${pageName} ${width} dark`);
        await page.emulateMedia({colorScheme:'light'});
        if(hash.includes('/t/')) {
          assert.equal(await page.getByRole('img',{name:'Xong',exact:true}).count(),1);
          assert.equal(await page.getByRole('img',{name:'Chưa',exact:true}).count(),1);
          assert.equal(await page.locator('.steps li').count(),6);
          assert.deepEqual(await page.locator('.steps [aria-current="step"] .sn').allTextContents(),['4']);
          assert(await page.locator('#view').innerText().then(text=>text.includes('Bước 4/6')));
          assert.equal(await page.locator('details').first().getAttribute('open'),'');
          const marker=()=>page.locator('details summary').first().evaluate(n=>getComputedStyle(n,'::before').content);
          assert.equal(await marker(),'"▾"');
          await page.locator('summary').first().focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('details').first().getAttribute('open'),null);
          assert.equal(await marker(),'"▸"');
        }
        if(pageName!=='projects') {
          assert(await page.locator('#refresh').isVisible());
          await page.emulateMedia({media:'print'});
          for(const selector of ['.tools','#refresh','#auto','#countdown','#status','.skip'])
            assert.equal(await page.locator(selector).isVisible(),false,`print ${pageName} ${width} ${selector}`);
          assert.equal(await page.locator('.top').evaluate(n=>getComputedStyle(n).position),'static');
          assert(await page.locator('h1').isVisible());
          assert(await page.locator('#view').innerText().then(text=>text.includes(frontmatter.title)));
          await page.emulateMedia({media:'screen'});
          assert(await page.locator('#refresh').isVisible());
        }
      }
    }
    for(const mode of ['priced','tokens','partial']) {
      costMode=mode;
      for(const width of [320,390,1280]) {
        await page.setViewportSize({width,height:900});
        await page.goto(`http://omi.test/?cost=${mode}&width=${width}#/p/omi/cost`);
        await page.locator('.cost-stats').waitFor();
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow cost ${mode} ${width}`);
        // Bars come from the CSSOM (the CSP blocks style attributes) and stay proportional.
        const widths=await page.locator('.panel').first().locator('.bar-f').evaluateAll(n=>n.map(b=>Math.round(b.getBoundingClientRect().width/b.parentElement.clientWidth*100)));
        assert.deepEqual(widths,[100,50],`bar widths ${mode} ${width}`);
        const text=await page.locator('#view').innerText();
        assert.equal(text.includes('Chỉ hiển thị token'),mode==='tokens');
        assert.equal(text.includes('Thiếu giá'),mode==='partial');
        assert.equal(await page.locator('.panel').first().locator('caption').evaluate(n=>n.getBoundingClientRect().height<60),true,`caption wrap ${mode} ${width}`);
        await page.getByRole('button',{name:'Theo model',exact:true}).click();
        await page.evaluate(axeSource);
        await audit(`cost ${mode} ${width} light`);
        await page.emulateMedia({colorScheme:'dark'});
        await audit(`cost ${mode} ${width} dark`);
        await page.emulateMedia({colorScheme:'light'});
      }
    }
    if(screens) {
      for(const name of ['projects','dashboard','task']) for(const width of [320,360,390,768,1280])
        assert(fs.statSync(path.join(screens,`${name}-${width}.png`)).size>0);
    }
    assert.deepEqual(errors,[]);
    console.log('ok: browser layouts at 320/360/390/768/1280px, sticky header, phone summaries, overflow disclosure, dark mode, CSP, keyboard controls, axe (light/dark), print, GET-only requests');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


if __name__ == "__main__":
    main()
