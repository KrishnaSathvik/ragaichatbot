// Puppeteer script to test multiple screen sizes
const puppeteer = require('puppeteer');

const screenSizes = [
  { name: 'iPhone SE', width: 320, height: 568 },
  { name: 'iPhone 6/7/8', width: 375, height: 667 },
  { name: 'iPhone XR', width: 414, height: 896 },
  { name: 'iPhone 12 Pro Max', width: 428, height: 926 },
  { name: 'Samsung Galaxy', width: 360, height: 800 },
  { name: 'iPad', width: 768, height: 1024 },
  { name: 'Desktop', width: 1024, height: 768 }
];

async function testResponsiveness() {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  for (const size of screenSizes) {
    await page.setViewport({ width: size.width, height: size.height });
    await page.goto('http://localhost:3000');
    
    // Wait for page to load
    await page.waitForTimeout(2000);
    
    // Take screenshot
    await page.screenshot({
      path: `screenshot-${size.name.replace(/[^a-zA-Z0-9]/g, '-')}.png`,
      fullPage: true
    });
    
    console.log(`✅ Screenshot taken for ${size.name} (${size.width}×${size.height})`);
  }

  await browser.close();
  console.log('🎉 All screenshots taken! Check the files.');
}

// Run the test
testResponsiveness().catch(console.error);
