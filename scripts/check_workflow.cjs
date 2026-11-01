const {createRequire}=require('node:module');const path=require('node:path');const fs=require('node:fs');
const req=process.env.LE_NODE_MODULES?createRequire(path.join(process.env.LE_NODE_MODULES,'package.json')):require;
const {chromium}=req('playwright');
(async()=>{
 const b=await chromium.launch({headless:true,channel:process.env.LE_BROWSER_CHANNEL||'msedge'});
 try{
 const p=await b.newPage({viewport:{width:1500,height:1050}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
 await p.goto('http://127.0.0.1:8877');await p.waitForFunction(()=>document.querySelector('#run')?.options.length>1);
 await p.selectOption('#run','demo-sdxl');await p.waitForFunction(()=>!document.querySelector('#download').disabled);
 const old=await p.evaluate(async()=>{let s=await(await fetch('/api/state')).json();return s.job.id});
 const files=fs.readdirSync('runs/demo-sdxl/images');
 await p.locator('#images').setInputFiles(path.resolve('runs/demo-sdxl/images',files[0]));
 await p.waitForFunction(async prior=>{let s;try{s=await(await fetch('/api/state')).json()}catch{return false}if(s.job.id!==prior&&s.job.status==='error')throw Error(s.job.message);return s.job.id!==prior&&s.job.status==='complete'},old,{timeout:120000});
 await p.locator('#seeds').fill('43');await p.locator('#query').fill('A luminous garden of glass flowers at night');
 const beforeQuery=await p.evaluate(async()=>{let s=await(await fetch('/api/state')).json();return s.job.id});
 await p.locator('#generate-query').click();
 await p.waitForFunction(async prior=>{let s;try{s=await(await fetch('/api/state')).json()}catch{return false}if(s.job.id!==prior&&s.job.status==='error')throw Error(s.job.message);return s.job.id!==prior&&s.job.status==='complete'},beforeQuery,{timeout:120000});
 if(errors.length)throw Error(errors.join('\n'));
 console.log('UI workflow passed: image upload, query generation/resume, job completion.');
 }finally{await b.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
