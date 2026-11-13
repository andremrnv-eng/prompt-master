// node cover.js -> cover.png (1080x1920) built from the video's own renderer
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => { console.error(e.message); process.exitCode = 1; });
  await p.goto('file://' + path.join(__dirname, 'index.html'));
  await p.evaluate(() => window.INIT);
  const data = await p.evaluate(() => {
    const mk = () => { const c = document.createElement('canvas'); c.width = 1080; c.height = 1920; return c; };
    const before = mk(), after = mk();
    const z = 105, y = 4.67;
    cam = () => ({ x: 2.57, y, z, r: 0 }); frameAt(0.12); before.getContext('2d').drawImage(OUT, 0, 0);
    cam = () => ({ x: -2.57, y, z, r: 0 }); frameAt(52.05); after.getContext('2d').drawImage(OUT, 0, 0);
    const c = mk(), g = c.getContext('2d');
    g.drawImage(before, 0, 0);
    // diagonal split: after on the right
    g.save(); g.beginPath(); g.moveTo(640, 0); g.lineTo(1080, 0); g.lineTo(1080, 1920); g.lineTo(440, 1920); g.closePath(); g.clip();
    g.drawImage(after, 0, 0); g.restore();
    g.strokeStyle = '#fff'; g.lineWidth = 14; g.beginPath(); g.moveTo(640, 0); g.lineTo(440, 1920); g.stroke();
    const F = '"Inter Display","Inter",sans-serif';
    const pill = (x, y, w, h, r, f) => { g.fillStyle = f; g.beginPath(); g.roundRect(x, y, w, h, r); g.fill(); };
    // labels on halves
    g.font = `900 54px ${F}`; g.textAlign = 'center';
    pill(60, 1490, 330, 92, 30, 'rgba(16,30,22,.85)'); g.fillStyle = '#FF4D4D'; g.fillText('БЫЛО', 225, 1555);
    pill(690, 1490, 330, 92, 30, 'rgba(16,30,22,.85)'); g.fillStyle = '#79E08A'; g.fillText('СТАЛО', 855, 1555);
    // headline block
    pill(60, 250, 960, 560, 44, 'rgba(16,30,22,.88)');
    g.fillStyle = '#79E08A'; g.fillRect(100, 250, 880, 10);
    g.fillStyle = '#fff'; g.font = `900 118px ${F}`;
    g.fillText('СТАРАЯ', 540, 400); g.fillText('ЯБЛОНЯ', 540, 520);
    g.fillStyle = '#FFC93C'; g.font = `900 92px ${F}`; g.fillText('3 года — 3 шага', 540, 650);
    g.fillStyle = '#FF4D4D'; g.font = `800 58px ${F}`; g.fillText('не режь за один раз', 540, 750);
    // bottom badge
    pill(190, 1640, 700, 120, 34, '#6b4a30'); g.fillStyle = '#fff3d6'; g.font = `900 64px ${F}`; g.fillText('ТЕТРАДЬ ДАЧНИКА', 540, 1722);
    return c.toDataURL('image/png');
  });
  fs.writeFileSync(path.join(__dirname, 'cover.png'), Buffer.from(data.split(',')[1], 'base64'));
  await b.close();
})();
