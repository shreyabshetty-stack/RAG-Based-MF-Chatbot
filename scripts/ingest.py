import urllib.request
import ssl
import json
import re
import os
from datetime import datetime

# Whitelisted Groww URLs for HDFC Mutual Funds
URLS = [
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-elss-tax-saver-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth"
]

def scrape_fund_data(url):
    print(f"Fetching data from: {url}")
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    ctx = ssl._create_unverified_context()
    
    try:
        with urllib.request.urlopen(req, context=ctx) as response:
            html = response.read().decode('utf-8')
            
        next_match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
        if not next_match:
            print(f"Error: Could not find __NEXT_DATA__ script tag for {url}")
            return None
            
        data = json.loads(next_match.group(1))
        
        # Access nested props -> pageProps -> mfServerSideData
        page_props = data.get('props', {}).get('pageProps', {})
        server_data = page_props.get('mfServerSideData', {})
        
        if not server_data:
            print(f"Error: mfServerSideData is empty for {url}")
            return None
            
        # Extract required factual attributes
        scheme_name = server_data.get('scheme_name')
        expense_ratio = server_data.get('expense_ratio')
        exit_load = server_data.get('exit_load')
        min_sip = server_data.get('min_sip_investment')
        benchmark = server_data.get('benchmark_name') or server_data.get('benchmark')
        risk = server_data.get('risk') or server_data.get('nfo_risk')
        fund_manager = server_data.get('fund_manager')
        launch_date = server_data.get('launch_date')
        aum = server_data.get('aum')
        isin = server_data.get('isin')
        
        # Hardcode ELSS Lock-in check
        # Under Section 80C, ELSS funds have a mandatory 3-year lock-in period.
        is_elss = "elss" in url.lower() or "tax-saver" in url.lower() or (scheme_name and "elss" in scheme_name.lower())
        elss_lock_in = "3 years" if is_elss else "Nil"
        
        # Clean strings helper
        def clean_str(val):
            return str(val).strip() if val is not None else None

        fund_details = {
            "scheme_name": clean_str(scheme_name),
            "source_url": url,
            "isin": clean_str(isin),
            "expense_ratio": f"{clean_str(expense_ratio)}%" if expense_ratio else None,
            "exit_load": clean_str(exit_load),
            "min_sip_investment": min_sip,
            "elss_lock_in": elss_lock_in,
            "risk_classification": clean_str(risk),
            "benchmark_index": clean_str(benchmark),
            "fund_manager": clean_str(fund_manager),
            "launch_date": clean_str(launch_date),
            "aum_in_cr": aum,
            "last_updated": datetime.now().strftime("%Y-%m-%d")
        }
        
        # Log parsed output
        print(f"Successfully scraped: {scheme_name}")
        print(f"  Expense Ratio: {fund_details['expense_ratio']}")
        print(f"  Exit Load: {fund_details['exit_load']}")
        print(f"  Min SIP: {fund_details['min_sip_investment']}")
        print(f"  ELSS Lock-in: {fund_details['elss_lock_in']}")
        print(f"  Risk: {fund_details['risk_classification']}")
        print(f"  Benchmark: {fund_details['benchmark_index']}")
        print("-" * 50)
        
        return fund_details
        
    except Exception as e:
        print(f"Failed to scrape {url}. Error: {e}")
        return None

def main():
    print("Starting Mutual Fund Corpus Ingestion Pipeline...")
    corpus = []
    
    for url in URLS:
        fund_data = scrape_fund_data(url)
        if fund_data:
            corpus.append(fund_data)
            
    if not corpus:
        print("Error: No data scraped. Corpus is empty.")
        return
        
    # Ensure target directory exists
    os.makedirs("data", exist_ok=True)
    
    # Save parsed corpus
    with open("data/raw_funds.json", "w", encoding="utf-8") as f:
        json.dump(corpus, f, indent=2)
        
    print(f"Corpus ingestion complete. Saved {len(corpus)} funds to data/raw_funds.json")

if __name__ == "__main__":
    main()
