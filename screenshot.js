const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

(async () => {
    const browser = await puppeteer.launch({
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    });
    
    const page = await browser.newPage();
    
    const htmlPath = path.resolve(__dirname, 'feishu_api_examples.html');
    await page.goto(`file://${htmlPath}`, {
        waitUntil: 'networkidle0'
    });
    
    const outputPath = path.resolve(__dirname, 'feishu_api_examples.png');
    await page.screenshot({
        path: outputPath,
        fullPage: true
    });
    
    console.log(`Screenshot saved to: ${outputPath}`);
    
    await browser.close();
})();