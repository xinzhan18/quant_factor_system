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
    
    const outputPath = path.resolve(__dirname, 'feishu_api_examples.pdf');
    await page.pdf({
        path: outputPath,
        format: 'A4',
        printBackground: true,
        margin: {
            top: '20px',
            right: '20px',
            bottom: '20px',
            left: '20px'
        }
    });
    
    console.log(`PDF saved to: ${outputPath}`);
    
    await browser.close();
})();