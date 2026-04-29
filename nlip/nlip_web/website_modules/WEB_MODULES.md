# Website Modules Documentation

![Status](https://img.shields.io/badge/status-complete-success)

Website modules are Python scripts that interface between the nlip_web client and various e-commerce websites. Each module handles searching, scraping, and parsing product information from a specific online store.

## Table of Contents

- [Overview](#overview)
- [How It Works](#how-it-works)
- [Module Status](#module-status)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Module Structure](#module-structure)
- [Creating a New Module](#creating-a-new-module)
- [Using Modules](#using-modules)
- [Output Format](#output-format)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## Overview

The `website_modules` directory contains individual Python modules, each designed to search and extract product information from a specific e-commerce website. These modules enable the nlip_web application to search products across multiple online stores simultaneously, extract product data like names, prices, images, and links, return standardized JSON format for consistent display, and run searches in parallel for faster results using multi-threading.

### Key Concepts

Each module handles one specific e-commerce website. All modules implement the same `search_product()` function for consistency. The main module runs all store searches simultaneously using parallel execution. All modules return data in a consistent JSON format.

## How It Works

The system follows this flow:

```
User Search Query
       ↓
  Main Module
       ↓
  ┌────┴────┬─────────┬──────────┐
  ↓         ↓         ↓          ↓
Staples  Newegg  Dellelce  Walmart
  ↓         ↓         ↓          ↓
  └────┬────┴─────────┴──────────┘
       ↓
  Aggregated Results
       ↓
  JSON Response
       ↓
  Frontend Display
```

### Step-by-Step Process

1. User enters a search term (e.g., "laptop")
2. Main module receives the query and distributes it to all active modules
3. Each module runs in parallel:
   - Opens the store's website using Selenium
   - Performs the search
   - Scrapes product information using BeautifulSoup
   - Parses and structures the data
4. Results are aggregated into a single JSON response
5. Frontend displays products in an organized layout

## Module Status

| Module | Status | Store | Website | Notes |
|--------|--------|-------|---------|-------|
| Main Module | Complete | All Stores | N/A | Orchestrates all searches |
| Staples CA | Complete | Staples Canada | staples.ca | Fully functional |
| Newegg CA | Complete | Newegg Canada | newegg.ca | Fully functional |
| Dellelce Bookstore | Complete | Dellelce | Custom | Fully functional |
| Walmart CA | Complete | Walmart Canada | walmart.ca | Fully functional |
| Amazon | Complete | Amazon | amazon.com | Fully functional |
| Home Depot | Complete | Home Depot | homedepot.ca | Fully functional |

Status Legend:
- Complete: Fully implemented and tested
- In Progress: Currently being developed
- Needs Review: Requires review/feedback
- Planned: Planned for future development

## Architecture

### Directory Structure

```
website_modules/
├── main_module.py              # Main orchestrator (queries all stores)
├── staples_ca_module.py        # Staples Canada module
├── newegg_ca_module.py         # Newegg Canada module
├── dellelce_bookstore_module.py # Dellelce bookstore module
├── walmart_ca_module.py         # Walmart Canada module
├── amazon_final.py             # Amazon module
├── homeDepotSelen.py           # Home Depot module
└── WEB_MODULES.md             # This documentation file
```

### Main Module Architecture

The `main_module.py` uses ThreadPoolExecutor to run searches in parallel:

```python
# Maximum concurrent threads
MAX_THREADS = 4

# List of active modules
search_modules = [
    dellelce_bookstore_module,
    newegg_ca_module,
    staples_ca_module
]

# Parallel execution
with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
    # Submit all searches simultaneously
    # Collect results as they complete
```

### Individual Module Architecture

Each module follows this pattern:

```python
# 1. Configuration
STORE_NAME = 'store_name'
WEB_ADDRESS = 'https://www.store.com/'
SEARCH_ARG = 'search?query='

# 2. Main search function
def search_product(product_name: str) -> str:
    # Setup Selenium driver
    # Navigate to search page
    # Wait for page load
    # Parse HTML with BeautifulSoup
    # Extract product data
    # Return JSON string
```

## Getting Started

### Prerequisites

Before using website modules, ensure you have:

1. Python 3.10+ installed
2. Poetry package manager
3. Required Python packages:
   ```bash
   poetry add beautifulsoup4 selenium requests
   ```
4. Chrome/Chromium browser (for Selenium)
5. ChromeDriver (automatically managed by Selenium 4+)

### Installation

```bash
# Navigate to project root
cd nlip_web

# Install dependencies
poetry install
poetry add beautifulsoup4 selenium requests
```

### Quick Test

Test a single module:

```bash
# From project root
python3 -m website_modules.staples_ca_module "laptop"
```

Test the main module (all stores):

```bash
# From project root
./run_main_module.sh
# Or:
python3 -m website_modules.main_module "laptop"
```

## Module Structure

### Required Function Signature

Every module must implement this function:

```python
def search_product(product_name: str) -> str:
    """
    Search for products on the store's website.
    
    Args:
        product_name (str): The search query (e.g., "laptop", "wireless mouse")
    
    Returns:
        str: JSON string with format: {"store_name": [product_objects]}
    
    Example:
        >>> result = search_product("laptop")
        >>> import json
        >>> data = json.loads(result)
        >>> print(data["staples_ca"][0]["name"])
    """
    pass
```

### Standard Module Template

```python
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# ===== CONFIGURATION =====
STORE_NAME = 'example_store'
WEB_ADDRESS = 'https://www.example.com/'
SEARCH_ARG = 'search?query='
HTTP_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# ===== MAIN FUNCTION =====
def search_product(product_name: str) -> str:
    """
    Search for products on Example Store.
    """
    # Setup Chrome options
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(f"user-agent={HTTP_HEADERS['User-Agent']}")
    
    # Initialize driver
    driver = webdriver.Chrome(options=options)
    
    try:
        # Build search URL
        search_url = f"{WEB_ADDRESS}{SEARCH_ARG}{product_name}"
        driver.get(search_url)
        
        # Wait for page load
        time.sleep(5)
        
        # Scroll to load content
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Get page source
        html = driver.page_source
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        
        # Extract products
        results = {STORE_NAME: []}
        
        # Find product elements (customize selectors for your store)
        product_elements = soup.select("div.product-item")
        
        for element in product_elements[:10]:  # Limit to 10 results
            name = element.select_one("h3.product-name")
            price = element.select_one("span.price")
            link = element.select_one("a.product-link")
            image = element.select_one("img.product-image")
            
            if name and price:
                results[STORE_NAME].append({
                    "name": name.get_text(strip=True),
                    "price": price.get_text(strip=True),
                    "link": f"{WEB_ADDRESS}{link.get('href', '')}" if link else "N/A",
                    "product_photo": image.get('src', '') if image else None,
                    "description": "No description available",
                    "availability": "In Stock"  # Customize based on store
                })
        
        return json.dumps(results)
        
    finally:
        driver.quit()

# ===== SCRIPT EXECUTION =====
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        results = search_product(sys.argv[1])
        print(results)
    else:
        print("Usage: python module_name.py <search_term>")
```

## Creating a New Module

Follow these steps to add support for a new store:

### Step 1: Create the Module File

```bash
# In website_modules/ directory
touch new_store_module.py
```

### Step 2: Implement the Module

Use the template above and customize:

1. Store Configuration:
   - `STORE_NAME`: Unique identifier (e.g., "bestbuy_ca")
   - `WEB_ADDRESS`: Base URL
   - `SEARCH_ARG`: Search URL pattern

2. CSS Selectors:
   - Inspect the store's HTML structure
   - Find selectors for: product name, price, link, image
   - Test selectors in browser console

3. Data Extraction:
   - Extract all required fields
   - Handle missing data gracefully
   - Clean and format data

### Step 3: Add to Main Module

Edit `main_module.py`:

```python
from . import new_store_module

search_modules = [
    dellelce_bookstore_module,
    newegg_ca_module,
    staples_ca_module,
    new_store_module  # Add your module here
]
```

### Step 4: Test Your Module

```bash
# Test individually
python3 -m website_modules.new_store_module "test product"

# Test with main module
python3 -m website_modules.main_module "test product"
```

### Step 5: Update Documentation

Add your module to the Module Status table above.

## Using Modules

### Programmatic Usage

#### Single Store Search

```python
from website_modules import staples_ca_module
import json

# Search for products
results_json = staples_ca_module.search_product("wireless mouse")
results = json.loads(results_json)

# Access products
for product in results["staples_ca"]:
    print(f"{product['name']}: {product['price']}")
    print(f"Link: {product['link']}\n")
```

#### Multi-Store Search

```python
from website_modules import main_module
import json

# Search all stores
results = main_module.search_product("laptop")

# Results structure:
# {
#   "results": [
#     {"staples_ca": [...]},
#     {"newegg_ca": [...]},
#     {"dellelce_bookstore": [...]}
#   ]
# }

for store_results in results["results"]:
    store_name = list(store_results.keys())[0]
    products = store_results[store_name]
    
    print(f"\n=== {store_name.upper()} ===")
    for product in products[:3]:  # Show first 3
        print(f"  {product['name']} - {product['price']}")
```

### Command Line Usage

```bash
# Single module
python3 -m website_modules.staples_ca_module "laptop"

# All modules (via script)
./run_main_module.sh

# All modules (direct)
python3 -m website_modules.main_module "laptop"
```

### Integration with nlip_web

The modules are automatically used when you:

1. Start the product search server:
   ```bash
   poetry run vite-products
   ```

2. Use the React frontend:
   ```bash
   cd client && npm run dev
   ```

3. Search for products in the web interface

## Output Format

### Single Module Output

Each module returns a JSON string with this structure:

```json
{
  "store_name": [
    {
      "name": "Product Name",
      "price": "$99.99",
      "link": "https://store.com/product/123",
      "product_photo": "https://store.com/images/product.jpg",
      "description": "Product description text",
      "availability": "In Stock",
      "sizes": ["Small", "Medium", "Large"]
    }
  ]
}
```

### Main Module Output

The main module aggregates all store results:

```json
{
  "results": [
    {
      "staples_ca": [
        {
          "name": "Laptop",
          "price": "$999.99",
          "link": "...",
          "product_photo": "...",
          "description": "...",
          "availability": "In Stock"
        }
      ]
    },
    {
      "newegg_ca": [
        {
          "name": "Gaming Laptop",
          "price": "$1299.99",
          "link": "...",
          "product_photo": "...",
          "description": "...",
          "availability": "In Stock"
        }
      ]
    }
  ]
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Product name/title |
| `price` | string | Yes | Product price (formatted as string) |
| `link` | string | Yes | Direct URL to product page |
| `product_photo` | string | Optional | URL to product image |
| `description` | string | Optional | Product description |
| `availability` | string | Optional | Stock status |
| `sizes` | array | Optional | Available sizes/variants |

## Troubleshooting

### Common Issues

#### 1. Module Import Error

**Problem**: `ModuleNotFoundError: No module named 'website_modules'`

**Solution**: 
- Run from project root directory, not from `website_modules/`
- Use: `python3 -m website_modules.module_name` (with `-m` flag)

#### 2. Selenium WebDriver Error

**Problem**: `selenium.common.exceptions.WebDriverException`

**Solution**:
- Ensure Chrome/Chromium is installed
- ChromeDriver is automatically managed in Selenium 4+
- For older versions, download ChromeDriver manually

#### 3. No Results Returned

**Problem**: Module returns empty results

**Solution**:
- Check if website structure changed (CSS selectors may be outdated)
- Verify search URL is correct
- Check if website blocks automated access
- Increase wait times if page loads slowly

#### 4. Timeout Errors

**Problem**: Requests timeout or take too long

**Solution**:
- Increase timeout in Selenium options
- Check internet connection
- Some stores may be slow to respond
- Consider reducing number of concurrent threads

### Debugging Tips

1. Test selectors in browser console:
   ```javascript
   document.querySelectorAll("div.product-item")
   ```

2. Save HTML for inspection:
   ```python
   with open("debug.html", "w") as f:
       f.write(driver.page_source)
   ```

3. Add print statements:
   ```python
   print(f"Found {len(products)} products")
   print(f"First product: {products[0] if products else 'None'}")
   ```

4. Run in non-headless mode:
   ```python
   # Remove or comment out:
   # options.add_argument("--headless=new")
   ```

## Contributing

We welcome contributions. Here's how you can help:

### Adding New Stores

1. Create a new module following the template above
2. Test thoroughly with various search terms
3. Add to `main_module.py`
4. Update this documentation
5. Submit a pull request

### Improving Existing Modules

1. Fix bugs or improve error handling
2. Update selectors if website structure changes
3. Add new product fields if available
4. Optimize performance
5. Improve code documentation

### Documentation Improvements

1. Fix typos or unclear explanations
2. Add more examples
3. Improve troubleshooting section
4. Add diagrams or visual aids
5. Translate to other languages

### Reporting Issues

When reporting issues, please include:

- Module name
- Search term used
- Error message (if any)
- Expected vs actual behavior
- Python version
- Operating system

## Additional Resources

- [Selenium Documentation](https://www.selenium.dev/documentation/)
- [BeautifulSoup Documentation](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
- [NLIP Server](https://github.com/nlip-project/nlip_server) - Required dependency
- [NLIP SDK](https://github.com/nlip-project/nlip_sdk) - Development tools

