#!/usr/bin/env python3
"""
Audio Streamer to Icecast
Streams an MP3 file to an Icecast server in a continuous loop.
"""

__version__ = "0.0.1"

import subprocess
import sys
import os
import time
import argparse
import signal
import json
import threading
from pathlib import Path
from typing import List, Dict


class StreamEndpoint:
    """Represents a single Icecast endpoint configuration."""
    
    def __init__(self, config: Dict):
        """
        Initialize endpoint from configuration dictionary.
        
        Args:
            config: Dictionary with endpoint configuration
        """
        self.host = config.get('host')
        self.port = config.get('port')
        self.mount = config.get('mount')
        self.username = config.get('username', 'source')
        self.password = config.get('password')
        self.stream_name = config.get('stream_name', 'Audio Stream')
        self.bitrate = config.get('bitrate', '128k')  # Default to 128k if not specified
        self.source_file = config.get('source_file')  # Source MP3 file for this endpoint
        self.protocol = config.get('protocol', 'http').lower()  # http or https, default to http
        self.process = None
        self.running = True
        
        # Validate required fields
        if not all([self.host, self.port, self.mount, self.password, self.source_file]):
            raise ValueError("Endpoint missing required fields: host, port, mount, password, source_file")
        
        # Validate protocol
        if self.protocol not in ['http', 'https']:
            raise ValueError(f"Protocol must be 'http' or 'https', got: {self.protocol}")
    
    def get_icecast_url(self):
        """Get the Icecast URL for this endpoint."""
        return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}{self.mount}"


class StreamGroup:
    """Represents a group of endpoints sharing the same source file and bitrate."""
    
    def __init__(self, mp3_file: Path, bitrate: str, endpoints: List[StreamEndpoint]):
        """
        Initialize a stream group.
        
        Args:
            mp3_file: Path to the MP3 file
            bitrate: Audio bitrate (e.g., '128k')
            endpoints: List of endpoints in this group
        """
        self.mp3_file = mp3_file
        self.bitrate = bitrate
        self.endpoints = endpoints
        self.process = None
        self.running = True
    
    def get_group_id(self):
        """Get a unique identifier for this group."""
        return f"{self.mp3_file.name}:{self.bitrate}"


class AudioStreamer:
    """Streams audio files to one or more Icecast servers."""
    
    def __init__(self, endpoints: List[StreamEndpoint], mp3_file: str = None):
        """
        Initialize the audio streamer.
        
        Args:
            endpoints: List of StreamEndpoint objects to stream to
            mp3_file: Optional path to MP3 file (legacy mode, when not using config)
        """
        self.endpoints = endpoints
        self.running = True
        self.stream_groups = []  # Groups of endpoints by (file, bitrate)
        self.processes = {}  # Track processes by group identifier
        
        # For legacy mode, validate MP3 file exists
        if mp3_file:
            mp3_path = Path(mp3_file)
            if not mp3_path.exists():
                raise FileNotFoundError(f"MP3 file not found: {mp3_path}")
            # In legacy mode, set source_file for all endpoints
            for endpoint in self.endpoints:
                endpoint.source_file = str(mp3_path)
        else:
            # Validate source files exist for each endpoint
            for endpoint in self.endpoints:
                source_path = Path(endpoint.source_file)
                if not source_path.exists():
                    raise FileNotFoundError(f"Source MP3 file not found for endpoint {endpoint.host}:{endpoint.port}{endpoint.mount}: {source_path}")
        
        if not self.endpoints:
            raise ValueError("At least one endpoint must be provided")
        
        # Group endpoints by (source_file, bitrate)
        self._group_endpoints()
    
    def _group_endpoints(self):
        """Group endpoints by (source_file, bitrate) combination."""
        groups_dict = {}
        
        for endpoint in self.endpoints:
            # Use endpoint's source_file instead of shared mp3_file
            source_path = Path(endpoint.source_file)
            key = (str(source_path.absolute()), endpoint.bitrate)
            if key not in groups_dict:
                groups_dict[key] = []
            groups_dict[key].append(endpoint)
        
        # Create StreamGroup objects
        for (file_path, bitrate), endpoint_list in groups_dict.items():
            group = StreamGroup(Path(file_path), bitrate, endpoint_list)
            self.stream_groups.append(group)
    
    def build_ffmpeg_command(self, stream_group: StreamGroup):
        """Build the ffmpeg command for streaming to multiple endpoints."""
        ffmpeg_cmd = [
            'ffmpeg',
            '-re',  # Read input at native frame rate (important for streaming)
            '-stream_loop', '-1',  # Loop the input indefinitely
            '-i', str(stream_group.mp3_file),  # Input file
        ]
        
        # For each endpoint in the group, add output parameters
        # FFmpeg processes outputs sequentially, so each needs its own encoding params
        for endpoint in stream_group.endpoints:
            # Map the audio stream and add encoding parameters for this output
            ffmpeg_cmd.extend([
                '-map', '0:a:0',  # Map the first audio stream from input
                '-acodec', 'libmp3lame',  # Audio codec (MP3)
                '-ab', stream_group.bitrate,  # Audio bitrate
                '-ar', '44100',  # Sample rate
                '-ac', '2',  # Audio channels (stereo)
                '-f', 'mp3',  # Output format
                '-content_type', 'audio/mpeg',  # Content type
                '-ice_name', endpoint.stream_name,  # Stream name
                endpoint.get_icecast_url()  # Output URL
            ])
        
        return ffmpeg_cmd
    
    def get_endpoint_id(self, endpoint: StreamEndpoint):
        """Get a unique identifier for an endpoint."""
        return f"{endpoint.host}:{endpoint.port}{endpoint.mount}"
    
    def start_streaming(self):
        """Start streaming to all configured Icecast endpoints."""
        if not self.check_ffmpeg():
            print("Error: ffmpeg is not installed or not in PATH")
            sys.exit(1)
        
        print(f"Starting stream to {len(self.endpoints)} Icecast endpoint(s)...")
        print("-" * 60)
        print(f"Grouped into {len(self.stream_groups)} stream group(s) by (file, bitrate)")
        print("-" * 60)
        
        # Display grouping information
        for group in self.stream_groups:
            group_id = group.get_group_id()
            print(f"\nGroup: {group_id} ({len(group.endpoints)} endpoint(s))")
            print(f"  Source File: {group.mp3_file}")
            for endpoint in group.endpoints:
                endpoint_id = self.get_endpoint_id(endpoint)
                print(f"  → {endpoint.protocol.upper()}://{endpoint.host}:{endpoint.port}{endpoint.mount}")
                print(f"    Stream Name: {endpoint.stream_name}")
                print(f"    Username: {endpoint.username}")
                print(f"    Bitrate: {endpoint.bitrate}")
        
        print("-" * 60)
        print("\nPress Ctrl+C to stop streaming\n")
        
        # Start a streaming thread for each group
        threads = []
        for group in self.stream_groups:
            thread = threading.Thread(target=self._stream_to_group, args=(group,), daemon=True)
            thread.start()
            threads.append(thread)
        
        try:
            # Monitor all groups
            while self.running:
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n\nStopping all streams...")
            self.stop_streaming()
    
    def _stream_to_group(self, stream_group: StreamGroup):
        """Stream to a group of endpoints in a separate thread."""
        group_id = stream_group.get_group_id()
        
        while self.running and stream_group.running:
            try:
                self._start_group_process(stream_group)
                
                # Monitor the process
                while stream_group.process and stream_group.running and self.running:
                    return_code = stream_group.process.poll()
                    if return_code is not None:
                        # Process ended
                        if stream_group.running:
                            endpoint_list = ", ".join([self.get_endpoint_id(e) for e in stream_group.endpoints])
                            print(f"\n[{group_id}] Process ended, restarting in 3 seconds...")
                            print(f"[{group_id}] Affected endpoints: {endpoint_list}")
                            time.sleep(3)
                            break
                        else:
                            break
                    time.sleep(1)
                    
            except Exception as e:
                endpoint_list = ", ".join([self.get_endpoint_id(e) for e in stream_group.endpoints])
                print(f"[{group_id}] Error: {e}")
                print(f"[{group_id}] Affected endpoints: {endpoint_list}")
                if stream_group.running:
                    print(f"[{group_id}] Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    break
    
    def _start_group_process(self, stream_group: StreamGroup):
        """Start an ffmpeg process for a group of endpoints."""
        group_id = stream_group.get_group_id()
        ffmpeg_cmd = self.build_ffmpeg_command(stream_group)
        
        try:
            stream_group.process = subprocess.Popen(
                ffmpeg_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            self.processes[group_id] = stream_group.process
            endpoint_list = ", ".join([self.get_endpoint_id(e) for e in stream_group.endpoints])
            print(f"[{group_id}] Started streaming to {len(stream_group.endpoints)} endpoint(s): {endpoint_list}")
        except Exception as e:
            print(f"[{group_id}] Failed to start process: {e}")
            stream_group.process = None
    
    def stop_streaming(self):
        """Stop all streaming processes."""
        self.running = False
        
        # Stop all groups
        for group in self.stream_groups:
            group.running = False
            if group.process:
                group.process.terminate()
        
        # Wait for all processes to terminate
        for group_id, process in self.processes.items():
            if process:
                try:
                    process.wait(timeout=5)
                    print(f"[{group_id}] Stream stopped.")
                except subprocess.TimeoutExpired:
                    process.kill()
                    print(f"[{group_id}] Stream force stopped.")
        
        self.processes.clear()
        print("All streams stopped.")
    
    def check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False


def load_config(config_file: str) -> Dict:
    """Load configuration from JSON file."""
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")


def create_endpoints_from_config(config: Dict) -> List[StreamEndpoint]:
    """Create StreamEndpoint objects from configuration."""
    endpoints = []
    
    # Check if config has an 'endpoints' key (list of endpoints)
    if 'endpoints' in config:
        endpoint_configs = config['endpoints']
    elif isinstance(config, list):
        # Config is a list of endpoints
        endpoint_configs = config
    else:
        # Config is a single endpoint object
        endpoint_configs = [config]
    
    for idx, endpoint_config in enumerate(endpoint_configs):
        try:
            endpoint = StreamEndpoint(endpoint_config)
            endpoints.append(endpoint)
        except ValueError as e:
            print(f"Warning: Skipping endpoint {idx + 1} due to error: {e}", file=sys.stderr)
            continue
    
    return endpoints


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Stream MP3 file to Icecast server(s) in a loop',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using JSON configuration file (recommended)
  %(prog)s -f audio.mp3 -c config.json
  
  # Single endpoint via command line (legacy)
  %(prog)s -f audio.mp3 -H localhost -p 8000 -m /stream.mp3 -P mypassword
        """
    )
    
    parser.add_argument('-f', '--file',
                       help='Path to MP3 file to stream (required for legacy mode, not needed with config file)')
    parser.add_argument('-c', '--config',
                       help='Path to JSON configuration file with endpoint(s)')
    
    # Legacy single endpoint arguments (optional if config is provided)
    parser.add_argument('-H', '--host',
                       help='Icecast server hostname or IP address (legacy)')
    parser.add_argument('-p', '--port', type=int,
                       help='Icecast server port (legacy)')
    parser.add_argument('-m', '--mount',
                       help='Icecast mount point, e.g., /stream.mp3 (legacy)')
    parser.add_argument('-P', '--password',
                       help='Icecast source password (legacy)')
    parser.add_argument('-u', '--username', default='source',
                       help='Icecast username (default: source, legacy)')
    parser.add_argument('-n', '--name', default='Audio Stream',
                       help='Stream name (default: Audio Stream, legacy)')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Create endpoints
    endpoints = []
    
    if args.config:
        # Load from JSON config file
        try:
            config = load_config(args.config)
            endpoints = create_endpoints_from_config(config)
        except Exception as e:
            print(f"Error loading configuration: {e}", file=sys.stderr)
            sys.exit(1)
    elif all([args.host, args.port, args.mount, args.password, args.file]):
        # Use command-line arguments (legacy mode)
        endpoint_config = {
            'host': args.host,
            'port': args.port,
            'mount': args.mount,
            'password': args.password,
            'username': args.username,
            'stream_name': args.name,
            'protocol': 'http'  # Default to http for legacy mode
        }
        try:
            endpoints = [StreamEndpoint(endpoint_config)]
        except ValueError as e:
            print(f"Error creating endpoint: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        if not args.config:
            print("Error: Either provide a configuration file (-c) or all endpoint parameters (-H, -p, -m, -P, -f)", 
                  file=sys.stderr)
        else:
            print("Error: Invalid configuration", file=sys.stderr)
        sys.exit(1)
    
    if not endpoints:
        print("Error: No valid endpoints configured", file=sys.stderr)
        sys.exit(1)
    
    # Create streamer instance
    try:
        # In config mode, mp3_file is None (source files come from config)
        # In legacy mode, mp3_file is required
        streamer = AudioStreamer(
            endpoints=endpoints,
            mp3_file=args.file if not args.config else None
        )
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            streamer.stop_streaming()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start streaming
        streamer.start_streaming()
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()

