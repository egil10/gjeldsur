# Norway Macro Clock

A living, automated dashboard that displays Norway's key economic indicators in a dense "macro clock" style. Data is fetched from official sources (SSB, Norges Bank, NAV, Skatteetaten), cleaned to a standard schema, and rendered in a responsive web interface.

## 🎯 Vision

A real-time dashboard that looks like a dense "macro clock" with many compact tiles showing Norway's key indicators (level + sparkline + YoY/MoM + last updated). Political periods are shaded/colored via configuration, and the site publishes to GitHub Pages via Actions on push and monthly (cron).

## 🏗️ Architecture

### Data Pipeline
- **Backend**: Python 3.11+ with pandas, requests, matplotlib
- **Adapters**: Resilient network stack for SSB, Norges Bank, NAV, Skatteetaten
- **Processing**: Standardized data schema with JSON/CSV/Parquet outputs
- **Validation**: Automated data quality checks and schema validation

### Frontend
- **Framework**: Vite + React + TypeScript
- **Charts**: ECharts for performant sparklines
- **Styling**: Modern CSS with high contrast and accessibility
- **Deployment**: Static export to GitHub Pages

### Infrastructure
- **CI/CD**: GitHub Actions with monthly cron and push triggers
- **Hosting**: GitHub Pages with automatic deployments
- **Data Storage**: Versioned JSON/CSV/Parquet files in `/data/`

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git

### Local Development

1. **Clone and setup**:
   ```bash
   git clone <your-repo-url>
   cd gjeldsur
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**:
   ```bash
   cd web
   npm install
   ```

4. **Generate mock data** (if APIs are unavailable):
   ```bash
   python scripts/dev_seed.py
   ```

5. **Run the data pipeline**:
   ```bash
   python pipelines/run_all.py --seed
   ```

6. **Start the development server**:
   ```bash
   cd web
   npm run dev
   ```

7. **Open your browser** to `http://localhost:3000`

### Production Build

1. **Build the React app**:
   ```bash
   cd web
   npm run build
   ```

2. **Create the site directory**:
   ```bash
   mkdir -p site
   cp -r web/dist/* site/
   cp -r data site/
   cp -r config site/
   cp -r plots site/ 2>/dev/null || true
   ```

## 🌐 Deployment

### 1️⃣ Auto-deploy via GitHub Actions (recommended)

This is the **recommended approach** — your repo has a `.github/workflows/deploy.yml` that:

- **Fetches data** → builds plots → builds site
- **Pushes the build folder** to GitHub Pages
- **Runs automatically** on push and on schedule (monthly)

You only need to commit your code; Actions takes care of the site.

**To enable:**
1. Push your code to GitHub
2. Go to repository **Settings → Pages**
3. Set **Source** to **"GitHub Actions"**
4. The workflow will automatically run and deploy to GitHub Pages

**What happens:**
- ✅ **On push to `main`**: Automatically rebuilds and deploys
- ✅ **Monthly cron**: Updates data and redeploys (1st of each month at 6:00 UTC)
- ✅ **Manual trigger**: Go to Actions tab → "Deploy to GitHub Pages" → "Run workflow"

### 2️⃣ Manual Deployment (for testing)

If you want to test locally before pushing:

1. **Build the project**:
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Run data pipeline
   python pipelines/run_all.py --seed
   
   # Install Node.js dependencies and build frontend
   cd web
   npm install
   npm run build
   cd ..
   ```

2. **Create the site directory**:
   ```bash
   mkdir -p site
   cp -r web/dist/* site/
   cp -r data site/
   cp -r config site/
   cp -r plots site/ 2>/dev/null || true
   ```

3. **Test locally**:
   ```bash
   cd site
   python -m http.server 8000
   # Open http://localhost:8000
   ```

### 3️⃣ Quick Test with Mock Data

If you want to test without real API calls:
```bash
python pipelines/run_all.py --seed
```
This generates mock data for all indicators.

## 📊 Adding New Indicators

### 1. Update the Catalog

Add your indicator to `pipelines/catalog.yaml`:

```yaml
- id: your_indicator
  adapter: ssb_px  # or norges_bank, nav, skatteetaten
  params:
    dataset: 1234
    lang: en
    date_field_guess: ["Month", "time", "Tid"]
    value_field_guess: ["value", "Your indicator name"]
  transform: your_indicator_standardize
  out_dir: data/your_indicator
  schedule: monthly
  title: "Your Indicator Title"
  unit: "Unit of measurement"
  frequency: "monthly"
  source:
    name: "SSB"
    table: "1234"
    url: "https://www.ssb.no/en/statbank/table/1234"
  politics_overlay: true
```

### 2. Create the Indicator Module

Create `pipelines/indicators/your_indicator_ssb_1234.py`:

```python
import pandas as pd
from pathlib import Path
from adapters.ssb_px import fetch_and_normalize

OUT = Path("data/your_indicator")
OUT.mkdir(parents=True, exist_ok=True)

def fetch(params):
    return fetch_and_normalize(
        dataset=params["dataset"],
        lang=params.get("lang", "en"),
        date_field_guess=params.get("date_field_guess"),
        value_field_guess=params.get("value_field_guess")
    )

def enrich(df):
    # Your enrichment logic here
    s = df["value"]
    return {
        "latest_value": float(s.iloc[-1]),
        "mom_pct": float((s.iloc[-1]/s.iloc[-2]-1)*100) if len(s)>1 else None,
        "yoy_pct": float((s.iloc[-1]/s.iloc[-13]-1)*100) if len(s)>13 else None,
        "min": float(s.min()),
        "max": float(s.max())
    }

def write_outputs(df, meta, out_dir=OUT):
    # Your output writing logic here
    # See cpi_ssb_03013.py for reference implementation
    pass
```

### 3. Test Your Indicator

```bash
# Test the pipeline
python pipelines/run_all.py --dry-run

# Verify data quality
python scripts/verify_data.py --file data/your_indicator/latest.json

# Run the full pipeline
python pipelines/run_all.py
```

## 🔧 Configuration

### Environment Variables

Copy `env.example` to `.env` and configure:

```bash
# TLS Configuration
INSECURE=0  # Set to 1 to bypass TLS verification (for corporate proxies)
REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt  # Custom CA bundle path

# Development mode
DEV_SEED=0  # Set to 1 to use mock data if APIs fail
```

### Political Periods

Edit `config/governments.json` to configure political periods and party colors:

```json
{
  "parties": {
    "Ap": {"name": "Arbeiderpartiet", "color": "#E03C31"},
    "H": {"name": "Høyre", "color": "#005AA3"}
  },
  "periods": [
    {
      "start": "2021-10-14",
      "end": "9999-12-31",
      "coalition": ["Ap", "Sp"],
      "description": "Current government"
    }
  ]
}
```

## 🛠️ Troubleshooting

### TLS Issues

If you encounter TLS/SSL errors:

1. **Corporate proxy**: Set `INSECURE=1` in your `.env` file
2. **Custom CA bundle**: Set `REQUESTS_CA_BUNDLE=/path/to/ca-bundle.crt`
3. **System CA bundle**: Ensure `certifi` is installed and up to date

### Data Fetching Issues

1. **API failures**: Use `--seed` flag to generate mock data
2. **Network timeouts**: Check your internet connection and firewall settings
3. **Rate limiting**: The adapters include exponential backoff retries

### Build Issues

1. **Node.js dependencies**: Run `npm ci` in the `web/` directory
2. **Python dependencies**: Ensure you're using Python 3.11+ and run `pip install -r requirements.txt`
3. **TypeScript errors**: Check that all TypeScript files compile correctly

### Deployment Issues

1. **GitHub Pages**: Ensure the repository has Pages enabled and the workflow has proper permissions
2. **Build artifacts**: Check that the `site/` directory is created correctly
3. **Data files**: Verify that `/data/` and `/config/` are copied to the site directory

## 📈 Performance

### Optimization Strategies

- **Lazy loading**: Tiles mount in batches using IntersectionObserver
- **Caching**: Aggressive client-side caching with ETag support
- **Bundle size**: ECharts is loaded separately to reduce initial bundle size
- **Data size**: Each `latest.json` is kept under ~150KB by trimming series

### Monitoring

- **Data quality**: Run `python scripts/verify_data.py` regularly
- **Build performance**: Monitor GitHub Actions execution times
- **User experience**: Check Core Web Vitals in browser dev tools

## 🔒 Security

- **No secrets**: All data sources are public APIs
- **TLS verification**: Enabled by default with configurable bypass
- **Input validation**: All data is validated against schemas
- **XSS protection**: React automatically escapes user input

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make your changes and test thoroughly
4. Run the verification script: `python scripts/verify_data.py`
5. Commit your changes: `git commit -am 'Add your feature'`
6. Push to the branch: `git push origin feature/your-feature`
7. Submit a pull request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- **Data Sources**: SSB, Norges Bank, NAV, Skatteetaten
- **Technologies**: React, ECharts, Pandas, GitHub Actions
- **Inspiration**: US Debt Clock style dashboards

## 📞 Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing GitHub issues
3. Create a new issue with detailed information about your problem

---

**Norway Macro Clock** - Real-time economic indicators for Norway 🇳🇴