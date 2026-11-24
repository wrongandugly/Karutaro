// Sonda Mercari via Vercel — Chrome enxuto (@sparticuz/chromium) em rede limpa.
// Abre a busca, conta os anuncios renderizados e devolve amostras em JSON.
const chromium = require('@sparticuz/chromium');
const puppeteer = require('puppeteer-core');

module.exports = async (req, res) => {
  const url = 'https://jp.mercari.com/search?keyword=CX-5%20%E3%82%AD%E3%83%A3%E3%83%AA%E3%82%A2';
  let browser;
  try {
    browser = await puppeteer.launch({
      args: chromium.args,
      defaultViewport: chromium.defaultViewport,
      executablePath: await chromium.executablePath(),
      headless: chromium.headless,
    });
    const page = await browser.newPage();
    await page.setExtraHTTPHeaders({ 'Accept-Language': 'ja-JP,ja;q=0.9' });
    await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 45000 });
    await new Promise(r => setTimeout(r, 6000));
    const data = await page.evaluate(() => {
      const as = [...document.querySelectorAll('a[href*="/item/"]')];
      return {
        title: document.title,
        items: as.length,
        samples: as.slice(0, 10)
          .map(a => (a.innerText || '').trim().replace(/\n/g, ' ').slice(0, 120))
          .filter(Boolean),
      };
    });
    res.status(200).json({ ok: data.items > 0, ...data });
  } catch (e) {
    res.status(200).json({ ok: false, error: String(e).slice(0, 300) });
  } finally {
    if (browser) await browser.close();
  }
};
