#!/usr/bin/env python3
"""
Pokemon Card Image Scraper for YOLO Training Dataset
Scrapes all Pokemon card images from pkmncards.com/sets/
"""

import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin, urlparse
import json
from pathlib import Path
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PokemonCardScraper:
    def __init__(self, base_url="https://pkmncards.com/sets/", download_dir="pokemon_cards"):
        self.base_url = base_url
        self.download_dir = Path(download_dir)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create directories
        self.download_dir.mkdir(exist_ok=True)
        (self.download_dir / "images").mkdir(exist_ok=True)
        (self.download_dir / "metadata").mkdir(exist_ok=True)
        
        # Track downloaded cards and metadata
        self.downloaded_cards = []
        self.failed_downloads = []
        
        # Thread lock for thread-safe operations
        self.lock = threading.Lock()
        
        # Progress tracking
        self.total_cards_expected = 0
        self.progress_bar = None
        
    def get_page_content(self, url, retries=3):
        """Get page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to get {url} after {retries} attempts")
                    return None
                    
    def extract_set_links(self):
        """Extract all set links from the main page"""
        logger.info("Extracting set links from main page...")
        
        response = self.get_page_content(self.base_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        set_links = []
        
        # Find all links in the sets sections
        # Looking for links that contain set names and codes
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Filter for set links (they usually contain set codes in parentheses)
            if (href and href.startswith('https://pkmncards.com/set/') and 
                text and '(' in text and ')' in text):
                set_links.append({
                    'url': href,
                    'name': text,
                    'code': self.extract_set_code(text)
                })
        
        # Remove duplicates
        unique_links = []
        seen_urls = set()
        for link in set_links:
            if link['url'] not in seen_urls:
                unique_links.append(link)
                seen_urls.add(link['url'])
                
        logger.info(f"Found {len(unique_links)} unique set links")
        return unique_links
    
    def extract_set_code(self, set_name):
        """Extract set code from set name"""
        # Look for text in parentheses at the end
        match = re.search(r'\(([^)]+)\)$', set_name.strip())
        if match:
            return match.group(1)
        return "UNKNOWN"
    
    def count_cards_in_set(self, set_url, set_info):
        """Count the number of cards in a set without downloading them"""
        response = self.get_page_content(set_url)
        if not response:
            return 0
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all card articles with the specific structure
        card_articles = soup.find_all('article', class_='type-pkmn_card entry')
        
        # Count valid card articles
        valid_cards = 0
        for article in card_articles:
            try:
                # Check if this article has the required structure
                card_link = article.find('a', class_='card-image-link')
                if not card_link:
                    continue
                    
                img_tag = card_link.find('img', class_='card-image')
                if not img_tag:
                    continue
                    
                img_url = img_tag.get('src', '')
                if not img_url:
                    continue
                
                valid_cards += 1
                
            except Exception:
                continue
        
        return valid_cards
    
    def count_total_cards(self):
        """Count total cards across all sets"""
        logger.info("🔢 Counting total cards across all sets...")
        
        # Get all set links
        set_links = self.extract_set_links()
        if not set_links:
            logger.error("No set links found!")
            return 0, []
        
        total_count = 0
        set_counts = []
        
        # Use tqdm for counting progress
        with tqdm(total=len(set_links), desc="📊 Scanning sets", unit="set") as pbar:
            for set_info in set_links:
                try:
                    count = self.count_cards_in_set(set_info['url'], set_info)
                    total_count += count
                    set_counts.append((set_info, count))
                    
                    pbar.set_postfix({
                        'Current': set_info['name'][:30],
                        'Cards': count,
                        'Total': total_count
                    })
                    pbar.update(1)
                    
                    # Small delay to be respectful
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"Error counting cards in {set_info['name']}: {e}")
                    set_counts.append((set_info, 0))
                    pbar.update(1)
        
        # Print summary
        print(f"\n📋 SCAN RESULTS:")
        print(f"   Total Sets: {len(set_links)}")
        print(f"   Total Cards: {total_count:,}")
        print(f"   Avg per Set: {total_count/len(set_links):.1f}")
        
        # Show top 10 largest sets
        largest_sets = sorted(set_counts, key=lambda x: x[1], reverse=True)[:10]
        print(f"\n🏆 Largest Sets:")
        for i, (set_info, count) in enumerate(largest_sets, 1):
            print(f"   {i:2d}. {set_info['name'][:40]:<40} {count:>4} cards")
        
        print()
        return total_count, set_counts
    
    def get_card_images_from_set(self, set_url, set_info):
        """Extract all card images from a specific set page"""
        logger.info(f"Scraping cards from set: {set_info['name']}")
        
        response = self.get_page_content(set_url)
        if not response:
            return []
            
        soup = BeautifulSoup(response.content, 'html.parser')
        cards = []
        
        # Find all card articles with the specific structure you mentioned
        card_articles = soup.find_all('article', class_='type-pkmn_card entry')
        
        for article in card_articles:
            try:
                # Find the card image link
                card_link = article.find('a', class_='card-image-link')
                if not card_link:
                    continue
                    
                # Extract card details
                card_title = card_link.get('title', '')
                card_page_url = card_link.get('href', '')
                
                # Find the image
                img_tag = card_link.find('img', class_='card-image')
                if not img_tag:
                    continue
                    
                img_url = img_tag.get('src', '')
                if not img_url:
                    continue
                
                # Extract pokemon name and card details from title
                pokemon_name, card_number = self.parse_card_title(card_title)
                
                card_info = {
                    'pokemon_name': pokemon_name,
                    'card_title': card_title,
                    'card_number': card_number,
                    'set_name': set_info['name'],
                    'set_code': set_info['code'],
                    'image_url': img_url,
                    'card_page_url': card_page_url
                }
                
                cards.append(card_info)
                
            except Exception as e:
                logger.warning(f"Error processing card in {set_info['name']}: {e}")
                continue
        
        logger.info(f"Found {len(cards)} cards in {set_info['name']}")
        return cards
    
    def parse_card_title(self, title):
        """Parse card title to extract Pokemon name and card number"""
        # Example: "Deoxys · POP Series 4 (P4) #2"
        # Extract pokemon name (before ·)
        parts = title.split('·')
        pokemon_name = parts[0].strip() if parts else "Unknown"
        
        # Extract card number (after #)
        card_number = "0"
        number_match = re.search(r'#(\w+)', title)
        if number_match:
            card_number = number_match.group(1)
            
        # Clean pokemon name
        pokemon_name = re.sub(r'[^\w\s-]', '', pokemon_name).strip()
        
        return pokemon_name, card_number
    
    def download_image(self, card_info):
        """Download a single card image"""
        try:
            img_url = card_info['image_url']
            response = self.get_page_content(img_url)
            
            if not response:
                self.failed_downloads.append(card_info)
                return False
            
            # Create filename
            safe_pokemon_name = re.sub(r'[^\w\s-]', '', card_info['pokemon_name']).replace(' ', '_')
            safe_set_code = re.sub(r'[^\w-]', '', card_info['set_code'])
            
            filename = f"{safe_pokemon_name}_{safe_set_code}_{card_info['card_number']}.jpg"
            
            # Handle duplicate filenames
            filepath = self.download_dir / "images" / filename
            counter = 1
            original_filepath = filepath
            while filepath.exists():
                name_part = original_filepath.stem
                extension = original_filepath.suffix
                filepath = original_filepath.parent / f"{name_part}_{counter}{extension}"
                counter += 1
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Update card info with local path
            card_info['local_path'] = str(filepath.relative_to(self.download_dir))
            card_info['filename'] = filepath.name
            
            # Thread-safe append
            with self.lock:
                self.downloaded_cards.append(card_info)
                # Update progress bar if it exists
                if self.progress_bar:
                    self.progress_bar.update(1)
                    self.progress_bar.set_postfix({
                        'Current': card_info['pokemon_name'][:20],
                        'Downloaded': len(self.downloaded_cards),
                        'Failed': len(self.failed_downloads)
                    })
            
            logger.debug(f"Downloaded: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading {card_info.get('card_title', 'Unknown')}: {e}")
            
            # Thread-safe append
            with self.lock:
                self.failed_downloads.append(card_info)
                # Update progress bar if it exists (failed downloads still count as processed)
                if self.progress_bar:
                    self.progress_bar.update(1)
                    self.progress_bar.set_postfix({
                        'Current': 'FAILED',
                        'Downloaded': len(self.downloaded_cards),
                        'Failed': len(self.failed_downloads)
                    })
            return False
    
    def save_metadata(self):
        """Save metadata about all downloaded cards"""
        metadata = {
            'total_cards': len(self.downloaded_cards),
            'total_failed': len(self.failed_downloads),
            'cards': self.downloaded_cards,
            'failed_downloads': self.failed_downloads
        }
        
        # Save as JSON
        with open(self.download_dir / "metadata" / "cards_metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Create YOLO format labels file (for reference)
        pokemon_names = list(set(card['pokemon_name'] for card in self.downloaded_cards))
        pokemon_names.sort()
        
        with open(self.download_dir / "metadata" / "pokemon_classes.txt", 'w') as f:
            for i, name in enumerate(pokemon_names):
                f.write(f"{i}: {name}\n")
        
        # Create summary
        with open(self.download_dir / "metadata" / "download_summary.txt", 'w') as f:
            f.write(f"Pokemon Card Download Summary\n")
            f.write(f"============================\n\n")
            f.write(f"Total cards downloaded: {len(self.downloaded_cards)}\n")
            f.write(f"Total failed downloads: {len(self.failed_downloads)}\n")
            f.write(f"Unique Pokemon: {len(pokemon_names)}\n\n")
            
            # Group by set
            sets = {}
            for card in self.downloaded_cards:
                set_name = card['set_name']
                if set_name not in sets:
                    sets[set_name] = 0
                sets[set_name] += 1
            
            f.write("Cards by Set:\n")
            for set_name, count in sorted(sets.items()):
                f.write(f"  {set_name}: {count} cards\n")
        
        logger.info(f"Metadata saved. Total cards: {len(self.downloaded_cards)}")
    
    def download_cards_parallel(self, cards, max_workers=5):
        """Download multiple cards in parallel"""
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_card = {executor.submit(self.download_image, card): card for card in cards}
            
            # Process completed downloads
            for future in as_completed(future_to_card):
                card = future_to_card[future]
                try:
                    success = future.result()
                except Exception as e:
                    logger.error(f"Thread error downloading {card.get('card_title', 'Unknown')}: {e}")
                    with self.lock:
                        self.failed_downloads.append(card)
    
    def scrape_all_cards(self, delay=0.1, parallel=False, max_workers=5, skip_count=False):
        """Main method to scrape all cards from all sets"""
        logger.info("🚀 Starting Pokemon card scraping...")
        
        if not skip_count:
            # First, count all cards to show total progress
            self.total_cards_expected, set_counts = self.count_total_cards()
            if self.total_cards_expected == 0:
                logger.error("No cards found to download!")
                return
        else:
            # If skipping count, get set links for downloading
            set_links = self.extract_set_links()
            if not set_links:
                logger.error("No set links found!")
                return
            set_counts = [(set_info, 0) for set_info in set_links]  # Unknown counts
            self.total_cards_expected = 0
        
        # Initialize progress bar
        if self.total_cards_expected > 0:
            self.progress_bar = tqdm(
                total=self.total_cards_expected,
                desc="💾 Downloading cards",
                unit="card",
                bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
            )
        
        try:
            # Download cards from each set
            for i, (set_info, expected_count) in enumerate(set_counts, 1):
                logger.info(f"📦 Processing set {i}/{len(set_counts)}: {set_info['name']}")
                
                # Get cards from this set
                cards = self.get_card_images_from_set(set_info['url'], set_info)
                
                if not cards:
                    logger.warning(f"No cards found in {set_info['name']}")
                    continue
                
                if parallel and len(cards) > 1:
                    # Download cards in parallel for faster performance
                    logger.info(f"⚡ Downloading {len(cards)} cards in parallel (max {max_workers} workers)...")
                    self.download_cards_parallel(cards, max_workers)
                    
                    # Brief pause between sets when using parallel
                    time.sleep(delay * 5)
                else:
                    # Download each card image sequentially
                    for card in cards:
                        self.download_image(card)
                        # Reduced delay for faster downloading
                        time.sleep(delay)
                
                # Save progress after each set
                self.save_metadata()
                logger.info(f"✅ Set completed: {set_info['name']} - "
                           f"{len(cards)} cards found, "
                           f"{len(self.downloaded_cards)} total downloaded")
                
                # Minimal delay between sets
                time.sleep(delay * 2)
        
        finally:
            # Close progress bar
            if self.progress_bar:
                self.progress_bar.close()
                self.progress_bar = None
        
        # Final save
        self.save_metadata()
        
        # Final summary
        print(f"\n🎉 SCRAPING COMPLETED!")
        print(f"   Expected: {self.total_cards_expected:,} cards" if self.total_cards_expected > 0 else "   Expected: Unknown")
        print(f"   Downloaded: {len(self.downloaded_cards):,} cards")
        print(f"   Failed: {len(self.failed_downloads):,} cards")
        if self.total_cards_expected > 0:
            success_rate = (len(self.downloaded_cards) / self.total_cards_expected) * 100
            print(f"   Success Rate: {success_rate:.1f}%")
        
        logger.info(f"Scraping completed! Downloaded {len(self.downloaded_cards)} cards, {len(self.failed_downloads)} failed.")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Pokemon Card Scraper for YOLO Training")
    parser.add_argument("--delay", type=float, default=0.1, 
                       help="Delay between downloads in seconds (default: 0.1)")
    parser.add_argument("--parallel", action="store_true",
                       help="Use parallel downloading for faster speeds")
    parser.add_argument("--workers", type=int, default=5,
                       help="Number of parallel workers (default: 5)")
    parser.add_argument("--fast", action="store_true",
                       help="Fast mode: parallel with minimal delay")
    parser.add_argument("--skip-count", action="store_true",
                       help="Skip counting cards (start downloading immediately)")
    
    args = parser.parse_args()
    
    # Fast mode preset
    if args.fast:
        args.parallel = True
        args.delay = 0.05
        args.workers = 8
        print("🚀 Fast mode enabled: parallel downloading with 8 workers and 0.05s delay")
    
    scraper = PokemonCardScraper()
    
    print(f"⚙️  Configuration:")
    print(f"   Delay: {args.delay}s between downloads")
    print(f"   Parallel: {'Yes' if args.parallel else 'No'}")
    if args.parallel:
        print(f"   Workers: {args.workers}")
    print()
    
    try:
        scraper.scrape_all_cards(
            delay=args.delay, 
            parallel=args.parallel, 
            max_workers=args.workers,
            skip_count=args.skip_count
        )
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        scraper.save_metadata()
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        scraper.save_metadata()


if __name__ == "__main__":
    main() 