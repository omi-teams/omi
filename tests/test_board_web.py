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
    # Countdown is a sibling of the label, outside the last-updated live region.
    assert re.search(r'<span id="status"[^>]*></span>\s*<div class="auto-refresh">\s*'
                     r'<label[^>]*><input[^>]*id="auto"[^>]*> Tự làm mới \(30 giây\)</label>\s*'
                     r'<span id="countdown" class="countdown" aria-hidden="true"></span>', html)


def test_mockup_layout() -> None:
    css = (WEB / "app.css").read_text(encoding="utf-8")
    # The approved desktop structures and phone adaptation must remain present.
    for cls in ("bar", "brand", "tools", "switch", "wrap", "panel", "ph", "stats", "stat", "plan",
                "kanban", "col", "colh", "card", "grid2", "feed", "fi", "po", "poi",
                "projects", "pc", "counts", "layout", "main", "side", "steps", "sn", "crit", "ck"):
        assert re.search(r"\." + cls + r"[\s.{:]", css), cls
    for token in ("#f6f6f4", "#1f2421", "#0f6e6e", "prefers-color-scheme: dark", "max-width:767px",
                  "repeat(2,minmax(0,1fr))", "min(340px,100%)", ":focus-visible", "prefers-reduced-motion",
                  "position:sticky;top:0", "scroll-padding-top:", ".usage-summary", ".merged-empty"):
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
const remoteSource={repo:'https:'+'//github.com/omi-teams/omi-state',sha:'abc123456789',fetched_at:'2026-10-30T12:00:00Z',stale:false};
const frontmatter={title:'<img src=x onerror=evil()>',status:'in-progress',step:'build',plan:'PLAN-006',model:'sonnet',effort:'medium',depends:'TASK-114',workflow:'feature'};
const detail={source:remoteSource,id:'TASK-115',frontmatter,goal:'Ship the board',criteria:[{text:'Safe <script> text',checked:true},{text:'Responsive',checked:false}],checkpoint:'Next: review',steps:'- build started',reports:'2026-10-30 engineer:\n> Complete',usage:{rows:[{role:'engineer',output:'1234',duration:'30s'}],runs:1,review_rounds:0}};
const counts={planned:2,'in-progress':1,review:0,blocked:0,done:4};
const plan={id:'PLAN-006',title:'Board',status:'active',done:4,total:7};
const summary={source:remoteSource,name:'omi',branch:'main',plans:[plan],task_counts:counts,po_waiting_count:1};
const totals={runs:1,input:10,output:1234,cache:5000,review_rounds:0};
const dashboard={...summary,kanban:{planned:[], 'in-progress':[detail],review:[],blocked:[],done:[]},po_waiting:[{id:'TASK-115',reason:'po_gate',text:'accept'}],activity:[{id:'TASK-115',text:'build done',time:'2026-10-30 14:52'}],decisions:['- 2026-10-30: Approved'],usage:{totals,models:{sonnet:totals}}};
const workflowDetail={...detail,current_step:'review',workflow_steps:['plan','design','build','review',{id:'accept',gate:'po'},'qa']};
const crowded={...dashboard,kanban:{...dashboard.kanban,done:Array.from({length:4},(_,i)=>({...detail,id:`TASK-${110+i}`,frontmatter:{...frontmatter,status:'done'}}))}};
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
const elements = Object.fromEntries(['view','nav','auto','countdown','status','err','refresh','main','source'].map(id => [id,new Element('div')]));
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
let now=0;
class Clock extends Date { static now() { return now; } }
const localStorage={getItem:k=>stored[k] || null,setItem:(k,v)=>{stored[k]=v;}};
const window={listeners:{},addEventListener(k,f){this.listeners[k]=f;}};
const location={hash:'#/'};
""" + API_FIXTURES + r"""
let data={projects:[summary],source:remoteSource};
let timeouts=[];
async function fetch(path,opts) {
  calls++;
  if(pending) return pending(path,opts);
  if(fail) throw Error('offline');
  return {ok:true,text:async()=>JSON.stringify(data)};
}
const context=vm.createContext({document,localStorage,window,location,fetch,console,Date:Clock,AbortController,
  setTimeout:(f,ms)=>{const t={f,ms};timeouts.push(t);return t;},clearTimeout:t=>{timeouts=timeouts.filter(x=>x!==t);},
  setInterval:(f,ms)=>{interval=f;intervalMs=ms;return 1;},clearInterval:()=>{interval=null;}});
const source=fs.readFileSync(process.argv[1],'utf8');
vm.runInContext(source,context);
const invoke=code=>vm.runInContext(code,context);
const flush=()=>new Promise(resolve=>setImmediate(resolve));
async function advance(seconds) {
  for(let i=0;i<seconds;i++) { now+=1000;if(interval) interval();await flush(); }
}
const countdown=()=>elements.countdown.textContent;
(async()=>{
  await flush();
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
  assert.equal(intervalMs,1000);
  assert.equal(countdown(),'Làm mới sau 30 giây');
  const original=elements.view.children[0];
  const focused=find(elements.view,'pc')[0];focused.focus();
  const initialCalls=calls;
  const replacements=[elements.view.replacements,elements.nav.replacements,elements.status.replacements];
  await advance(5);
  assert.equal(countdown(),'Làm mới sau 25 giây');
  assert.equal(calls,initialCalls);
  assert.deepEqual([elements.view.replacements,elements.nav.replacements,elements.status.replacements],replacements);
  assert.equal(document.activeElement,focused);
  // A manual refresh restarts the deadline, including an unchanged API response.
  await elements.refresh.listeners.click();
  assert.equal(countdown(),'Làm mới sau 30 giây');
  await advance(29);assert.equal(calls,initialCalls+1);
  assert.equal(countdown(),'Làm mới sau 1 giây');
  await advance(1);assert.equal(calls,initialCalls+2);
  assert.equal(countdown(),'Làm mới sau 30 giây');
  await advance(1);assert.equal(countdown(),'Làm mới sau 29 giây');
  await invoke('route()');
  assert.equal(elements.view.children[0],original);
  assert.equal(document.activeElement,focused);
  fail=true; await invoke('route()');
  assert(elements.err.textContent.includes('Thử lại'));
  assert.equal(countdown(),'Làm mới sau 30 giây');
  assert.equal(elements.view.children[0],original);
  fail=false;await invoke('route()');
  assert.equal(elements.err.textContent,'');
  assert(elements.status.textContent.startsWith('Cập nhật lần cuối '));
  assert.equal(elements.view.children[0],original);
  const before=calls;document.hidden=true;document.listeners.visibilitychange();
  assert.equal(countdown(),'Tạm dừng');assert.equal(interval,null);
  await advance(60);assert.equal(calls,before);assert.equal(countdown(),'Tạm dừng');
  document.hidden=false;document.listeners.visibilitychange();await flush();assert.equal(calls,before+1);
  assert.equal(countdown(),'Làm mới sau 30 giây');
  elements.auto.checked=false;elements.auto.listeners.change();assert.equal(interval,null);assert.equal(stored['omi-board-auto'],'off');
  assert.equal(countdown(),'Đã tắt');
  await advance(30);assert.equal(calls,before+1);
  await elements.refresh.listeners.click();assert.equal(calls,before+2);assert.equal(countdown(),'Đã tắt');
  document.hidden=true;document.listeners.visibilitychange();
  document.hidden=false;document.listeners.visibilitychange();await flush();assert.equal(calls,before+2);
  assert.equal(countdown(),'Đã tắt');assert.equal(interval,null);
  elements.auto.checked=true;elements.auto.listeners.change();assert.equal(intervalMs,1000);
  assert.equal(countdown(),'Làm mới sau 30 giây');
  // The next poll is 30 seconds after a slow refresh completes.
  let completeRefresh;
  pending=()=>new Promise(resolve=>{completeRefresh=resolve;});
  const slow=elements.refresh.listeners.click();await advance(35);
  assert.equal(calls,before+3);
  pending=null;completeRefresh({ok:true,text:async()=>JSON.stringify(data)});await slow;
  assert.equal(countdown(),'Làm mới sau 30 giây');
  await advance(29);assert.equal(calls,before+3);
  await advance(1);assert.equal(calls,before+4);
  // A request that never settles is aborted after 10 s, then the error UI shows and polling resumes.
  pending=(path,opts)=>new Promise((_,reject)=>opts.signal.addEventListener('abort',()=>reject(Object.assign(Error('aborted'),{name:'AbortError'}))));
  const hung=elements.refresh.listeners.click();await flush();
  assert.equal(timeouts.length,1);assert.equal(timeouts[0].ms,10000);
  timeouts[0].f();await hung;
  assert(elements.err.textContent.includes('quá thời gian chờ'));assert(elements.err.textContent.includes('Thử lại'));
  assert.equal(timeouts.length,0);assert.equal(countdown(),'Làm mới sau 30 giây');assert.equal(intervalMs,1000);
  pending=null;await advance(30);assert.equal(elements.err.textContent,'');
  // Delayed timer callbacks use elapsed time rather than counting callbacks.
  now+=5000;interval();await flush();assert.equal(countdown(),'Làm mới sau 25 giây');
  localStorage.setItem=()=>{throw Error('blocked');};elements.auto.listeners.change();
  data=dashboard;location.hash='#/p/omi';await invoke('route()');
  assert.equal(find(elements.view,'stat').length,4);
  assert.equal(find(elements.view,'col').length,6); // Five desktop columns plus the phone's merged empty row.
  assert.equal(find(elements.view,'empty-pair').length,2);
  assert.equal(find(elements.view,'merged-empty').length,1);
  assert.equal(find(elements.view,'poi').length,1);
  assert.equal(find(elements.view,'card').length,1);
  assert(find(elements.view,'card')[0].textContent.includes(frontmatter.title));
  assert.equal(all(elements.view).filter(n=>n.tagName==='img'||n.tagName==='script').length,0);
  assert.equal(find(elements.view,'card')[0].attrs.href,'#/p/omi/t/TASK-115');
  for(const text of ['Hoạt động','Quyết định','Sử dụng','abc1234','1.234']) assert(elements.view.textContent.includes(text),text);
  assert(!elements.view.textContent.includes('/state/projects/omi'));
  for(const text of ['✓ Sạch','Trước ','Sau ','Commit cuối']) assert(!elements.view.textContent.includes(text),text);
  assert.equal(find(elements.view,'usage-summary')[0].textContent,'1 lượt · 1.234 output');
  data=crowded;await invoke('route()');
  const more=find(elements.view,'more')[0];assert.equal(more.tagName,'details');
  assert.equal(more.children[0].textContent,'+ 2 task khác');
  assert.equal(more.children[0].tagName,'summary');
  assert.equal(more.children[1].attrs.href,'#/p/omi/t/TASK-112');
  assert.equal(more.children[2].attrs.href,'#/p/omi/t/TASK-113');
  assert.equal(find(elements.view,'col-done')[0].children.filter(n=>n.tagName==='a').length,2);
  data={...dashboard,kanban:{...dashboard.kanban,review:[detail]}};await invoke('route()');
  assert.equal(find(elements.view,'merged-empty').length,0);
  assert.equal(find(elements.view,'empty-pair').length,0);
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
  assert.equal(all(elements.view).filter(n=>n.tagName==='details').length,1);
  assert.equal(find(elements.view,'steps').length,0);assert(elements.view.textContent.includes('build'));
  data=workflowDetail;await invoke('route()');
  const stepper=find(elements.view,'steps')[0];assert.equal(stepper.children.length,6);
  assert.equal(stepper.children[3].attrs['aria-current'],'step');assert(stepper.textContent.includes('accept · PO'));
  assert(elements.view.textContent.includes('Bước 4/6'));
  assert.equal(find(stepper,'done').length,3);
  data={...workflowDetail,current_step:'unknown',frontmatter:{...frontmatter,step:'unknown'}};await invoke('route()');
  assert(!elements.view.textContent.includes('Bước 0/'));
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
  console.log('ok: API views, mockup DOM, safe text, countdown ticks/resets/off/hidden, polling, recovery, focus, storage, races');
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
        const data=url.pathname.endsWith('/tasks/TASK-115')?workflowDetail:url.pathname==='/api/projects/omi'?crowded:{projects:[summary],source:remoteSource};
        return route.fulfill({json:data});
      }
      const name=url.pathname==='/'?'index.html':url.pathname.slice(1);
      const types={'index.html':'text/html','app.css':'text/css','app.js':'application/javascript','favicon.svg':'image/svg+xml'};
      assert(types[name],name);
      await route.fulfill({body:fs.readFileSync(path.join(process.argv[1],name)),contentType:types[name],
        headers:{'Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self'"}});
    });
    for(const width of [360,390,768,1280]) {
      await page.setViewportSize({width,height:900});
      for(const hash of ['#/','#/p/omi','#/p/omi/t/TASK-115']) {
        await page.goto(`http://omi.test/?width=${width}&page=${encodeURIComponent(hash)}${hash}`);
        await page.locator('#status').filter({hasText:'Cập nhật lần cuối'}).waitFor();
        assert.equal(await page.locator('h1').count(),1);
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`overflow ${width} ${hash}`);
        assert.equal(await page.locator('[style]').count(),0);
        assert.equal(await page.locator('#view script, #view img').count(),0);
        const header=await page.locator('.top').boundingBox();
        assert(await page.locator('#countdown').isVisible());
        assert.equal(await page.locator('#countdown').getAttribute('aria-hidden'),'true');
        assert.equal(await page.locator('#countdown').evaluate(n=>n.closest('[aria-live], [role="status"], [role="alert"]')),null);
        const countdownBox=await page.locator('#countdown').boundingBox();
        const switchBox=await page.locator('.switch').boundingBox();
        if(width<768) {
          assert.equal(countdownBox.x,switchBox.x);
          assert(countdownBox.y>=switchBox.y+switchBox.height);
        } else assert(countdownBox.x>=switchBox.x+switchBox.width);
        assert(countdownBox.y+countdownBox.height<=header.y+header.height);
        assert.equal(await page.locator('.top').evaluate(n=>getComputedStyle(n).position),'sticky');
        assert(await page.locator('html').evaluate(n=>parseFloat(getComputedStyle(n).scrollPaddingTop))>header.height);
        if(width<768) assert(header.height<150,'compact phone header');
        if(hash==='#/p/omi') {
          const columns=await page.locator('.col:visible').evaluateAll(nodes=>nodes.map(n=>n.getBoundingClientRect().x));
          assert.equal(new Set(columns).size,width<768?1:5);
          assert.equal(columns.length,width<768?4:5);
          assert.equal(await page.locator('.merged-empty').isVisible(),width<768);
          assert.equal(await page.locator('.usage-summary').isVisible(),width<768);
          assert.equal(await page.locator('.usage .scroll').isVisible(),width>=768);
          const overflow=page.locator('.more summary');
          assert.equal(await page.locator('.col-done .card:visible').count(),2);
          await overflow.focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('.col-done .card:visible').count(),4);
          await page.keyboard.press('Tab');
          assert.equal(await page.evaluate(()=>document.activeElement.getAttribute('href')),'#/p/omi/t/TASK-112');
          assert((await page.locator('.top').boundingBox()).y===0,'header stays pinned after keyboard scroll');
          await overflow.evaluate(n=>n.scrollIntoView());
          assert((await overflow.boundingBox()).y>=(await page.locator('.top').boundingBox()).height,'anchored element clears header');
          await overflow.focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('.col-done .card:visible').count(),2);
        }
        // Native keyboard controls and the skip link must work in the real DOM.
        await page.locator('.skip').focus();
        await page.keyboard.press('Enter');
        assert.equal(await page.evaluate(()=>document.activeElement.id),'main');
        assert((await page.locator('#main').boundingBox()).y>=(await page.locator('.top').boundingBox()).height,'skip target clears header');
        await page.locator('#auto').focus();
        const checked=await page.locator('#auto').isChecked();
        await page.keyboard.press('Space');
        assert.equal(await page.locator('#auto').isChecked(),!checked);
        assert.equal(await page.locator('#countdown').innerText(),'Đã tắt');
        await page.keyboard.press('Space');
        const initial=await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor);
        await page.emulateMedia({colorScheme:'dark'});
        assert.notEqual(await page.locator('body').evaluate(n=>getComputedStyle(n).backgroundColor),initial);
        await page.emulateMedia({colorScheme:'light'});
        if(hash.includes('/t/')) {
          assert.equal(await page.locator('.steps li').count(),6);
          assert.deepEqual(await page.locator('.steps [aria-current="step"] span').allTextContents(),['4','review']);
          assert(await page.locator('#view').innerText().then(text=>text.includes('Bước 4/6')));
          assert.equal(await page.locator('details').first().getAttribute('open'),'');
          await page.locator('summary').focus();await page.keyboard.press('Enter');
          assert.equal(await page.locator('details').first().getAttribute('open'),null);
        }
      }
    }
    assert.deepEqual(errors,[]);
    console.log('ok: browser layouts at 360/390/768/1280px, sticky header, phone summaries, overflow disclosure, dark mode, CSP, keyboard controls');
  } finally { await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
"""


if __name__ == "__main__":
    main()
