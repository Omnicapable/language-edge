const {createRequire}=require('node:module');
const path=require('node:path');
const fs=require('node:fs');
const resolveFrom=process.env.LE_NODE_MODULES;
const req=resolveFrom?createRequire(path.join(resolveFrom,'package.json')):require;
const {chromium}=req('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true,...(process.env.LE_BROWSER_CHANNEL?{channel:process.env.LE_BROWSER_CHANNEL}:{})});
 try{
 const errors=[];
 const page=await browser.newPage({viewport:{width:1500,height:1050}});
 page.on('pageerror',e=>errors.push(e.message));
 await page.goto(process.env.LE_URL||'http://127.0.0.1:8877');
 await page.waitForFunction(()=>document.querySelector('#run').options.length>1);
 await page.selectOption('#run','demo-sdxl');
 await page.waitForTimeout(1800);
 await page.locator('#open-create').click();
 await page.selectOption('#device','mps');
 await page.selectOption('#memory-mode','low-memory');
 if(!await page.locator('#create-panel').isVisible())throw Error('Workspace controls did not open');
 await page.selectOption('#device','auto');await page.selectOption('#memory-mode','standard');
 await page.locator('#open-create').click();
 const out=path.resolve('project_admin/screenshots');fs.mkdirSync(out,{recursive:true});
 await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
 await page.getByRole('button',{name:'About this map'}).click();
 if(!await page.locator('#about').isVisible())throw Error('Help dialog did not open');
 await page.getByRole('button',{name:'Close',exact:true}).click();
 if(process.env.LE_EXPECT_MAP==='1'){
  await page.waitForFunction(()=>document.querySelector('#download').disabled===false);
  const points=await page.evaluate(()=>({count:map.points.length,screen:screen.map(p=>({x:p.x,y:p.y,id:p.point.id}))}));
  const box=await page.locator('#canvas').boundingBox();
  const visible=points.screen.find(p=>p.x>20&&p.y>20&&p.x<box.width-20&&p.y<box.height-20);
  await page.mouse.click(box.x+visible.x,box.y+visible.y);
  await page.waitForFunction(()=>!document.querySelector('#selection').hidden);
  await page.screenshot({path:path.join(out,'selected.png'),fullPage:true});
  await page.locator('#mesh').uncheck();await page.locator('#mesh').check();
  await page.locator('#reset').click();
  console.log('Map point count',points.count);
 }
 await page.setViewportSize({width:390,height:844});await page.waitForTimeout(300);
 await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);
 if(overflow)throw Error('Mobile horizontal overflow');
 if(errors.length)throw Error(errors.join('\n'));
 console.log('UI passed: desktop, mobile, help, console, device/memory controls'+(process.env.LE_EXPECT_MAP==='1'?', map selection, envelope, camera':''));
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
