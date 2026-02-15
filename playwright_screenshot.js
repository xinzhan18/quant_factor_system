const { chromium } = require('playwright');
const path = require('path');

(async () => {
    const browser = await chromium.launch({
        headless: true
    });
    
    const page = await browser.newPage();
    
    const htmlPath = path.resolve(__dirname, 'feishu_api_examples.html');
    await page.goto(`file://${htmlPath}`, {
        waitUntil: 'networkidle'
    });
    
    const outputPath = path.resolve(__dirname, 'feishu_api_examples.png');
    await page.screenshot({
        path: outputPath,
        fullPage: true
    });
    
    console.log(`Screenshot saved to: ${outputPath}`);
    
    await browser.close();
})();