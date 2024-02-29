const { Readability } = require("@mozilla/readability");
const { JSDOM } = require("jsdom");

// Usage: node extract_stdout.js <html>

function extractContent(page) {
  const reader = new Readability(page.window.document);
  const content = reader.parse();
  process.stdout.write(JSON.stringify(content), process.exit);
}

if (!process.argv[2]) {
  console.error("Error: URL argument missing.");
  process.exit(1);
}

const html = process.argv[2];
const page = new JSDOM(html);
extractContent(page);
