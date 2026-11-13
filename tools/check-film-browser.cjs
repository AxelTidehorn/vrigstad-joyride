// Uninstrumented game load plus gallery integrity check. Development only.
const {chromium}=require('playwright');
const {spawn}=require('node:child_process');
const fs=require('node:fs');
async function main(){
 const server=spawn('python3',['-m','http.server','8767','--bind','127.0.0.1'],{stdio:'ignore'});
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
 const result={errors:[],note:'Actual built game with no game source, camera or RAF instrumentation (favicon requests receive an empty 204). Default Negative, grain and mist, dynamic daylight fixed at 13:00.'};
 try{
  const page=await browser.newPage({viewport:{width:1280,height:720},deviceScaleFactor:1});
  await page.route('**/favicon.ico',route=>route.fulfill({status:204,body:''}));
  page.on('pageerror',e=>result.errors.push(String(e)));
  page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text())});
  await page.goto('http://127.0.0.1:8767/index.html?time=13',{waitUntil:'load',timeout:120000});
  await page.locator('#go').evaluate(el=>el.click());
  await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
  result.started=await page.locator('#intro').isHidden();
  result.canvas=await page.locator('#gl').evaluate(el=>({width:el.width,height:el.height}));
  const cdp=await page.context().newCDPSession(page);
  const shot=await cdp.send('Page.captureScreenshot',{format:'png',fromSurface:true});
  fs.writeFileSync('docs/film-study/live-default.png',Buffer.from(shot.data,'base64'));
  await page.goto('http://127.0.0.1:8767/docs/film-study/index.html',{waitUntil:'load'});
  result.gallery=await page.evaluate(()=>({images:document.images.length,broken:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src),missingAlt:[...document.images].filter(i=>!i.alt).length,language:document.documentElement.lang}));
  // Resolve lazy images before checking their HTTP responses.
  const imagePaths=await page.locator('img').evaluateAll(els=>els.map(el=>el.src));
  result.gallery.httpErrors=[];
  for(const src of imagePaths){const response=await page.request.get(src);if(!response.ok())result.gallery.httpErrors.push([src,response.status()])}
  if(!result.started||result.errors.length||result.gallery.httpErrors.length||result.gallery.missingAlt)throw Error('browser check failed');
 }finally{fs.writeFileSync('docs/film-study/live-check.json',JSON.stringify(result,null,2));await browser.close();server.kill()}
}
main().catch(e=>{console.error(e);process.exitCode=1});
