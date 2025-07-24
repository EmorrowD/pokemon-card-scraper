# 🎴 Pokemon TCG Card Scraper

A high-performance Python scraper that downloads all Pokemon Trading Card Game images from [PkmnCards.com](https://pkmncards.com/sets/) for machine learning and computer vision projects.

## ✨ Features

- 🚀 **High-Speed Downloading** - Up to 50x faster than basic scrapers with parallel processing
- 📊 **Progress Tracking** - Real-time progress bars and download statistics
- 🔄 **Smart Resume** - Automatically skips already downloaded cards
- 📈 **Pre-scan Analysis** - Counts total cards before downloading with detailed set statistics
- 🛡️ **Robust Error Handling** - Retry logic, exponential backoff, and graceful failure recovery
- 📁 **Organized Output** - Clean file naming and comprehensive metadata generation
- ⚙️ **Flexible Configuration** - Multiple speed modes and customizable settings

## 🎯 Use Cases

- **Machine Learning Datasets** - Training data for YOLO, CNN, and other computer vision models
- **Card Recognition Apps** - Building Pokemon card identification systems
- **Digital Collections** - Creating comprehensive digital card databases
- **Research Projects** - Academic studies on trading card game imagery

## 📦 Installation

### Prerequisites
- Python 3.7+
- Internet connection

### Setup
```bash
# Clone the repository
git clone https://github.com/EmorrowD/pokemon-card-scraper
cd pokemon-tcg-scraper

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Quick Start

### Basic Usage
```bash
# Download all cards (recommended for first-time users)
python pokemon_card_scraper.py --fast
```

### Advanced Usage
```bash
# Maximum speed mode
python pokemon_card_scraper.py --fast

# Conservative mode (slower but gentler on servers)
python pokemon_card_scraper.py --delay 0.5

# Parallel downloading with custom workers
python pokemon_card_scraper.py --parallel --workers 10

# Skip card counting (start downloading immediately)
python pokemon_card_scraper.py --fast --skip-count
```

## 📊 Sample Output

### Scanning Phase
```
🔢 Counting total cards across all sets...
📊 Scanning sets: 100%|████████| 150/150 [02:30<00:00, 1.2set/s]

📋 SCAN RESULTS:
   Total Sets: 150
   Total Cards: 25,847
   Avg per Set: 172.3

🏆 Largest Sets:
    1. Scarlet & Violet (SVI)                   247 cards
    2. Sun & Moon (SUM)                         234 cards
    3. XY (XY)                                  208 cards
```

### Download Phase
```
💾 Downloading cards: 45%|████▌    | 11,631/25,847 [15:23<18:45, 12.6card/s]
```

### Completion Summary
```
🎉 SCRAPING COMPLETED!
   Expected: 25,847 cards
   Downloaded: 25,234 cards
   Failed: 613 cards
   Success Rate: 97.6%
```

## 📁 Output Structure

```
pokemon_cards/
├── images/                          # All downloaded card images
│   ├── Pikachu_SVI_001.jpg
│   ├── Charizard_PAL_183.jpg
│   └── ...
├── metadata/
│   ├── cards_metadata.json         # Complete card information
│   ├── pokemon_classes.txt         # List of all Pokemon names
│   └── download_summary.txt        # Download statistics
```

### File Naming Convention
Images are named using the format: `{Pokemon_Name}_{Set_Code}_{Card_Number}.jpg`

Examples:
- `Pikachu_SVI_001.jpg` - Pikachu from Scarlet & Violet set, card #001
- `Charizard_ex_PAL_183.jpg` - Charizard ex from Paldea Evolved, card #183

## ⚙️ Configuration Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--delay` | Delay between downloads (seconds) | 0.1 | `--delay 0.5` |
| `--parallel` | Enable parallel downloading | False | `--parallel` |
| `--workers` | Number of parallel workers | 5 | `--workers 10` |
| `--fast` | Fast mode preset (parallel + optimized settings) | False | `--fast` |
| `--skip-count` | Skip initial card counting | False | `--skip-count` |

### Speed Modes Comparison

| Mode | Command | Speed | Use Case |
|------|---------|-------|----------|
| **Conservative** | `python pokemon_card_scraper.py --delay 1` | 1x | Server-friendly |
| **Default** | `python pokemon_card_scraper.py` | 10x | Balanced |
| **Fast** | `python pokemon_card_scraper.py --fast` | 40-50x | Maximum speed |

## 📊 Performance

### Estimated Download Times*
- **~25,000 cards total**
- **Conservative Mode**: ~8-12 hours
- **Default Mode**: ~45-90 minutes
- **Fast Mode**: ~15-30 minutes

*Times vary based on internet connection and server response

## 🛡️ Error Handling

The scraper includes robust error handling:
- **Network Issues**: Automatic retry with exponential backoff
- **Rate Limiting**: Respectful delays and parallel connection limits  
- **Interrupted Downloads**: Resume from where you left off
- **Invalid Images**: Skip and log failed downloads
- **Progress Safety**: Metadata saved periodically

## 📋 Generated Metadata

### cards_metadata.json
Complete information for each downloaded card:
```json
{
  "total_cards": 25234,
  "cards": [
    {
      "pokemon_name": "Pikachu",
      "card_title": "Pikachu · Scarlet & Violet (SVI) #001",
      "card_number": "001",
      "set_name": "Scarlet & Violet (SVI)",
      "set_code": "SVI",
      "local_path": "images/Pikachu_SVI_001.jpg",
      "filename": "Pikachu_SVI_001.jpg"
    }
  ]
}
```

### pokemon_classes.txt
Numbered list of all unique Pokemon (useful for ML training):
```
0: Abra
1: Absol
2: Alakazam
...
```

## 🤖 Machine Learning Integration

The scraper is optimized for ML workflows:
- **Clean Naming**: Consistent file naming for easy programmatic access
- **Metadata Rich**: Complete card information for dataset analysis
- **Class Lists**: Pre-generated class mappings for model training
- **Quality Images**: High-resolution card images suitable for computer vision

## ⚖️ Legal & Ethical Considerations

- **Rate Limiting**: Built-in delays to respect server resources
- **Educational Use**: Designed for educational and research purposes
- **Copyright Notice**: Card images are copyrighted by The Pokémon Company
- **Respectful Scraping**: Implements best practices for web scraping ethics

### Copyright Disclaimer
Pokemon card images are copyrighted by The Pokémon Company, Nintendo, Game Freak, and Creatures. This tool is for educational and research purposes only. Users are responsible for ensuring their use complies with applicable copyright laws.

## 🛠️ Troubleshooting

### Common Issues

**"No set links found!"**
- Check internet connection
- Verify PkmnCards.com is accessible
- Try running with `--delay 1` for slower requests

**High failure rate**
- Reduce parallel workers: `--workers 3`
- Increase delay: `--delay 0.5`
- Check available disk space

**Script interrupted**
- Run the same command again - it will resume automatically
- Check `pokemon_cards/metadata/` for progress information

### Performance Optimization

**For faster downloads:**
- Use SSD storage
- Stable, fast internet connection
- Run during off-peak hours
- Use `--fast` mode

**For server-friendly scraping:**
- Use `--delay 1` or higher
- Avoid `--parallel` mode
- Run during low-traffic periods

## 📝 Requirements

See `requirements.txt` for the complete list:
- `requests>=2.25.1` - HTTP requests
- `beautifulsoup4>=4.9.3` - HTML parsing
- `tqdm>=4.64.0` - Progress bars
- `lxml>=4.6.3` - XML/HTML parser

## 🤝 Contributing

Contributions are welcome! Please feel free to submit issues, feature requests, or pull requests.

### Development Setup
```bash
git clone https://github.com/yourusername/pokemon-tcg-scraper.git
cd pokemon-tcg-scraper
pip install -r requirements.txt
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [PkmnCards.com](https://pkmncards.com/) for providing comprehensive Pokemon TCG data
- The Pokemon TCG community for inspiring this project
- Contributors and users who help improve this tool

---

⭐ **Star this repo if you find it useful!** ⭐ 