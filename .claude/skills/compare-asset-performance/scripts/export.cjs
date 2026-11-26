const {resolve} = require('node:path');
const {pathToFileURL} = require('node:url');
const {spawn} = require('node:child_process');
const {once} = require('node:events');
const { existsSync } = require('node:fs');

async function main() {
  const [html, period, output] = process.argv.slice(2);
  if (!html || !output || !['week', 'full'].includes(period)) throw Error('Usage: export.cjs interactive.html week|full output.mp4');
  const browser = await require('puppeteer-core').launch({
    executablePath: process.env.CHROME_PATH || ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/google-chrome','/usr/bin/chromium',String.raw`C:\Program Files\Google\Chrome\Application\chrome.exe`].find(existsSync),
    headless: true, args: ['--disable-gpu']
  });
  let encoder;
  try {
    const page = await browser.newPage();
    await page.setViewport({width:1280,height:720});
    await page.goto(pathToFileURL(resolve(html)).href);
    if (period==='week' && await page.$eval('#week', b=>b.disabled)) throw Error('Insufficient prior-week history');
    await page.addStyleTag({content:'.controls,.tabs{visibility:hidden}'});
    encoder = spawn('ffmpeg',['-v','error','-y','-f','image2pipe','-framerate','30','-i','pipe:0','-c:v','libx264','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',output],{stdio:['pipe','inherit','inherit']});
    const finished = once(encoder,'exit');
    const drawingFrames=period==='week'?120:195;
    const totalFrames=drawingFrames+75;
    for(let frame=0; frame<totalFrames; frame++) {
      await page.evaluate((v,p)=>window.setComparisonFrame(v,p), Math.min(frame/(drawingFrames-1),1), period);
      const jpeg = await page.screenshot({type:'jpeg',quality:96});
      if(!encoder.stdin.write(jpeg)) await once(encoder.stdin,'drain');
    }
    encoder.stdin.end();
    if((await finished)[0]!==0) throw Error('FFmpeg could not write the export');
  } finally {
    if(encoder && encoder.exitCode===null) encoder.kill();
    await browser.close();
  }
}
main().catch(e=>{console.error(e.message);process.exitCode=1});
