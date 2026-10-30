"""Board frontend: no innerHTML or external resources, files ship as package data."""
import fnmatch
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipfile
from pathlib import Path

import helpers  # noqa: F401

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "src" / "omi" / "board" / "web"
FILES = ("index.html", "app.css", "app.js", "favicon.svg")


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
    for needle in ("Thử lại", "Cập nhật lần cuối", "document.hidden", "localStorage"):
        assert needle in js, needle
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'role="status"' in html and 'id="refresh"' in html and "Làm mới" in html


def test_mockup_layout() -> None:
    css = (WEB / "app.css").read_text(encoding="utf-8")
    # The approved desktop structures and phone adaptation must remain present.
    for cls in ("bar", "brand", "tools", "switch", "wrap", "panel", "ph", "stats", "stat", "plan",
                "kanban", "col", "colh", "card", "grid2", "feed", "fi", "po", "poi", "sync",
                "projects", "pc", "counts", "layout", "main", "side", "steps", "sn", "crit", "ck"):
        assert re.search(r"\." + cls + r"[\s.{:]", css), cls
    for token in ("#f6f6f4", "#1f2421", "#0f6e6e", "prefers-color-scheme: dark", "max-width:767px",
                  "repeat(2,minmax(0,1fr))", "min(340px,100%)", ":focus-visible", "prefers-reduced-motion"):
        assert token in css, token
    html = (WEB / "index.html").read_text(encoding="utf-8")
    assert 'class="skip"' in html and 'href="#main"' in html and '<main ' in html


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
        print("skip test_browser_layout_and_keyboard: node missing")
        return
    run = subprocess.run([node, "-e", BROWSER_TEST, str(WEB)], cwd=ROOT, capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    print(run.stdout.strip())


def main() -> None:
    test_files_safe()
    test_package_data()
    test_wheel_ships_web()
    test_app_js_behaviors()
    test_mockup_layout()
    test_runtime()
    test_browser_layout_and_keyboard()


API_FIXTURES = r"""
const frontmatter={title:'<img src=x onerror=evil()>',status:'in-progress',step:'build',plan:'PLAN-006',model:'sonnet',effort:'medium',depends:'TASK-114',workflow:'feature'};
const detail={id:'TASK-115',frontmatter,goal:'Ship the board',criteria:[{text:'Safe <script> text',checked:true},{text:'Responsive',checked:false}],checkpoint:'Next: review',steps:'- build started',reports:'2026-10-30 engineer:\n> Complete',usage:{rows:[{role:'engineer',output:'1234',duration:'30s'}],runs:1,review_rounds:0}};
const counts={planned:2,'in-progress':1,review:0,blocked:0,done:4};
const plan={id:'PLAN-006',title:'Board',status:'active',done:4,total:7};
const summary={name:'omi',plans:[plan],task_counts:counts,po_waiting_count:1};
const totals={runs:1,input:10,output:1234,cache:5000,review_rounds:0};
const dashboard={...summary,kanban:{planned:[], 'in-progress':[detail],review:[],blocked:[],done:[]},po_waiting:[{id:'TASK-115',reason:'po_gate',text:'accept'}],activity:[{id:'TASK-115',text:'build done',time:'2026-10-30 14:52'}],decisions:['- 2026-10-30: Approved'],usage:{totals,models:{sonnet:totals}},sync:{ahead:0,behind:1,dirty:false,last_commit:'abc12345 time title'}};
"""


RUNTIME_TEST = r"""
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
class Element {
  constructor(tag) { this.tagName = tag; this.children = []; this.attrs = {}; this.listeners = {}; this.checked = true; this.text = ''; }
  set textContent(value) { this.text = String(value); this.children = []; }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(''); }
  setAttribute(k, v) { this.attrs[k] = String(v); }
  append(...kids) { this.children.push(...kids); }
  replaceChildren(...kids) { this.text = ''; this.children = kids; this.replacements = (this.replacements || 0) + 1; }
  addEventListener(k, f) { this.listeners[k] = f; }
  focus() { document.activeElement = this; }
}
const elements = Object.fromEntries(['view','nav','auto','status','err','refresh','main'].map(id => [id,new Element('div')]));
function all(root) { return [root, ...root.children.flatMap(all)]; }
function find(root, cls) { return all(root).filter(n => (n.attrs.class || '').split(' ').includes(cls)); }
const document = {
  body: new Element('body'), hidden:false, listeners:{},
  createElement: tag => new Element(tag),
  getElementById: id => elements[id] || all(elements.view).find(n => n.attrs.id === id),
  addEventListener(k,f) { this.listeners[k]=f; }
};
document.activeElement = document.body;
let interval, intervalMs, calls=0, stored={}, fail=false, pending=null;
const localStorage={getItem:k=>stored[k] || null,setItem:(k,v)=>{stored[k]=v;}};
const window={listeners:{},addEventListener(k,f){this.listeners[k]=f;}};
const location={hash:'#/'};
""" + API_FIXTURES + r"""
let data=[summary];
async function fetch(path) {
  calls++;
  if(pending) return pending(path);
  if(fail) throw Error('offline');
  return {ok:true,text:async()=>JSON.stringify(data)};
}
const context=vm.createContext({document,localStorage,window,location,fetch,console,Date,
  setInterval:(f,ms)=>{interval=f;intervalMs=ms;return 1;},clearInterval:()=>{interval=null;}});
const source=fs.readFileSync(process.argv[1],'utf8');
vm.runInContext(source,context);
const invoke=code=>vm.runInContext(code,context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
(async()=>{
  await flush();
  assert.equal(find(elements.view,'pc').length,1);
  assert.equal(find(elements.view,'counts')[0].children.length,5);
  assert.equal(all(elements.view).find(n=>n.tagName==='progress').attrs.value,'4');
  assert(elements.view.textContent.includes('1 dự án'));
  assert.equal(intervalMs,30000);
  const original=elements.view.children[0];
  const focused=find(elements.view,'pc')[0];focused.focus();
  await invoke('route()');
  assert.equal(elements.view.children[0],original);
  assert.equal(document.activeElement,focused);
  fail=true; await invoke('route()');
  assert(elements.err.textContent.includes('Thử lại'));
  assert.equal(elements.view.children[0],original);
  fail=false;await invoke('route()');
  assert.equal(elements.err.textContent,'');
  assert(elements.status.textContent.startsWith('Cập nhật lần cuối '));
  assert.equal(elements.view.children[0],original);
  const before=calls;document.hidden=true;interval();await flush();assert.equal(calls,before);
  document.hidden=false;document.listeners.visibilitychange();await flush();assert.equal(calls,before+1);
  elements.auto.checked=false;elements.auto.listeners.change();assert.equal(interval,null);assert.equal(stored['omi-board-auto'],'off');
  elements.auto.checked=true;elements.auto.listeners.change();assert.equal(intervalMs,30000);
  localStorage.setItem=()=>{throw Error('blocked');};elements.auto.listeners.change();
  data=dashboard;location.hash='#/p/omi';await invoke('route()');
  assert.equal(find(elements.view,'stat').length,4);
  assert.equal(find(elements.view,'col').length,5);
  assert.equal(find(elements.view,'poi').length,1);
  assert.equal(find(elements.view,'card').length,1);
  assert(find(elements.view,'card')[0].textContent.includes(frontmatter.title));
  assert.equal(all(elements.view).filter(n=>n.tagName==='img'||n.tagName==='script').length,0);
  assert.equal(find(elements.view,'card')[0].attrs.href,'#/p/omi/t/TASK-115');
  for(const text of ['Hoạt động','Quyết định','Sử dụng','Trước 0 · Sau 1','abc1234','1.234']) assert(elements.view.textContent.includes(text),text);
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
  assert.equal(all(elements.view).filter(n=>n.tagName==='details').length,1);
  assert.equal(find(elements.view,'steps').length,0);assert(elements.view.textContent.includes('build'));
  data={...detail,workflow_steps:['plan','design','build','review',{id:'accept',gate:'po'}]};await invoke('route()');
  const stepper=find(elements.view,'steps')[0];assert.equal(stepper.children.length,5);
  assert.equal(stepper.children[2].attrs['aria-current'],'step');assert(stepper.textContent.includes('accept · PO'));
  // Late responses from another route cannot replace the current route.
  let finish;
  pending=()=>new Promise(resolve=>{finish=resolve;});const late=invoke('route()');await flush();
  pending=null;data=[];location.hash='#/';await invoke('route()');
  finish({ok:true,text:async()=>JSON.stringify(detail)});await late;
  assert(elements.view.textContent.includes('Chưa có dự án.'));
  data=[summary];await elements.refresh.listeners.click();assert.equal(find(elements.view,'pc').length,1);
  data={...dashboard,po_waiting:[],plans:[],activity:[],decisions:[]};location.hash='#/p/omi';await invoke('route()');
  for(const text of ['Không có việc chờ PO.','Chưa có kế hoạch.','Chưa có hoạt động.','Chưa có quyết định.']) assert(elements.view.textContent.includes(text));
  console.log('ok: API views, mockup DOM, safe text, polling, recovery, focus, storage, races');
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


BROWSER_TEST = r"""
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
let chromium;
try { ({chromium}=require('playwright')); }
catch(e) {
  if(e.code!=='MODULE_NOT_FOUND') throw e;
  console.log('skip test_browser_layout_and_keyboard: playwright missing (360px/390px visual and keyboard checks unverified)');
  process.exit(0);
}
""" + API_FIXTURES + r"""
(async()=>{
  // If Playwright is installed, a missing browser is a test failure, not a silent skip.
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage();
    const errors=[];page.on('pageerror', e=>errors.push(e.message));
    page.on('console', msg=>{if(msg.type()==='error') errors.push(msg.text());});
    await page.route('http://omi.test/**',async route=>{
      const url=new URL(route.request().url());
      if(url.pathname.startsWith('/api/')) {
        const data=url.pathname.endsWith('/tasks/TASK-115')?detail:url.pathname==='/api/projects/omi'?dashboard:[summary];
        return route.fulfill({json:data});
      }
      const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      const types={'index.html':'text/html','app.css':'text/css','app.js':'application/javascript','favicon.svg':'image/svg+xml'};
      assert(types[name],name);
      await route.fulfill({body:fs.readFileSync(path.join(process.argv[1],name)),contentType:types[name],
        headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'"}});
    });
    for(const width of [360,390,1280]) {
      await page.setViewportSize({width,height:900});
      for(const hash of ['#/','#/p/omi','#/p/omi/t/TASK-115']) {
        await page.goto('http://omi.test/'+hash);
        await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
        assert.equal(await page.locator('h1').count(),1);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width} ${hash}`);
        assert.equal(await page.locator('[style]').count(),0);
        assert.equal(await page.locator('#view script, #view img').count(),0);
        if(hash==='#/p/omi') {
          const columns=await page.locator('.col').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().x));
          assert.equal(new Set(columns).size,width<768?1:5);
        }
        // Native keyboard controls and the skip link must work in the real DOM.
        await page.locator('.skip').focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.evaluate(()=>document.activeElement.id),'main');
        await page.locator('#auto').focus();
        const checked=await page.locator('#auto').isChecked();
        await page.keyboard.press('Space');
        assert.equal(await page.locator('#auto').isChecked(),!checked);
        await page.keyboard.press('Space');
        const initial=await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor);
        await page.emulateMedia({colorScheme:'dark'});
        assert.notEqual(await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor),initial);
        await page.emulateMedia({colorScheme:'light'});
        if(hash.includes('/t/')) {
          assert.equal(await page.locator('details').first().getAttribute('open'),'');
          await page.locator('summary').focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('details').first().getAttribute('open'),null);
        }
      }
    }
    assert.deepEqual(errors,[]);
    console.log('ok: browser layouts at 360/390/1280px, dark mode, CSP, keyboard controls');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


if __name__ == "__main__":
    main()
