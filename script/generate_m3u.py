#!/usr/bin/env python3
"""
Saudi Channels M3U Generator - FINAL WORKING VERSION
Generates M3U with EXTVLCOPT headers for VLC compatibility
"""

import os
import sys
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json
import re

class SaudiChannelsM3U:
    def __init__(self):
        # Headers that made the stream work (from successful XHR)
        self.required_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://aloula.sba.sa/',
            'Origin': 'https://aloula.sba.sa',
            'Connection': 'keep-alive',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"'
        }
        
        # Try to get token from environment variable (GitHub secret)
        self.token = os.environ.get('CHANNEL_TOKEN')
        if not self.token:
            # Fallback to hardcoded token (expires 2026)
            self.token = (
                'hdntl=exp=1774006481~'
                'acl=%2fksa1live%2fksa1.smil%2f*~'
                'data=hdntl~'
                'hmac=b892a43982bbddc829a5547d3b9eeb5c0c88a9f9c7e7cc98e906a963784691c4'
            )
        
        # Base URL
        self.base_url = "https://live.kwikmotion.com"
        
        # First, fetch channel list from API
        self.channels = self.fetch_channels()
        
    def fetch_channels(self) -> List[Dict]:
        """Fetch channel list from Faulio API"""
        try:
            print("📡 Fetching channel list from API...")
            response = requests.get(
                'https://aloula.faulio.com/api/v1/channels',
                headers={'User-Agent': self.required_headers['User-Agent']},
                timeout=10
            )
            response.raise_for_status()
            channels_data = response.json()
            
            channels = []
            stream_paths = {
                'saudia': 'ksa1live/ksa1.smil',
                'sbc': 'sbc',  # Need verification
                'alekhbariya': 'ksanews',
                'quran': 'ksaquranlive/ksaquran.smil',
                'sunna': 'ksasunna',
                'riyadiya1': 'ksasports1',
                'riyadiya2': 'ksasports2',
                'riyadiya3': 'ksasports3live/ksasports3.smil',
                'thikrayat': 'thikrayat',  # Need verification
                'saudiaalaan': 'ksasaudiaalaan'  # Need verification
            }
            
            for channel in channels_data:
                slug = channel.get('url')
                if slug in stream_paths:
                    channel_info = {
                        'id': channel.get('id'),
                        'slug': slug,
                        'name': channel.get('title', '').replace(' – البث المباشر', ''),
                        'name_ar': channel.get('title', ''),
                        'logo': channel.get('logo', {}).get('full', ''),
                        'group': self.get_channel_group(slug),
                        'stream_path': stream_paths[slug],
                        'publish_path': self.get_publish_path(stream_paths[slug]),
                        'quality': self.get_quality_name(stream_paths[slug])
                    }
                    channels.append(channel_info)
                    print(f"  ✅ Found: {channel_info['name']}")
            
            return channels
            
        except Exception as e:
            print(f"❌ Error fetching channels: {e}")
            # Fallback to hardcoded channels
            return self.get_fallback_channels()
    
    def get_channel_group(self, slug: str) -> str:
        """Determine channel group based on slug"""
        religious = ['quran', 'sunna']
        sports = ['riyadiya1', 'riyadiya2', 'riyadiya3']
        news = ['alekhbariya']
        
        if slug in religious:
            return 'Religious'
        elif slug in sports:
            return 'Sports'
        elif slug in news:
            return 'News'
        else:
            return 'Saudi TV'
    
    def get_publish_path(self, stream_path: str) -> str:
        """Generate publish path from stream path"""
        if 'live/' in stream_path:
            base = stream_path.split('live/')[0] + 'live/'
            name = stream_path.split('/')[0].replace('live', '')
            return f"{base}{name}publish"
        return stream_path.replace('.smil', 'publish')
    
    def get_quality_name(self, stream_path: str) -> str:
        """Generate quality name from stream path"""
        if 'ksa1' in stream_path:
            return 'ksa1_480p'
        elif 'ksaquran' in stream_path:
            return 'ksaquran_480p'
        elif 'ksasports3' in stream_path:
            return 'ksasports3_source'
        else:
            return 'source'
    
    def get_fallback_channels(self) -> List[Dict]:
        """Fallback channels if API fails"""
        return [
            {
                'id': 2,
                'slug': 'saudia',
                'name': 'Saudia Channel',
                'name_ar': 'قناة السعودية',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/89/52/fullhd_e07b4198a85a2bc1b3c0733a71f61dd010dec85d.png',
                'group': 'Saudi TV',
                'stream_path': 'ksa1live/ksa1.smil',
                'publish_path': 'ksa1publish',
                'quality': 'ksa1_480p'
            },
            {
                'id': 7,
                'slug': 'quran',
                'name': 'Holy Quran Channel',
                'name_ar': 'قناة القرآن الكريم',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/da/6c/fullhd_7eaf7e165c4cad5b3a45eff65d2011e18be5d670.png',
                'group': 'Religious',
                'stream_path': 'ksaquranlive/ksaquran.smil',
                'publish_path': 'ksaquranpublish',
                'quality': 'ksaquran_480p'
            },
            {
                'id': 16,
                'slug': 'riyadiya3',
                'name': 'Al-Riyadiya 3',
                'name_ar': 'القناة الرياضية 3',
                'logo': 'https://aloula.faulio.com/storage/mediagallery/2d/ee/fullhd_f1d461237592b4d46c44a6f300df1d97051f7c55.png',
                'group': 'Sports',
                'stream_path': 'ksasports3live/ksasports3.smil',
                'publish_path': 'ksasports3publish',
                'quality': 'ksasports3_source'
            }
        ]
    
    def generate_stream_url(self, channel: Dict) -> str:
        """Generate stream URL using pattern from captured URLs"""
        
        stream_url = (
            f"{self.base_url}/{channel['stream_path']}/"
            f"{channel['publish_path']}/{channel['quality']}/"
            f"{self.token}/chunks_dvr.m3u8"
        )
        
        return stream_url
    
    def generate_m3u_with_headers(self) -> str:
        """Generate M3U with EXTVLCOPT headers for VLC"""
        
        # Get GitHub Pages URL if running in Actions
        github_pages_url = os.environ.get('GITHUB_PAGES_URL', '')
        
        m3u_content = [
            '#EXTM3U',
            f'#PLAYLIST: Saudi Channels - Generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            f'#GENERATOR: GitHub Actions - {os.environ.get("GITHUB_RUN_ID", "local")}',
            '',
            '# =================================================',
            '# 🇸🇦 Saudi TV Channels Live Streams',
            '# =================================================',
            '#',
            '# 📺 How to use:',
            '#   1. Open VLC Media Player',
            '#   2. Drag and drop this file into VLC',
            '#   3. Or use Media → Open File',
            '#',
            '# 🔧 Technical Details:',
            '#   - Streams require specific HTTP headers',
            '#   - EXTVLCOPT lines below tell VLC what to send',
            '#   - Token expires: March 2026',
            '#',
            '# =================================================',
            ''
        ]
        
        print("\n📡 Generating M3U with headers...")
        print("=" * 60)
        
        for channel in self.channels:
            stream_url = self.generate_stream_url(channel)
            
            print(f"\n📺 Processing: {channel['name']}")
            print(f"  URL: {stream_url[:100]}...")
            
            # EXTINF line with TVG attributes
            extinf = (
                f'#EXTINF:-1 '
                f'tvg-id="{channel["slug"]}" '
                f'tvg-name="{channel["name"]}" '
                f'tvg-logo="{channel["logo"]}" '
                f'group-title="{channel["group"]}", '
                f'{channel["name"]}'
            )
            
            m3u_content.append(extinf)
            
            # Add ALL required headers as EXTVLCOPT
            m3u_content.append('#EXTVLCOPT:network-caching=1000')
            m3u_content.append('#EXTVLCOPT:live-caching=300')
            m3u_content.append(f'#EXTVLCOPT:http-referrer={self.required_headers["Referer"]}')
            m3u_content.append(f'#EXTVLCOPT:http-user-agent={self.required_headers["User-Agent"]}')
            m3u_content.append(f'#EXTVLCOPT:http-origin={self.required_headers["Origin"]}')
            m3u_content.append('#EXTVLCOPT:http-accept=*/*')
            m3u_content.append('#EXTVLCOPT:http-accept-language=en-US,en;q=0.9')
            
            # The stream URL
