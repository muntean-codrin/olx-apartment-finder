@echo off
echo Starting scraper and bot in parallel...

start "Scraper" cmd /k "cd scraper && python scrape.py"
start "Bot" cmd /k "cd bot && node index.js"

echo All processes launched.
