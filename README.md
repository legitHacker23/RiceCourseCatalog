 # 🎓 Rice University Academic Advisor

A comprehensive academic advisor system for Rice University students, providing course recommendations, program guidance, and academic planning through an intuitive web interface.

## 📁 Project Structure

```
RiceCatalog/
├── 🚀 streamlit_unified_app.py    # Main app - run with: streamlit run streamlit_unified_app.py
├── 📄 requirements.txt            # Python dependencies
├── 📄 LICENSE                     # MIT License
├── 📄 .gitignore                  # Git ignore rules
├── 
├── 📂 app/                        # Core application components
│   ├── unified_advisor.py         # Main advisor logic
│   ├── intelligence_router.py     # Query routing system
│   ├── response_formatter.py      # Response formatting
│   └── course_recommender.py      # Course recommendation engine
├── 
├── 📂 scrapers/                   # Data collection tools
│   ├── selenium_rice_scraper.py   # Main program scraper (interactive)
│   └── rice_distribution_scraper.py # Distribution courses scraper
├── 
├── 📂 data/                       # All data files
│   ├── raw/                       # Raw scraped data
│   │   ├── rice_programs_*.json   # Program data
│   │   ├── rice_distribution_courses.json # Distribution courses
│   │   └── *.csv, *.json          # Course data files
│   └── processed/                 # Processed data files
└── 
└── 📂 venv/                       # Python virtual environment
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run the Main App
```bash
streamlit run streamlit_unified_app.py
```

### 3. Access the Interface
Open your browser to `http://localhost:8501`

## 🛠️ Tools Available

### 📱 **Main App** (`streamlit_unified_app.py`)
- **Unified chat interface** for all academic questions
- **Intelligent query routing** to appropriate systems
- **Course recommendations** based on student profile
- **Program guidance** with requirements and planning
- **Interactive visualizations** for academic progress

### 🔍 **Scrapers** (`scrapers/`)
- **`selenium_rice_scraper.py`**: Interactive program scraper
  - Scrapes all Rice University programs
  - Interactive mode asks for input when URLs fail
  - Finds actual program links from department pages
  
- **`rice_distribution_scraper.py`**: Distribution courses scraper
  - Scrapes Rice course catalog for distribution credits
  - Categorizes by Distribution Groups I, II, III
  - Includes special designations (Analyzing Diversity, etc.)

### 📊 **Data** (`data/`)
- **Raw data**: Direct scraping results
- **Processed data**: Cleaned and structured data
- **Course files**: CSV and JSON format course data

## 🎯 Features

### 🤖 **Intelligent Advisory**
- Context-aware responses based on student profile
- Multi-level intelligence routing (quick facts vs. detailed analysis)
- Personalized course recommendations

### 📚 **Comprehensive Data**
- All Rice University programs and requirements
- Distribution course catalog with 1,000+ courses
- Program learning outcomes and requirements
- Course prerequisites and descriptions

### 🎨 **Beautiful Interface**
- Clean, modern Streamlit interface
- Interactive visualizations
- Progress tracking and planning tools
- Mobile-responsive design

## 📖 Usage Examples

### Running the Main App
```bash
streamlit run streamlit_unified_app.py
```

### Running Scrapers
```bash
# Interactive program scraper
python scrapers/selenium_rice_scraper.py

# Distribution courses scraper
python scrapers/rice_distribution_scraper.py
```

## 🔧 Technical Details

### Architecture
- **Streamlit** for web interface
- **Selenium** for interactive web scraping
- **Pandas** for data processing
- **Plotly** for visualizations
- **Modular design** with separated concerns

### Data Sources
- Rice University General Announcements
- Rice University Course Catalog
- Department-specific program pages
- Real-time web scraping with validation

## 📄 License

MIT License - See LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**📧 Contact**: For questions or support, please open an issue on GitHub.

**🎓 Rice University**: This project is not officially affiliated with Rice University.