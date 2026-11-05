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
SCRIPTS = ("dom.js", "tree.js", "dashboard.js", "task.js", "inbox.js", "graph.js", "app.js")
FILES = ("index.html", "app.css", *SCRIPTS, "favicon.svg")


def app_js() -> str:
    return "\n".join((WEB / name).read_text(encoding="utf-8") for name in SCRIPTS)
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
    for name in ("index.html", "app.css", *SCRIPTS):
        text = (WEB / name).read_text(encoding="utf-8")
        assert not re.search(r"https?://|//cdn|@import|@font-face", text), name
    js = app_js()
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
    js = app_js()
    for needle in ("Thử lại", "Cập nhật lần cuối", "document.hidden", "pollVersion"):
        assert needle in js, needle
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert re.findall(r'<script src="([^"]+)"', html) == list(SCRIPTS)
    for name in SCRIPTS:
        assert len((WEB / name).read_text(encoding="utf-8").splitlines()) < 600, name
    assert 'role="status"' in html and 'id="refresh"' in html and "Làm mới" in html
    for removed in ("auto-refresh", "countdown", "30000", "Làm mới sau"):
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
                      "milestone", "epic", "fr", "nfr", "task", "bug", "security", "incident", "change", "spike", "chore"):
            low, high = sorted(luminance(pairs[f"{token}-{suffix}"]) for suffix in ("fg", "bg"))
            assert (high + .05) / (low + .05) >= 4.5, token
    js = app_js()
    for label in ("Bug", "Security", "Incident", "Change", "Spike", "Chore"):
        assert f'{label.lower()}: "{label}"' in js and f".chip.{label.lower()}{{" in css, label
    mockups = ROOT / ".omi/tasks/TASK-125-mockup"
    for name in ("projects", "dashboard", "task", "dashboard-phone", "task-phone", "spec"):
        assert (mockups / f"{name}.html").is_file(), name
    assert "max-width:390px" in (mockups / "task-phone.html").read_text(encoding="utf-8")


def run_node(node: str, script: str, *args: str, **kwargs) -> subprocess.CompletedProcess:
    # Scripts go through stdin: `node -e` hits the Windows command-line length limit.
    return subprocess.run([node, "-", *args], input="process.argv.splice(1, 1);" + script,
                          capture_output=True, text=True, encoding="utf-8", errors="replace", **kwargs)


def test_runtime() -> None:
    node = shutil.which("node")
    if not node:
        print("skip test_runtime: node missing (DOM behavior unverified)")
        return
    run = run_node(node, RUNTIME_TEST, str(WEB), *SCRIPTS)
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
        run = run_node(node, BROWSER_TEST, str(WEB), str(AXE), cwd=ROOT, env=env)
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
        run = run_node(node, stub + BROWSER_TEST, str(WEB), str(AXE), cwd=ROOT, env=env)
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
const tlRound=(n,role,stamp,verdict,body,open=false)=>({n,role,stamp,verdict,body,open});
const tlRows=[{kind:'step',name:'plan',start:'2026-11-02 16:29',end:'2026-11-02 16:29',state:'done',seconds:0,duration:'0 giây',percent:0,po:false,fail:false,rounds:[]},
  {kind:'step',name:'approve-mockup',start:'2026-11-02 16:39',end:'2026-11-02 16:41',state:'done',seconds:123,duration:'2 phút 3 giây',percent:7,po:true,fail:false,rounds:[]},
  {kind:'step',name:'build',start:'2026-11-02 16:41',end:'2026-11-02 17:46',state:'done',seconds:3900,duration:'1 giờ 5 phút',percent:100,po:false,fail:false,rounds:[tlRound(1,'engineer','2026-11-02 17:45','DONE','DONE\nFiles: <b>x</b>')]},
  {kind:'step',name:'review',start:'2026-11-02 17:46',end:'2026-11-02 18:11',state:'done',seconds:1480,duration:'24 phút 40 giây',percent:38,po:false,fail:true,rounds:[tlRound(1,'reviewer','2026-11-02 18:01','FAIL','FAIL\nfile:line - bug',true),tlRound(2,'reviewer','2026-11-02 18:10','PASS','PASS')]},
  {kind:'note',text:'Auto accept: review PASS',start:'2026-11-02 18:11'},
  {kind:'step',name:'qa',start:'2026-11-02 18:11',end:null,state:'running',seconds:760,duration:'12 phút 40 giây',percent:20,po:false,fail:false,rounds:[]}];
const timelineDetail={...workflowDetail,steps:'- plan started 2026-11-02 16:29',files:['src/omi/board/web/app.js','tests/test_board_web.py','README.md'],
  timeline:{rows:tlRows,now:'18:23',summary:{seconds:6286,duration:'1 giờ 44 phút',steps:5,done:4,running:1,rounds:3,fails:1}}};
const noFilesDetail={...timelineDetail,files:[]};
const noStepsDetail={...workflowDetail,steps:'',files:[],timeline:{rows:[],now:'18:23',summary:{seconds:0,duration:'0 giây',steps:0,done:0,running:0,rounds:0,fails:0}}};
const crowded={...dashboard,kanban:{...dashboard.kanban,done:Array.from({length:4},(_,i)=>({...detail,id:`TASK-${110+i}`,status:'done',phase:{key:'done',label:'Xong'},frontmatter:{...frontmatter,status:'done'}}))}};
const hierarchy={...crowded,kanban:{...crowded.kanban,'in-progress':[
  {...detail,parent:'FR-001'},
  {...detail,id:'MILESTONE-001',type:'milestone',children:['EPIC-001']},
  {...detail,id:'EPIC-001',type:'epic',parent:'MILESTONE-001',children:['FR-001']},
  {...detail,id:'FR-001',type:'fr',parent:'EPIC-001',children:['TASK-115']}
]}};
const inboxFixture=['po_gate','po_gate','needs_scope','quota','review_fail'].map((reason,index)=>({
  project:index===1?'other':'omi',id:`TASK-${115+index}`,title:index===0?frontmatter.title:'Yêu cầu PO quyết định',
  reason,...(reason==='po_gate'?{gate:index===0?'accept':'approve-mockup'}:{}),text:reason==='po_gate'?'Duyệt bước accept':'Cần PO quyết định; xem chi tiết task.',
  since:index===4?null:`2026-11-01 1${index}:00`,command:`omi-task TASK-${115+index}`}));


"""


RUNTIME_TEST = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
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
const elements = Object.fromEntries(['view','nav','status','err','refresh','main','source','inbox-count'].map(id => [id,new Element('div')]));
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
const window={isSecureContext:true,localStorage:{getItem:()=>null,setItem:()=>{}},scrollY:0,scrolled:null,scrollTo(x,y){this.scrolled=y;},listeners:{},addEventListener(k,f){this.listeners[k]=f;}};
const location={hash:'#/',get href(){return 'http:'+'//omi.test/'+this.hash;}};
window.history={pushState:(_state,_title,hash)=>{location.hash=hash;},replaceState:(_state,_title,hash)=>{location.hash=hash;}};
""" + API_FIXTURES + r"""
let data={projects:[summary],source:remoteSource};
let projectData=dashboard;
let globalInbox=[];
let timeouts=[];
async function fetch(path,opts) {
  if(path==='/api/projects' && location.hash.startsWith('#/p/')) return {ok:true,text:async()=>JSON.stringify({projects:[summary],source:data.source || remoteSource,inbox:globalInbox})};
  if((location.hash==='#/' || location.hash.includes('/t/')) && path==='/api/projects/omi') return {ok:true,text:async()=>JSON.stringify(projectData)};
  if(path.endsWith('/version')) versionCalls++; else calls++;
  if(pending) return pending(path,opts);
  if(fail) throw Error('offline');
  return {ok:true,text:async()=>JSON.stringify(path.endsWith('/version') ? {sha:versionSha} : data)};
}
const context=vm.createContext({document,window,location,fetch,console,Date:Clock,AbortController,
  setTimeout:(f,ms)=>{const t={f,ms};timeouts.push(t);return t;},clearTimeout:t=>{timeouts=timeouts.filter(x=>x!==t);},
  setInterval:(f,ms)=>{interval=f;intervalMs=ms;return 1;},clearInterval:()=>{interval=null;}});
for(const name of process.argv.slice(2)) vm.runInContext(fs.readFileSync(path.join(process.argv[1],name),'utf8'),context,{filename:name});
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
  const mk=(id,status,title,extra={})=>({...detail,id,status,frontmatter:{title,status,...extra}});
  const weekly={...dashboard,kanban:{planned:[mk('TASK-4','planned','Việc kế tiếp',{depends:'TASK-1'}),mk('TASK-5','planned','Chờ việc khác',{depends:'TASK-3'})],
    'in-progress':[mk('TASK-3','in-progress','Đang\nlàm')],review:[],blocked:[mk('TASK-6','blocked','Bị kẹt')],
    done:[mk('TASK-1','done','Xong tuần này'),mk('TASK-2','done','Xong tháng trước')]},
    activity:[{id:'TASK-1',time:'2026-11-01 10:00',text:'x'},{id:'TASK-2',time:'2026-09-01 10:00',text:'y'}],
    decisions:['- 2026-11-02: Chọn A','- 2026-09-01: Cũ']};
  const cost={has_prices:true,totals:{input:10,output:1234,cache:5000,runs:3,cost:1.5}};
  window.weekly=[weekly,cost];
  const md=invoke('weeklyReport("omi",window.weekly[0],window.weekly[1],new Date("2026-11-03T00:00:00Z"))');
  assert.equal(md,`# Báo cáo tuần: omi

Từ 2026-10-27 đến 2026-11-03

## Việc đã xong
- TASK-1: Xong tuần này

## Đang làm
- TASK-3: Đang làm

## Bị chặn
- TASK-6: Bị kẹt

## Quyết định
- 2026-11-02: Chọn A

## Token và chi phí (toàn dự án)
- Token vào: 10; ra: 1.234; cache: 5.000; lượt chạy: 3
- Chi phí: ≈ US$1,50

## Việc kế tiếp
- TASK-4: Việc kế tiếp
`);
  assert(invoke('weeklyReport("omi",{kanban:{},activity:[],decisions:[]},{totals:{}},new Date())').includes('## Bị chặn\n- Không có.'));
  assert(find(invoke('dashboard("omi",window.weekly[0])')[0],'chips')[0].children.some(n=>n.textContent==='Tải báo cáo tuần'));
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
  assert.equal(find(elements.view,'col-done')[0].tagName,'details');
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
  const reps=all(elements.view).filter(n=>n.tagName==='details'&&!(n.attrs.class||'').includes('raw'));assert.equal(reps.length,2);
  assert.equal(reps[0].attrs.open,'');assert.equal(reps[1].attrs.open,undefined);
  assert(reps[0].children[0].textContent.startsWith('2026-10-30 15:00 Coordinator (review) FAIL'));
  assert(reps[1].children[0].textContent.includes('engineer (claude)')&&reps[1].children[0].textContent.includes('DONE'));
  assert(elements.view.textContent.includes('Báo cáo (2)'));
  // Background refresh keeps opened reports and the scroll position of the same task page.
  reps[1].open=true;reps[1].listeners.toggle();window.scrollY=420;
  const oldSummary=reps[1].children[0];oldSummary.setAttribute('open','stale');oldSummary.focus();
  data={...detail,goal:'Changed goal'};await invoke('route()');
  const again=all(elements.view).filter(n=>n.tagName==='details'&&!(n.attrs.class||'').includes('raw'));
  assert.equal(again[0].attrs.open,'');assert.equal(again[1].attrs.open,'');assert.equal(window.scrolled,420);
  assert.notEqual(again[1].children[0],oldSummary);
  assert.equal(document.activeElement,again[1].children[0]);
  assert.equal(again[1].children[0].getAttribute('open'),null);
  assert.equal(oldSummary.isConnected,false);
  reps[0].open=false;reps[0].listeners.toggle();data={...detail,goal:'Changed again'};await invoke('route()');
  assert.equal(all(elements.view).filter(n=>n.tagName==='details'&&!(n.attrs.class||'').includes('raw'))[0].attrs.open,undefined);
  data=detail;
  assert.equal(find(elements.view,'steps').length,0);assert(elements.view.textContent.includes('Chưa có định nghĩa quy trình.'));
  data=workflowDetail;await invoke('route()');
  const stepper=find(elements.view,'steps')[0];assert.equal(stepper.children.length,6);
  assert.equal(stepper.children[3].attrs['aria-current'],'step');assert(stepper.textContent.includes('PO duyệt'));
  assert(elements.view.textContent.includes('Bước 4/6'));
  assert.equal(find(stepper,'done').length,3);
  // TASK-132: timeline rows, review rounds, changed files and the empty state.
  data=timelineDetail;await invoke('route()');
  const tl=find(elements.view,'tl')[0];assert.equal(tl.tagName,'ol');assert.equal(tl.children.length,6);
  const tlText=tl.children.map(n=>n.textContent);
  assert(tlText[0].startsWith('02/11 · 16:29')&&tlText[0].includes('plan')&&tlText[0].includes('0 giây'));
  assert(tlText[1].includes('◇ PO duyệt')&&tlText[1].includes('2 phút 3 giây'));
  assert(tlText[3].includes('✕ Có vòng FAIL')&&tlText[3].includes('Vòng 2')&&tlText[3].includes('reviewer · 18:10'));
  assert(tlText[4].includes('Auto accept: review PASS'));
  assert(tlText[5].includes('● Đang chạy')&&tlText[5].includes('đang chạy · 12 phút 40 giây')&&tlText[5].includes('Tính đến 18:23'));
  const rounds=all(tl).filter(n=>n.tagName==='details');assert.equal(rounds.length,3);
  assert.equal(rounds[0].attrs.open,undefined);assert.equal(rounds[1].attrs.open,'');assert.equal(rounds[2].attrs.open,undefined);
  assert(rounds[0].textContent.includes('<b>x</b>'));assert.equal(all(tl).filter(n=>n.tagName==='b').length,0);
  assert.equal(all(tl).filter(n=>n.tagName==='progress'&&n.attrs['aria-hidden']==='true').length,4);
  assert.equal(find(tl,'mk').filter(n=>n.attrs.class.includes('memo'))[0].attrs['aria-hidden'],'true');
  const raw=find(elements.view,'raw')[0];assert.equal(raw.tagName,'details');assert.equal(raw.attrs.open,undefined);assert(raw.children[0].textContent==='Văn bản gốc');
  assert(elements.view.textContent.includes('Tệp đã đổi · 3')&&elements.view.textContent.includes('Ghi bởi omi step'));
  const tx=elements.view.textContent;assert(tx.indexOf('Dòng thời gian')<tx.indexOf('Tệp đã đổi')&&tx.indexOf('Tệp đã đổi')<tx.indexOf('Văn bản gốc'));
  const fileItems=find(elements.view,'files')[0].children;assert.equal(fileItems[0].children[0].textContent,'src/omi/board/web/');assert.equal(fileItems[0].children[1].textContent,'app.js');
  assert.equal(fileItems[2].children[0].textContent,'');assert.equal(fileItems[2].children[1].textContent,'README.md');
  data=noFilesDetail;await invoke('route()');assert(!elements.view.textContent.includes('Tệp đã đổi'));assert.equal(find(elements.view,'tl').length,1);
  data={...noFilesDetail,files:undefined};await invoke('route()');assert(!elements.view.textContent.includes('Tệp đã đổi'));
  data=noStepsDetail;await invoke('route()');assert.equal(find(elements.view,'tl').length,0);
  assert(elements.view.textContent.includes('Chưa có bước nào được ghi'));assert.equal(find(elements.view,'raw').length,1);
  data=workflowDetail;await invoke('route()');assert(elements.view.textContent.includes('Chưa có bước nào được ghi'));
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
  assert.equal(all(tree).filter(n=>n.tagName==='details').length,3);
  assert.equal(all(tree).filter(n=>n.tagName==='details')[1].attrs.open,undefined);
  assert.equal(all(tree).filter(n=>n.tagName==='details')[2].children[0].textContent,'1 task đã xong');
  assert.equal(find(elements.view,'tree-block')[0].attrs.open,'');
  assert.equal(find(elements.view,'col-done')[0].attrs.open,undefined);assert.equal(find(elements.view,'col-planned').length,0);
  assert(tree.textContent.includes('tổng hợp'));
  assert.deepEqual(all(tree).filter(n=>n.tagName==='progress').map(n=>n.attrs.value),['1','1']);
  const leaf2={...leaf,id:'TASK-002',parent:'FR-002'};
  const parent2={...parent,id:'FR-002',children:['TASK-002']};
  const epic2={...epic,children:['FR-001','FR-002']};
  const two=invoke(`taskTree('omi',${JSON.stringify([epic2,parent,parent2,leaf,leaf2])})`);
  const groups=all(two).filter(n=>n.tagName==='details'&&n.children[0].textContent.endsWith('task đã xong'));
  assert.equal(groups.length,1);assert.equal(groups[0].children[0].textContent,'2 task đã xong');assert.equal(groups[0].attrs.open,undefined);
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
  assert(!elements.view.textContent.includes('Cảnh báo sức khỏe'));
  data={...data,alerts:[{id:'TASK-118',title:'<b>x</b>',kind:'stale',chip:'Không hoạt động',reason:'5 ngày (ngưỡng: 3 ngày).',action:'Hỏi agent.'}]};await invoke('route()');
  assert(elements.view.textContent.includes('Cảnh báo sức khỏe (1)'));
  assert(elements.view.textContent.includes('<b>x</b>') && elements.view.textContent.includes('Việc nên làm: Hỏi agent.'));
  assert.equal(find(elements.view,'alert').length,1);
  data={...data,alerts:[]};await invoke('route()');
  data={...data,source:{...remoteSource,stale:true}};await invoke('route()');
  assert(elements.err.textContent.startsWith('Dữ liệu cũ - không kết nối được GitHub (lúc '));
  await invoke('route()');assert(elements.err.textContent.startsWith('Dữ liệu cũ - không kết nối được GitHub'));
  data={...data,source:remoteSource};await invoke('route()');assert.equal(elements.err.textContent,'');
  fail=true;location.hash='#/p/missing';await invoke('route()');
  assert(elements.err.textContent.includes('Thử lại'));
  assert.equal(find(elements.view,'skeleton').length,0);
  assert(elements.view.textContent.includes('missing'));
  assert.equal(document.getElementById('board-search').disabled,true);
  assert(elements.view.textContent.includes('Bộ lọc khả dụng sau khi tải dữ liệu.'));
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

  // Inbox baseline, click-only permission, stable identity, and copy fallbacks.
  fail=false;
  let permissionRequests=0, notices=[], copied=[];
  window.Notification=class {
    static permission='default';
    static async requestPermission(){permissionRequests++;this.permission='granted';return 'granted';}
    constructor(title,options){this.title=title;this.options=options;notices.push(this);}
    close(){}
  };
  window.navigator={clipboard:{writeText:async text=>copied.push(text)}};
  window.focus=()=>{window.focused=true;};
  const item={project:'omi',id:'TASK-115',title:'<img src=x onerror=evil()>',reason:'po_gate',since:'2026-11-01 12:00',command:'omi-task TASK-115',text:'Approve accept'};
  const openInbox=async items=>{data={projects:[summary],source:remoteSource,inbox:items};location.hash='#/inbox';await invoke('route()');};
  await openInbox([item]);
  assert(invoke(`inboxPage(${JSON.stringify([item,{...item,reason:'quota'}])})`).map(n=>n.textContent).join('').includes('2 việc · 1 task'));
  assert.equal(permissionRequests,0);assert.equal(notices.length,0);
  assert.equal(elements['inbox-count'].textContent,'1');assert.equal(document.title,'(1) Hộp thư PO — omi board');
  assert.equal(all(elements.view).filter(n=>n.tagName==='img').length,0);
  versionSha=remoteSource.sha;now=Date.parse('2026-11-01T12:00:00Z');await invoke('route()');
  assert(elements.view.textContent.includes('Chờ 0 phút'));
  const ageView=elements.view.children[0], ageCalls=calls;
  now+=120000;await invoke('pollVersion()');
  assert(elements.view.textContent.includes('Chờ 2 phút'));assert.equal(calls,ageCalls);
  assert.equal(elements.view.children[0],ageView);
  now+=60000;await invoke('route()');
  assert(elements.view.textContent.includes('Chờ 3 phút'));assert.equal(elements.view.children[0],ageView);

  const settings=()=>all(elements.view).find(n=>n.attrs.id==='notification-settings');
  const notificationButton=()=>all(settings()).find(n=>n.tagName==='button');
  await notificationButton().listeners.click();
  assert.equal(permissionRequests,1);assert.equal(notices.length,0);assert(notificationButton().textContent.includes('Tắt'));
  const copyButton=()=>all(elements.view).find(n=>n.attrs['data-control']?.startsWith('['));
  await copyButton().listeners.click();assert.deepEqual(copied,['omi-task TASK-115']);assert(elements.view.textContent.includes('Đã sao chép: omi-task TASK-115'));
  window.navigator.clipboard.writeText=async()=>{throw Error('denied');};
  await copyButton().listeners.click();assert(elements.view.textContent.includes('Không sao chép được.'));assert.equal(copyButton().disabled,false);
  const next={...item,id:'TASK-116',command:'omi-task TASK-116',reason:'needs_scope'};
  await openInbox([item,next]);assert.equal(notices.length,1);
  await openInbox([{...item,text:'changed copy'},next]);assert.equal(notices.length,1);
  await openInbox([]);await openInbox([item,next]);assert.equal(notices.length,1);
  // Turning off/on, unchanged refresh and route changes never replay seen items.
  await notificationButton().listeners.click();await notificationButton().listeners.click();
  await invoke('route()');assert.equal(notices.length,1);
  const episode={...next,since:'2026-11-01 13:00'};
  copyButton().focus();window.scrollY=320;
  await openInbox([item,episode]);assert.equal(notices.length,2);assert.equal(document.activeElement,copyButton());assert.equal(window.scrolled,320);
  copyButton().focus();await openInbox([episode]);assert.equal(document.activeElement.attrs.id,'inbox-title');
  notices[0].onclick();assert(window.focused);assert.equal(location.hash,'#/inbox');
  // Partial/failed refresh keeps the old complete snapshot and seen set intact.
  const beforeInbox=invoke('JSON.stringify(inboxItems)');
  fail=true;await invoke('route()');assert.equal(invoke('JSON.stringify(inboxItems)'),beforeInbox);
  fail=false;
  window.Notification.permission='denied';invoke('renderNotificationSettings()');assert.equal(notificationButton().disabled,true);
  assert(settings().textContent.includes('bị chặn'));assert.equal(permissionRequests,2);
  window.Notification.permission='default';window.Notification.requestPermission=async()=>{permissionRequests++;return 'default';};
  invoke('renderNotificationSettings()');await notificationButton().listeners.click();assert(settings().textContent.includes('Chưa cấp quyền'));
  window.isSecureContext=false;invoke('renderNotificationSettings()');assert.equal(notificationButton().disabled,true);
  window.isSecureContext=true;window.localStorage={getItem:()=>null,setItem:()=>{throw Error('storage denied');}};
  invoke('renderNotificationSettings()');await notificationButton().listeners.click();assert(settings().textContent.includes('Tùy chọn chỉ áp dụng cho tab này'));
  // First snapshot after reload is silent even when the persisted opt-in is on.
  window.Notification.permission='granted';invoke('inboxItems=null; notifyEnabled=true');
  await openInbox([{...episode,project:'other'}]);assert.equal(notices.length,2);
  window.Notification=class {static permission='granted';constructor(){throw Error('unavailable');}};
  await openInbox([{...episode,id:'TASK-117'}]);assert(settings().textContent.includes('Không tạo được thông báo'));

  await invoke('route()');assert.equal(notices.length,2);
  // Global polling refreshes other projects even from a project route.
  window.Notification=class {static permission='granted';constructor(title,options){notices.push({title,options});}};
  globalInbox=[{...episode,project:'third',id:'TASK-118'}, {...episode,project:'fourth',id:'TASK-118'}];
  data=dashboard;location.hash='#/p/omi';await invoke('route()');
  assert.equal(notices.length,3);assert.equal(notices[2].title,'2 việc mới chờ PO');
  assert(document.title.startsWith('(2) '));
  await invoke('pollVersion()');assert.equal(notices.length,3);
  globalInbox=[...globalInbox,{...episode,project:'fifth'}];versionSha='other-project-change';
  await invoke('pollVersion()');assert.equal(notices.length,4);assert.equal(elements['inbox-count'].textContent,'3');
  for(const reason of ['needs_scope','quota']) {
    const first={...next,reason,since:null,request_marker:'2026-11-01 12:00'};
    await openInbox([first]);const count=notices.length;
    await openInbox([]);await openInbox([{...first,request_marker:'2026-11-01 13:00'}]);
    assert.equal(notices.length,count+1);
    await invoke('route()');assert.equal(notices.length,count+1);
  }
  // TASK-129: combined client filters, URL round-trip, contextual ancestors and leaf counts.
  fail=false;data=hierarchy;location.hash='#/p/omi';await invoke('route()');
  const filterTasks=Object.values(hierarchy.kanban).flat();
  const filterItems=[
    {...detail,id:'TASK-A',frontmatter:{title:'Board tiếng Việt',plan:'P & /?',role:'~builder'}},
    {...detail,id:'TASK-B',status:'done',frontmatter:{title:'Other'}},
    {...detail,id:'EPIC-A',type:'epic',frontmatter:{title:'Board parent',plan:'P & /?',role:'~builder'}}
  ];
  const runFilter=state=>invoke(`(${JSON.stringify(filterItems)}).filter(t=>matchesFilters(t,${JSON.stringify(state)})).map(t=>t.id)`);
  assert.deepEqual([...runFilter({q:'  BOARD ',status:'in-progress',type:'task',plan:'P & /?',role:'~~builder'})],['TASK-A']);
  assert.deepEqual([...runFilter({q:'task-b',status:'done',plan:'~none',role:'~none'})],['TASK-B']);
  assert.deepEqual([...runFilter({q:'tieng'})],[]); // Diacritics remain meaningful.
  assert.deepEqual([...runFilter({q:'tiếng'})],['TASK-A']);
  assert.deepEqual([...runFilter({q:'board',status:'done'})],[]);
  const shared={q:'Việt & /? <script>',status:'in-progress',type:'task',plan:'P & /?',role:'~~builder'};
  const hash=invoke(`projectHref('omi')+filterQuery(${JSON.stringify(shared)})`);
  const restored=invoke(`readFilters(${JSON.stringify(hash)},${JSON.stringify(filterItems)})`);
  assert.equal(JSON.stringify(restored.state),JSON.stringify(shared));assert.equal(restored.invalid,false);
  const invalid=invoke(`readFilters('#/p/omi?unknown=x&q=%E0%A4&status=bad&type=epic&plan=removed&role=~none&type=task',${JSON.stringify(filterItems)})`);
  assert.equal(invalid.invalid,true);assert.equal(JSON.stringify(invalid.state),JSON.stringify({type:'epic',role:'~none'}));
  const repeated=invoke(`readFilters('#/p/omi?q=first&q=second&status=done&status=planned',${JSON.stringify(filterItems)})`);
  assert.equal(repeated.state.q,'first');assert.equal(repeated.state.status,'done');
  const q=document.getElementById('board-search');
  const initialFilterCalls=calls;
  q.focus();q.value='TASK-115';q.listeners.input();
  assert.equal(find(elements.view,'filter-summary')[0].textContent,'Đang lọc: từ khóa “TASK-115”');
  assert.equal(calls,initialFilterCalls);assert.equal(document.getElementById('board-search'),q);assert.equal(document.activeElement,q);
  assert.equal(find(elements.view,'card').length,1);
  assert.equal(find(elements.view,'context-label').length,3);
  assert(find(elements.view,'tree')[0].textContent.includes('MILESTONE-001'));
  assert(find(elements.view,'tree')[0].children[0].attrs.open==='');
  assert(find(elements.view,'card')[0].children[1].attrs.href.endsWith('?q=TASK-115'));
  const select=document.getElementById('filter-status');select.value='done';select.listeners.change();
  assert.equal(find(elements.view,'card').length,0);assert(elements.view.textContent.includes('Không tìm thấy công việc phù hợp.'));
  const emptyReset=find(elements.view,'no-results')[0].children.find(n=>n.tagName==='button');
  emptyReset.listeners.click();assert.equal(q.value,'');assert.equal(document.activeElement,q);assert.equal(location.hash,'#/p/omi');
  q.value='FR-001';q.listeners.input();assert.equal(find(elements.view,'card').length,0);
  assert(elements.view.textContent.includes('Không có task lá khớp bộ lọc trên Kanban.'));
  assert.equal(find(elements.view,'context-label').length,2);
  q.listeners.keydown({key:'Escape',preventDefault(){}});assert.equal(q.value,'');
  const keyEvent={key:'/',target:document.body,preventDefault(){this.prevented=true;}};
  document.activeElement=document.body;document.listeners.keydown(keyEvent);assert.equal(document.activeElement,q);assert(keyEvent.prevented);
  for(const extra of [{ctrlKey:true},{metaKey:true},{altKey:true},{shiftKey:true},{isComposing:true},{target:q},{target:{tagName:'select'}},{target:{isContentEditable:true}}]) {
    document.activeElement=document.body;document.listeners.keydown({...keyEvent,...extra});assert.equal(document.activeElement,document.body);
  }
  location.hash='#/p/omi?status=done';await window.listeners.hashchange();
  assert.equal(calls,initialFilterCalls);assert.equal(find(elements.view,'card').length,4);assert.equal(document.getElementById('filter-status').value,'done');
  // Simulate opening the shared hash anew; linked controls/results are restored on load.
  invoke('loadedDashboard=null');await invoke('route()');assert.equal(find(elements.view,'card').length,4);
  const share=find(elements.view,'filter-actions')[0].children[1];let copiedUrl;
  window.navigator={clipboard:{writeText:async text=>{copiedUrl=text;}}};
  await share.listeners.click();assert.equal(copiedUrl,location.href);assert(elements.view.textContent.includes('Đã sao chép liên kết.'));
  window.navigator.clipboard.writeText=async()=>{throw Error('denied');};await share.listeners.click();
  assert.equal(document.getElementById('share-url').value,location.href);assert.equal(document.getElementById('share-url').attrs.readonly,'');
  assert(elements.view.textContent.includes('Không sao chép được. Chọn và sao chép liên kết bên dưới.'));
  // Reconcile stale metadata on refresh without clearing still-valid fields.
  location.hash='#/p/omi';await invoke('route()');
  assert.equal(document.getElementById('share-url'),undefined);
  assert(!elements.view.textContent.includes('Không sao chép được. Chọn và sao chép liên kết bên dưới.'));
  const previousTree=find(elements.view,'tree')[0].children[0];previousTree.open=false;previousTree.listeners.toggle();
  let searchControl=document.getElementById('board-search');searchControl.value='TASK-115';searchControl.listeners.input();
  assert.equal(find(elements.view,'tree')[0].children[0].attrs.open,'');
  searchControl.value='';searchControl.listeners.input();
  // Clearing every filter restores the saved disclosure state.
  find(elements.view,'filter-actions')[0].children[0].listeners.click();
  assert.equal(find(elements.view,'tree')[0].children[0].attrs.open,undefined);
  location.hash='#/p/omi?type=task&plan=PLAN-006';await invoke('route()');
  data={...hierarchy,kanban:Object.fromEntries(Object.entries(hierarchy.kanban).map(([key,items])=>[key,items.map(t=>({...t,frontmatter:{...t.frontmatter,plan:'NEW'}}))]))};
  await invoke('route()');
  assert.equal(document.getElementById('filter-plan').value,'');assert.equal(document.getElementById('filter-type').value,'task');
  assert(elements.view.textContent.includes('Một số bộ lọc không còn khả dụng đã được bỏ qua.'));
  assert.equal(location.hash,'#/p/omi?type=task');
  fail=true;await elements.refresh.listeners.click();
  assert.equal(document.getElementById('board-search').disabled,false);
  assert(elements.err.textContent.includes('Không làm mới được. Đang hiển thị dữ liệu lần tải trước.'));
  fail=false;data=hierarchy;await invoke('route()');
  const available=invoke(`filterOptions(${JSON.stringify(filterItems)})`);
  assert.equal(JSON.stringify(available.role),JSON.stringify([['~none','Chưa có vai trò'],['~~builder','~builder']]));
  location.hash='#/p/omi?status=done&q=%E0%A4&type=wrong';await invoke('route()');
  assert.equal(location.hash,'#/p/omi?status=done');assert.equal(document.getElementById('filter-status').value,'done');
  assert(elements.view.textContent.includes('Một số bộ lọc không còn khả dụng đã được bỏ qua.'));
  // The detail request remains a real task endpoint, with filters on its return links.
  location.hash='#/p/omi/t/TASK-115?status=done';data=detail;await invoke('route()');
  assert(all(elements.view).some(n=>n.tagName==='a' && n.attrs.href==='#/p/omi?status=done'));
  data={...hierarchy,kanban:{}};location.hash='#/p/omi';await invoke('route()');
  assert(elements.view.textContent.includes('Chưa có công việc trong dự án này.'));
  assert.equal(find(elements.view,'filter-actions')[0].children[0].disabled,true);
  data={...dashboard,kanban:{'in-progress':[{...detail,frontmatter:{...frontmatter,plan:' P '}}]}};await invoke('route()');
  const exactPlan=document.getElementById('filter-plan');exactPlan.value=' P ';exactPlan.listeners.change();
  assert.equal(location.hash,'#/p/omi?plan=%20P%20');assert.equal(find(elements.view,'card').length,1);
  // A delayed announcement from before a refresh cannot overwrite the new counts.
  const searchBeforeRefresh=document.getElementById('board-search');searchBeforeRefresh.value='TASK';searchBeforeRefresh.listeners.input();
  const announcement=timeouts.find(t=>t.ms===250);
  data={...data,kanban:{}};await invoke('route()');
  const refreshedCount=find(elements.view,'filter-count')[0].textContent;announcement.f();
  assert.equal(find(elements.view,'filter-count')[0].textContent,refreshedCount);
  console.log('ok: API views, mockup DOM, safe text, polling, recovery, focus, races, combined filters, hash round-trip, hierarchy context, keyboard, sharing');
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
    let timelineMode=null,release=null,timelineHold=null;
    const timelineFixture={full:timelineDetail,'no-files':noFilesDetail,'no-steps':noStepsDetail,loading:timelineDetail};
    const gnode=(id,title,status,layer,o={})=>({id,title,status,layer,depends:[],blocks:[],waiting:[],blocked_by:[],critical:false,...o});
    const gnodes=[gnode('TASK-124','Nguồn dữ liệu board','done',1,{blocks:['TASK-115'],critical:true}),
      gnode('TASK-126','Lược đồ trạng thái','done',1,{blocks:['TASK-127']}),
      gnode('TASK-115','Dashboard dự án','in-progress',2,{depends:['TASK-124'],blocks:['TASK-130'],critical:true}),
      gnode('TASK-127','Thông báo trình duyệt cho mọi người dùng bảng điều khiển','review',2,{depends:['TASK-126'],blocks:['TASK-131']}),
      gnode('TASK-130','Cảnh báo sức khỏe','blocked',3,{depends:['TASK-115'],blocks:['TASK-131'],waiting:['TASK-115'],blocked_by:['TASK-115'],critical:true}),
      gnode('TASK-131','Biểu đồ phụ thuộc','planned',4,{depends:['TASK-130','TASK-127'],waiting:['TASK-130','TASK-127'],critical:true})];
    const gedges=[['TASK-124','TASK-115',1],['TASK-126','TASK-127',0],['TASK-115','TASK-130',1],['TASK-130','TASK-131',1],['TASK-127','TASK-131',0]].map(([from,to,critical])=>({from,to,critical:!!critical}));
    const ggraph={empty:false,nodes:gnodes,edges:gedges,cycles:[],critical_path:['TASK-124','TASK-115','TASK-130','TASK-131'],
      summary:{tasks:6,layers:4,blocked:1,critical:4,critical_left:3,cycle_tasks:0}};
    const gscopes=(graph)=>({source:remoteSource,name:'omi',plans:[{id:'PLAN-007',title:'Đồ thị',status:'active'}],scopes:{all:graph,'PLAN-007':graph}});
    const graphFixture={full:gscopes(ggraph),
      cycle:gscopes({...ggraph,cycles:[['TASK-140','TASK-141','TASK-142','TASK-140']],summary:{...ggraph.summary,cycle_tasks:3}}),
      empty:gscopes({empty:true,nodes:[],edges:[],cycles:[],critical_path:[],summary:{tasks:2,layers:1,blocked:0,critical:1,critical_left:1,cycle_tasks:0}})};
    let graphMode='full';
    const alertFixture=[['stale','Không hoạt động'],['review_fail','Review FAIL ×2'],['behind','Nhánh tụt hậu'],['blocked_dep','Phụ thuộc bị chặn']]
      .map(([kind,chip],i)=>({id:`TASK-11${i}`,title:`Việc ${i}`,kind,chip,reason:'Lý do (ngưỡng: 3 ngày).',action:'Hỏi agent phụ trách.'}));
    let alertsOn=0;
    const errors=[];page.on('pageerror', e=>errors.push(e.message));
    page.on('console', msg=>{if(msg.type()==='error') errors.push(msg.text());});
    await page.route('**/*',async route=>{
      const url=new URL(route.request().url());
      if(url.origin!=='http://omi.test' || route.request().method()!=='GET') {
        errors.push(`Unexpected request: ${route.request().method()} ${url}`);
        return route.abort();
      }
      if(url.pathname.startsWith('/api/')) {
        if(timelineMode==='loading'&&url.pathname.endsWith('/tasks/TASK-115')) await timelineHold;
        if(url.pathname==='/api/projects/omi/graph') return route.fulfill({json:graphFixture[graphMode]});
        if(url.pathname==='/api/projects/omi/cost') return route.fulfill({json:{...costFixture[costMode],source:remoteSource}});
        const data=url.pathname.endsWith('/version')?{sha:remoteSource.sha}:url.pathname.endsWith('/tasks/TASK-115')?(timelineMode&&timelineFixture[timelineMode]||workflowDetail):url.pathname==='/api/projects/omi'?(alertsOn?{...hierarchy,alerts:alertFixture.slice(0,alertsOn)}:hierarchy):{projects:[summary],source:remoteSource,inbox:inboxFixture};
        return route.fulfill({json:data});
      }
      const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      const types={'.html':'text/html','.css':'text/css','.js':'application/javascript','.svg':'image/svg+xml'};
      assert(types[path.extname(name)],name);
      await route.fulfill({body:fs.readFileSync(path.join(process.argv[1],name)),contentType:types[path.extname(name)],
        headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'"}});
    });
    // TASK-191: sidebar links, native keyboard toggle, storage and mobile overlay.
    for(const width of [1280,375,320]) {
      await page.setViewportSize({width,height:900});
      await page.goto('http://omi.test/#/p/omi');
      await page.evaluate(()=>localStorage.removeItem('omi-board-sidebar'));
      await page.reload();
      await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
      const toggle=page.locator('#sidebar-toggle'), sidebar=page.locator('#board-sidebar');
      assert.equal(await toggle.getAttribute('aria-controls'),'board-sidebar');
      assert.equal(await toggle.getAttribute('aria-expanded'),String(width>=768));
      assert.equal(await sidebar.isVisible(),width>=768);
      if(width<768) { await toggle.focus();await page.keyboard.press('Space'); }
      assert.equal(await sidebar.locator('a').count(),7);
      assert.deepEqual(await sidebar.locator('a').allTextContents(),
        ['Tổng quan dự án','Cây công việc','Kanban','Hộp thư PO','Chi phí','Đồ thị phụ thuộc','Thông báo']);
      if(width<768) {
        const source=await page.locator('#source').boundingBox(), stamp=await page.locator('#status').boundingBox();
        assert(stamp.y+stamp.height<=source.y,'phone timestamp and source must occupy separate rows');
        assert(await page.locator('#sidebar-backdrop').isVisible());
        assert(await page.locator('main').evaluate(n=>n.inert));
        await toggle.focus();await page.keyboard.press('Shift+Tab');
        assert(await sidebar.locator('a').last().evaluate(n=>n===document.activeElement));
        await page.keyboard.press('Tab');assert(await toggle.evaluate(n=>n===document.activeElement));
      }
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`sidebar overflow ${width}`);
      await page.evaluate(axeSource);await audit(`sidebar open ${width} light`);
      await page.emulateMedia({colorScheme:'dark'});await audit(`sidebar open ${width} dark`);
      await page.emulateMedia({colorScheme:'light'});
      if(screens && width!==320) await page.screenshot({path:path.join(screens,`sidebar-${width}.png`)});
      for(const [label,target] of [['Cây công việc','board-tree'],['Kanban','board-kanban'],['Thông báo','notification-settings']]) {
        if(!(await sidebar.isVisible())) await toggle.click();
        await sidebar.getByRole('link',{name:label,exact:true}).click();
        await page.waitForFunction(id=>document.activeElement.id===id,target);
        assert(await page.locator('#'+target).isVisible());
        if(width<768) {
          assert.equal(await sidebar.isVisible(),false);
          assert.equal(await page.locator('main').evaluate(n=>n.inert),false);
        }
      }
      if(!(await sidebar.isVisible())) await toggle.click();
      for(const [label,selector] of [['Chi phí','.cost-stats'],['Đồ thị phụ thuộc','.g-summary'],['Hộp thư PO','.inbox-items'],['Tổng quan dự án','#board-tree']]) {
        if(!(await sidebar.isVisible())) await toggle.click();
        await sidebar.getByRole('link',{name:label,exact:true}).click();await page.locator(selector).waitFor();
      }
      if(!(await sidebar.isVisible())) await toggle.click();
      await page.keyboard.press('Escape');
      assert.equal(await toggle.getAttribute('aria-expanded'),'false');
      assert(await toggle.evaluate(n=>n===document.activeElement));
      assert.equal(await page.evaluate(()=>localStorage.getItem('omi-board-sidebar')),'closed');
      await page.reload();assert.equal(await sidebar.isVisible(),false);
      await toggle.focus();await page.keyboard.press('Enter');
      assert.equal(await page.evaluate(()=>localStorage.getItem('omi-board-sidebar')),'open');
      await page.reload();assert.equal(await sidebar.isVisible(),width>=768);
    }
    await page.addInitScript(()=>{
      if(!location.search.includes('sidebar-storage=blocked')) return;
      for(const method of ['getItem','setItem']) Object.defineProperty(Storage.prototype,method,{value:()=>{throw Error('storage disabled');}});
    });
    await page.setViewportSize({width:1280,height:900});
    await page.goto('http://omi.test/?sidebar-storage=blocked#/p/omi?section=kanban');
    await page.waitForFunction(()=>document.activeElement.id==='board-kanban');
    await page.locator('#sidebar-toggle').click();await page.locator('#sidebar-toggle').click();
    assert.equal(await page.locator('#sidebar-toggle').getAttribute('aria-expanded'),'true');
    await page.goto('http://omi.test/#/');
    await page.evaluate(()=>localStorage.removeItem('omi-board-sidebar'));
    console.log('ok: sidebar links, keyboard, persistence, disabled storage, mobile overlay and 320px overflow');
    // Exercise every main route, including short fixtures that need extra content
    // to make document scrolling possible at both viewport sizes.
    const headerFailures=[];
    const headerRoutes=[['projects','#/'],['dashboard','#/p/omi'],['task','#/p/omi/t/TASK-115'],
      ['inbox','#/inbox'],['cost','#/p/omi/cost'],['graph','#/p/omi/graph']];
    for(const width of [375,1280]) {
      await page.setViewportSize({width,height:800});
      for(const [name,hash] of headerRoutes) {
        await page.goto(`http://omi.test/?header=${name}&width=${width}${hash}`);
        await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
        await page.evaluate(()=>{
          const content=document.createElement('section');content.id='scroll-fixture';
          for(let i=0;i<80;i++) {
            const paragraph=document.createElement('p');paragraph.textContent=`Scroll regression row ${i}`;
            content.append(paragraph);
          }
          document.getElementById('main').append(content);
        });
        for(const bottom of [false,true]) {
          await page.evaluate(bottom=>window.scrollTo(0,bottom?document.documentElement.scrollHeight:300),bottom);
          await page.waitForFunction(()=>window.scrollY>0);
          const top=await page.locator('.top').evaluate(n=>n.getBoundingClientRect().top);
          if(top!==0) headerFailures.push(`${name} ${width} ${bottom?'bottom':'middle'}: top=${top}`);
          if(!bottom && screens) await page.screenshot({path:path.join(screens,`header-${name}-${width}.png`)});
        }
        await page.locator('#scroll-fixture').evaluate(n=>n.remove());
        await page.evaluate(()=>window.scrollTo(0,0));
      }
    }
    assert.deepEqual(headerFailures,[],'header must stay at top=0 while scrolling every main route');
    console.log('ok: sticky header on projects/dashboard/task/inbox/cost/graph at 375/1280px, middle and bottom scroll');
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
        // The timestamp wraps onto its own line on phones.
        if(width<768) assert(header.height<240,`compact phone header ${width} ${hash}: ${header.height}px`);
        if(hash==='#/p/omi') {
          const columns=await page.locator('.col:visible').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().x));
          assert.equal(new Set(columns).size,width<768?1:2);
          assert.equal(columns.length,2);
          assert.equal(await page.locator('.col-done .card:visible').count(),0);
          await page.locator('.col-done>summary').focus();await page.keyboard.press('Enter');
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
        assert(await page.locator('#main').evaluate(n=>n===document.activeElement),'skip target focused');
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
          assert.equal(await page.locator('details:not(.raw)').first().getAttribute('open'),'');
          const marker=()=>page.locator('details:not(.raw) summary').first().evaluate(n=>getComputedStyle(n,'::before').content);
          assert.equal(await marker(),'"▾"');
          await page.locator('details:not(.raw) summary').first().focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('details:not(.raw)').first().getAttribute('open'),null);
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

    // TASK-129: approved toolbar geometry, keyboard, history and shareable task navigation.
    for(const width of [320,375,768,1000,1280]) {
      await page.setViewportSize({width,height:900});
      await page.goto('http://omi.test/#/p/omi?q=TASK-115&type=task&plan=PLAN-006');
      await page.locator('.filter-count').filter({hasText:'1 / 8'}).waitFor();
      assert.equal(await page.locator('#share-url').count(),0);
      const search=page.getByRole('searchbox',{name:'Tìm ID hoặc tiêu đề'});
      assert.equal(await search.inputValue(),'TASK-115');
      assert.equal(await page.locator('#filter-plan').inputValue(),'PLAN-006');
      assert.equal(await page.locator('.context-label').count(),3);
      assert.equal(await page.locator('.card').count(),1);
      assert.equal(await page.locator('.filters').evaluate(n=>getComputedStyle(n).gridTemplateColumns.split(' ').length),width<768?1:width<=1000?2:5);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`filters overflow ${width}`);
      assert(await search.evaluate(n=>n.getBoundingClientRect().height>=44));
      if(screens && [375,1280].includes(width)) await page.screenshot({path:path.join(screens,`filters-${width}.png`),fullPage:true});
      await page.evaluate(axeSource);await audit(`filters ${width} light`);
      await page.emulateMedia({colorScheme:'dark'});await audit(`filters ${width} dark`);await page.emulateMedia({colorScheme:'light'});
      await page.locator('#refresh').focus();await page.keyboard.press('/');assert(await search.evaluate(n=>n===document.activeElement));
      await page.keyboard.press('Escape');assert.equal(await search.inputValue(),'');
      assert.equal(await page.locator('#filter-type').inputValue(),'task');assert.equal(await page.locator('#filter-plan').inputValue(),'PLAN-006');
      await search.fill('no matches');await page.getByText('Không tìm thấy công việc phù hợp.',{exact:true}).waitFor();
      assert(await search.evaluate(n=>n===document.activeElement));
      await page.locator('.no-results button').click();assert(await search.evaluate(n=>n===document.activeElement));
      assert.equal(await search.inputValue(),'');assert.equal(await page.locator('#filter-plan').inputValue(),'');
      // Real Back/Forward should only update the local results and retain search focus.
      let requests=0;const countRequest=request=>{if(request.url().includes('/api/projects'))requests++;};
      page.on('request',countRequest);
      await page.locator('#filter-status').selectOption('done');
      await search.focus();await page.goBack();
      await page.waitForFunction(()=>document.getElementById('filter-status').value==='');
      assert(await search.evaluate(n=>n===document.activeElement));
      await page.goForward();await page.waitForFunction(()=>document.getElementById('filter-status').value==='done');
      assert.equal(requests,0);page.off('request',countRequest);
      await page.reload();await page.locator('.filter-count').filter({hasText:'4 / 8'}).waitFor();
      assert.equal(await page.locator('#filter-status').inputValue(),'done');
      await page.evaluate(()=>{location.hash='#/p/omi/t/TASK-115?status=done';});await page.locator('.layout').waitFor();
      assert(page.url().endsWith('?status=done'));assert.equal(await page.getByRole('link',{name:'← Về dự án omi'}).getAttribute('href'),'#/p/omi?status=done');
      await page.getByRole('link',{name:'← Về dự án omi'}).click();await page.locator('.filter-count').filter({hasText:'4 / 8'}).waitFor();
      await page.evaluate(()=>Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText:async text=>{window.sharedUrl=text;}}}));
      await page.getByRole('button',{name:'Sao chép liên kết',exact:true}).click();
      await page.getByText('Đã sao chép liên kết.',{exact:true}).waitFor();assert.equal(await page.evaluate(()=>window.sharedUrl),page.url());
      await page.evaluate(()=>{navigator.clipboard.writeText=async()=>{throw Error('denied');};});
      await page.getByRole('button',{name:'Sao chép liên kết',exact:true}).click();
      assert.equal(await page.getByLabel('Liên kết chế độ xem').inputValue(),page.url());
      assert(await page.getByLabel('Liên kết chế độ xem').evaluate(n=>n.readOnly));
      if(width===1280) {
        await page.evaluate(()=>{document.body.style.zoom='2';});
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'filters 200% zoom overflow');
        await page.evaluate(()=>{document.body.style.zoom='';});
      }
    }
    await page.addInitScript(()=>{
      window.permissionRequests=0;window.notifications=[];
      Object.defineProperty(window,'isSecureContext',{value:true});
      Object.defineProperty(window,'Notification',{value:class {
        static permission='default';
        static async requestPermission(){window.permissionRequests++;this.permission='granted';return 'granted';}
        constructor(title,opts){window.notifications.push({title,opts});}
      }});
      window.localStorage.removeItem('omi-board-notifications');
      Object.defineProperty(navigator,'clipboard',{value:{writeText:async text=>{window.copiedCommand=text;}}});
    });
    for(const [count,label,schemes] of [[4,'alerts',['light','dark']],[1,'alerts-one',['light','dark']],[0,'alerts-empty',['light']]]) {
      alertsOn=count;
      for(const width of [375,1280]) {
        await page.setViewportSize({width,height:900});
        await page.goto(`http://omi.test/?${label}=${width}#/p/omi`);
        await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
        assert.equal(await page.locator('.alert').count(),count);
        assert.equal(await page.locator('section.health').count(),count?1:0);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${label} overflow ${width}`);
        if(count) {
          assert.equal(await page.locator('section.health').getAttribute('aria-labelledby'),'health-h');
          assert.equal(await page.locator('#health-h').innerText(),`Cảnh báo sức khỏe (${count})`);
          const go=await page.locator('.alert .go').first().boundingBox();
          if(width<768) assert(go.height>=44,`alert target ${go.height}`);
        }
        for(const scheme of schemes) {
          await page.emulateMedia({colorScheme:scheme});
          await page.evaluate(axeSource);await audit(`${label} ${width} ${scheme}`);
          if(screens) await page.screenshot({path:path.join(screens,`${label}-${width}-${scheme}.png`),fullPage:true});
        }
        await page.emulateMedia({colorScheme:'light'});
      }
    }
    alertsOn=0;
    for(const width of [320,375,1280]) {
      await page.setViewportSize({width,height:900});
      await page.goto(`http://omi.test/?inbox=${width}#/inbox`);
      await page.locator('.inbox-items>li').first().waitFor();
      assert.equal(await page.locator('.inbox-items>li').count(),5);
      assert.equal(await page.title(),'(5) Hộp thư PO — omi board');
      assert.equal(await page.locator('#inbox-count').innerText(),'5');
      assert.equal(await page.evaluate(()=>window.permissionRequests),0);
      assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`inbox overflow ${width}`);
      const columns=await page.locator('.inbox-items>li').first().evaluate(n=>getComputedStyle(n).gridTemplateColumns.split(' ').length);
      assert.equal(columns,width<768?1:3);
      assert(await page.locator('.inbox-items .chip').first().evaluate(n=>n.getBoundingClientRect().height<30),'compact approved reason badge');
      assert.equal(await page.locator('.inbox-items time').count(),4);
      assert((await page.locator('.inbox-items').innerText()).includes('Chờ: chưa rõ thời điểm'));
      assert.equal(await page.locator('#view img,#view script').count(),0);
      await page.evaluate(axeSource);await audit(`inbox ${width} light`);
      if(screens) await page.screenshot({path:path.join(screens,`inbox-${width}.png`),fullPage:true});
      await page.getByRole('button',{name:'Bật thông báo',exact:true}).focus();
      await page.keyboard.press('Space');
      await page.getByRole('button',{name:'Tắt thông báo',exact:true}).waitFor();
      assert.equal(await page.evaluate(()=>window.permissionRequests),1);
      assert.equal(await page.evaluate(()=>window.notifications.length),0);
      const copy=page.getByRole('button',{name:'Sao chép omi-task TASK-115 · omi',exact:true});
      await copy.focus();await page.keyboard.press('Enter');
      await page.getByText('Đã sao chép: omi-task TASK-115',{exact:true}).waitFor();
      assert.equal(await page.evaluate(()=>window.copiedCommand),'omi-task TASK-115');
      await page.evaluate(()=>{navigator.clipboard.writeText=async()=>{throw Error('denied');};});
      await copy.click();await page.getByText('Không sao chép được. Chọn và sao chép lệnh hiển thị bên trên.',{exact:true}).waitFor();
      assert(await copy.evaluate(n=>n===document.activeElement));
      await page.emulateMedia({colorScheme:'dark'});await audit(`inbox ${width} dark`);
      await page.emulateMedia({colorScheme:'light'});
      // Two hundred percent zoom on the desktop must still fit its viewport.
      if(width===1280) {
        await page.evaluate(()=>{document.body.style.zoom='2';});
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'inbox zoom overflow');
        await page.evaluate(()=>{document.body.style.zoom='';});
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
        // Font-independent: the caption fills its table instead of shrinking to a narrow column.
        assert.equal(await page.locator('.panel').first().locator('caption').evaluate(n=>n.getBoundingClientRect().width>=n.closest('table').getBoundingClientRect().width*.9),true,`caption wrap ${mode} ${width}`);
        await page.getByRole('button',{name:'Theo model',exact:true}).click();
        await page.evaluate(axeSource);
        await audit(`cost ${mode} ${width} light`);
        await page.emulateMedia({colorScheme:'dark'});
        await audit(`cost ${mode} ${width} dark`);
        await page.emulateMedia({colorScheme:'light'});
      }
    }
    // TASK-131: dependency graph (wide SVG + list, phone list only, cycle banner, empty state).
    await page.setViewportSize({width:1280,height:900});
    await page.goto('http://omi.test/#/p/omi');
    assert.equal(await page.getByRole('link',{name:'Đồ thị phụ thuộc →'}).getAttribute('href'),'#/p/omi/graph');
    for(const mode of ['full','cycle','empty']) {
      graphMode=mode;
      for(const width of mode==='full'?[320,375,768,1280]:[375,1280]) {
        await page.setViewportSize({width,height:900});
        await page.goto(`http://omi.test/?graph=${mode}&width=${width}#/p/omi/graph/PLAN-007`);
        await page.locator(mode==='empty'?'.g-blank':'.g-summary').waitFor();
        assert.equal(await page.locator('h1').innerText(),'Đồ thị phụ thuộc');
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow graph ${mode} ${width}`);
        assert.equal(await page.locator('[style]').count(),0);
        assert.equal(await page.locator('#view script, #view img, #view foreignObject').count(),0);
        assert.equal(await page.locator('.g-plans a').allInnerTexts().then(a=>a.join('|')),'PLAN-007|Tất cả');
        assert.equal(await page.locator('.g-plans [aria-current="page"]').innerText(),'PLAN-007');
        if(mode==='empty') {
          assert.equal(await page.locator('svg').filter({has:page.locator('.g-node')}).count(),0);
          assert((await page.locator('.g-blank').innerText()).includes('Chưa có task nào khai báo phụ thuộc.'));
        } else {
          const wide=width>=768;
          assert.equal(await page.locator('.g-wide').isVisible(),wide,`graph svg visibility ${width}`);
          assert.equal(await page.locator('.g-wide').getAttribute('aria-hidden'),'true');
          assert.equal(await page.locator('.g-it').count(),6);
          assert.equal(await page.locator('.g-it.crit').count(),4);
          assert.equal(await page.locator('.g-it.blocked').count(),1);
          const list=await page.locator('.g-layers').innerText();
          assert(list.includes('Bị chặn bởi: TASK-115') && list.includes('Đang chờ: TASK-130, TASK-127') && list.includes('Tầng 4'));
          assert.equal(await page.locator('.g-summary').innerText().then(s=>s.replace(/\s+/g,' ')),'6 task 4 tầng 1 bị chặn 4 task trên đường găng (còn 3 chưa xong)');
          assert.equal(await page.locator('.g-warn').count(),mode==='cycle'?1:0);
          if(mode==='cycle') assert((await page.locator('.g-warn').innerText()).includes('TASK-140 → TASK-141 → TASK-142 → TASK-140'));
          if(width<768) assert((await page.locator('.g-it .go').first().boundingBox()).height>=44,'graph touch target');
          if(wide) {
            assert.equal(await page.locator('.g-node').count(),6);
            assert.equal(await page.locator('.g-edge').count(),5);
            assert.equal(await page.locator('.g-edge.crit').count(),3);
            assert.equal(await page.locator('.g-node.blocked rect').evaluate(n=>getComputedStyle(n).strokeDasharray!=='none'),true);
            const fits=await page.locator('.g-ti, .g-st').evaluateAll(nodes=>nodes.every(n=>n.getBBox().width<=160));
            assert(fits,'graph node text stays inside the box');
            assert.equal(await page.locator('.g-ti').filter({hasText:'…'}).count(),1);
          }
        }
        await page.evaluate(axeSource);await audit(`graph ${mode} ${width} light`);
        await page.emulateMedia({colorScheme:'dark'});await audit(`graph ${mode} ${width} dark`);
        await page.emulateMedia({colorScheme:'light'});
        if(screens) await page.screenshot({path:path.join(screens,`graph-${mode==='full'?'':mode+'-'}${width}.png`),fullPage:true});
        if(mode==='full'&&width===1280) {
          await page.locator('.g-plans a').last().click();
          await page.waitForFunction(()=>location.hash==='#/p/omi/graph/all');
          await page.locator('.g-plans [aria-current="page"]').filter({hasText:'Tất cả'}).waitFor();
          await page.locator('a.g-node').filter({hasText:'TASK-115'}).click();
          await page.waitForFunction(()=>location.hash==='#/p/omi/t/TASK-115');
          await page.locator('.layout').waitFor();
        }
      }
    }
    // TASK-132: task timeline at desktop and phone width (full, no files, no steps, loading), one screenshot per mockup screen.
    for(const mode of ['full','no-files','no-steps','loading']) {
      timelineMode=mode;
      for(const width of [1280,390]) {
        await page.setViewportSize({width,height:900});
        if(mode==='loading') timelineHold=new Promise(r=>{release=r;});
        await page.goto(`http://omi.test/?timeline=${mode}&width=${width}#/p/omi`);
        await page.locator('h1').waitFor();
        await page.evaluate(()=>{location.hash='#/p/omi/t/TASK-115';});
        if(mode==='loading') {
          const busy=page.locator('section[aria-busy="true"]');await busy.waitFor();
          assert.equal(await busy.locator('[role="status"]').innerText(),'Đang tải…');
        } else {
          await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
          await page.locator(mode==='no-steps'?'.empty-box':'.tl').waitFor();
          assert.equal(await page.locator('.tl').count(),mode==='no-steps'?0:1);
          assert.equal(await page.locator('.files').count(),mode==='full'?1:0);
          assert.equal(await page.locator('details.raw').count(),1);
          if(mode!=='no-steps') {
            assert.equal(await page.locator('.tl progress[aria-hidden="true"]').count(),4);
            assert.equal(await page.locator('.tl details[open]').count(),1);
            assert((await page.locator('.tl').innerText()).includes('đang chạy · 12 phút 40 giây'));
          }
        }
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow timeline ${mode} ${width}`);
        assert.equal(await page.locator('#view script, #view img').count(),0);
        if(screens) await page.screenshot({path:path.join(screens,`timeline-${mode}-${width}.png`),fullPage:true});
        await page.evaluate(axeSource);await audit(`timeline ${mode} ${width} light`);
        await page.emulateMedia({colorScheme:'dark'});await audit(`timeline ${mode} ${width} dark`);
        await page.emulateMedia({colorScheme:'light'});
        if(mode==='loading') release();
      }
    }
    timelineMode=null;
    graphMode='full';
    if(screens) {
      for(const name of ['projects','dashboard','task']) for(const width of [320,360,390,768,1280])
        assert(fs.statSync(path.join(screens,`${name}-${width}.png`)).size>0);
      for(const mode of ['full','no-files','no-steps','loading']) for(const width of [1280,390])
        assert(fs.statSync(path.join(screens,`timeline-${mode}-${width}.png`)).size>0);
      for(const name of ['graph-375','graph-1280','graph-cycle-1280','graph-empty-1280','graph-empty-375'])
        assert(fs.statSync(path.join(screens,`${name}.png`)).size>0);
    }
    assert.deepEqual(errors,[]);
    console.log('ok: browser layouts at 320/360/390/768/1280px, inbox at 320/375/1280px and 200% zoom, phone summaries, overflow disclosure, dark mode, CSP, keyboard controls, axe (light/dark), print, GET-only requests, filters/history/sharing at 320/375/768/1000/1280px, dependency graph (SVG, list, cycle, empty) at 320/375/768/1280px');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


if __name__ == "__main__":
    main()
