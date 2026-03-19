#!/usr/bin/env python3
"""
Saudi Channels M3U Generator - GitHub Actions Optimized Version
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging for GitHub Actions
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

class SaudiChannelsM3U:
    def __init__(self):
        self.logger = logger
        self.output_dir = Path('output')
        self.output_dir.mkdir(exist_ok=True)
        
        # Required headers from successful XHR
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://aloula.sba.sa/',
            'Origin': 'https://aloula.sba.sa'
        }
        
        # Token from environment or fallback
        self.token = os.environ.get('CHANNEL_TOKEN')
        if not self.token:
            self.token = (
                'hdntl=exp=1774006481~'
                'acl=%2fksa1live%2fksa1.smil%2f*~'
                'data=hdntl~'
                'hmac=b892a43982bbddc829a5547d3b9eeb5c0c88a9f9c7e7cc98e906a963784691c4'
            )
            self.logger.info("⚠️ Using fallback token (valid until 2026)")
        
        self.base_url = "https://live.kwikmotion.com"
        self.channels = self.fetch_channels()
        
    def fetch_channels(self) -> List[Dict]:
        """Fetch channel list with error handling"""
        try:
            self.logger.info("📡 Fetching channel list from API...")
            response = requests.get(
                'https://aloula.faulio.com/api/v1/channels',
                headers={'User-Agent': self.headers['User-Agent']},
                timeout=10
            )
            response.raise_for_status()
            channels_data = response.json()
            
            # Map slugs to stream paths (you'll need to complete this mapping)
            stream_paths = {
                'saudia': 'ksa1live/ksa1.smil',
                'quran': 'ksaquranlive/ksaquran.smil',
                'riyadiya3': 'ksasports3live/ksasports3.smil',
                # Add more mappings as you discover them
            }
            
            channels = []
            for channel in channels_data:
                slug = channel.get('url')
                if slug in stream_paths:
                    channel_info = {
                        'id': channel.get('id'),
                        'slug': slug,
                        'name': channel.get('title', '').replace(' – البث المباشر', ''),
                        'name_ar': channel.get('title', ''),
                        'logo': channel.get('logo', {}).get('full', ''),
                        'group': self.get_group(slug),
                        'stream_path': stream_paths[slug]
                    }
                    channels.append(channel_info)
                    self.logger.info(f"  ✅ {channel_info['name']}")
            
            return channels if channels else self.get_fallback_channels()
            
        except Exception as e:
            self.logger.error(f"❌ Error fetching channels: {e}")
            return self.get_fallback_channels()
    
    def get_group(self, slug: str) -> str:
        """Determine channel group"""
        groups = {
            'quran': 'Religious',
            'sunna': 'Religious',
            'riyadiya': 'Sports',
            'alekhbariya': 'News'
        }
        for key, group in groups.items():
            if key in slug:
                return group
        return 'Saudi TV'
    
    def get_fallback_channels(self) -> List[Dict]:
        """Fallback channels if API fails"""
        self.logger.info("📋 Using fallback channel list")
        return [
            {
                'slug': 'saudia',
                'name': 'Saudia Channel',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/89/52/fullhd_e07b4198a85a2bc1b3c0733a71f61dd010dec85d.png',
                'group': 'Saudi TV',
                'stream_path': 'ksa1live/ksa1.smil'
            },
            {
                'slug': 'quran',
                'name': 'Holy Quran Channel',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/da/6c/fullhd_7eaf7e165c4cad5b3a45eff65d2011e18be5d670.png',
                'group': 'Religious',
                'stream_path': 'ksaquranlive/ksaquran.smil'
            },
            {
                'slug': 'riyadiya3',
                'name': 'Al-Riyadiya 3',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/2d/ee/fullhd_f1d461237592b4d46c44a6f300df1d97051f7c55.png',
                'group': 'Sports',
                'stream_path': 'ksasports3live/ksasports3.smil'
            }
        ]
    
    def generate_stream_url(self, channel: Dict) -> str:
        """Generate stream URL"""
        base = channel['stream_path'].split('/')[0].replace('live', '')
        quality_map = {
            'ksa1': 'ksa1_480p',
            'ksaquran': 'ksaquran_480p',
            'ksasports3': 'ksasports3_source'
        }
        
        quality = 'source'
        for key, val in quality_map.items():
            if key in channel['stream_path']:
                quality = val
                break
        
        return (
            f"{self.base_url}/{channel['stream_path']}/"
            f"{base}publish/{quality}/"
            f"{self.token}/chunks_dvr.m3u8"
        )
    
    def generate_m3u(self) -> str:
        """Generate M3U content"""
        lines = [
            '#EXTM3U',
            f'#PLAYLIST: Saudi Channels - Generated on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")} UTC',
            f'#GITHUB_RUN: {os.environ.get("GITHUB_RUN_ID", "local")}',
            ''
        ]
        
        self.logger.info(f"\n📡 Generating M3U for {len(self.channels)} channels...")
        
        for channel in self.channels:
            stream_url = self.generate_stream_url(channel)
            
            extinf = (
                f'#EXTINF:-1 '
                f'tvg-id="{channel["slug"]}" '
                f'tvg-name="{channel["name"]}" '
                f'tvg-logo="{channel["logo"]}" '
                f'group-title="{channel["group"]}", '
                f'{channel["name"]}'
            )
            
            lines.extend([
                extinf,
                '#EXTVLCOPT:network-caching=1000',
                '#EXTVLCOPT:live-caching=300',
                f'#EXTVLCOPT:http-referrer={self.headers["Referer"]}',
                f'#EXTVLCOPT:http-user-agent={self.headers["User-Agent"]}',
                f'#EXTVLCOPT:http-origin={self.headers["Origin"]}',
                stream_url,
                ''
            ])
            
            self.logger.info(f"  ✅ {channel['name']}")
        
        return '\n'.join(lines)
    
    def save_files(self, m3u_content: str):
        """Save all output files"""
        # Save M3U
        m3u_path = self.output_dir / 'saudi_channels.m3u'
        m3u_path.write_text(m3u_content, encoding='utf-8')
        self.logger.info(f"\n✅ M3U saved: {m3u_path} ({m3u_path.stat().st_size} bytes)")
        
        # Save metadata
        metadata = {
            'generated': datetime.utcnow().isoformat(),
            'channels': len(self.channels),
            'github_run': os.environ.get('GITHUB_RUN_ID'),
            'token_expiry': 'March 2026'
        }
        
        meta_path = self.output_dir / 'metadata.json'
        meta_path.write_text(json.dumps(metadata, indent=2))
        
        # Create .nojekyll for GitHub Pages
        (self.output_dir / '.nojekyll').touch()
        
        self.logger.info(f"✅ Metadata saved")

def main():
    logger.info("=" * 60)
    logger.info("🇸🇦 Saudi Channels M3U Generator - GitHub Actions")
    logger.info("=" * 60)
    
    try:
        generator = SaudiChannelsM3U()
        m3u_content = generator.generate_m3u()
        generator.save_files(m3u_content)
        
        logger.info("\n" + "=" * 60)
        logger.info("✅ Generation complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"\n❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
