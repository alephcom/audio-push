# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.3] - 2025-01-XX

### Added
- Support for directories as `source_file` - automatically creates playlist from all audio files in folder
- Automatic playlist generation for directories using FFmpeg concat demuxer
- Support for multiple audio formats in directories (.mp3, .wav, .ogg, .m4a, .aac, .flac, .opus)
- Files in directories are played in alphabetical order in a continuous loop
- Force download option for configuration files to always get latest version

### Changed
- Configuration files from URLs are always downloaded (bypass cache) to ensure latest version
- Playlist files are now stored in cache directory (`~/.cache/audio-push/`) instead of source directory
- Improved file extension detection for cached downloads
- Better handling of URLs with query parameters

### Technical Details
- Directories create playlist files using FFmpeg concat format stored in cache directory
- Playlist files use MD5 hash of directory path as filename prefix
- Playlist files are automatically generated and managed in cache
- Force download option for config files ensures fresh configuration on each run

## [0.0.2] - 2025-01-XX

### Added
- Support for HTTP/HTTPS source file URLs
- Support for HTTP/HTTPS configuration file URLs
- Automatic download and caching of remote source files
- Automatic download and caching of remote configuration files
- Cache directory at `~/.cache/audio-push/` for downloaded files
- Per-endpoint source file configuration
- Per-endpoint protocol configuration (HTTP/HTTPS)
- Automatic file extension detection from URLs and Content-Type headers
- Content-Type based file extension inference for downloaded files

### Changed
- Endpoints now require individual `source_file` specification
- Source files can be local paths or HTTP/HTTPS URLs
- Protocol (HTTP/HTTPS) is now configurable per endpoint
- Configuration file no longer requires `-f/--file` command-line argument

### Technical Details
- Cached files use MD5 hash of URL as filename for consistency
- Files are only downloaded if not already in cache
- Cache location: `~/.cache/audio-push/`

## [0.0.1] - 2025-11-01

### Added
- Initial release of audio-push application
- Support for streaming MP3 files to Icecast servers
- JSON configuration file support for multiple endpoints
- Command-line interface for single endpoint streaming (legacy mode)
- Automatic endpoint grouping by (source_file, bitrate) for efficiency
- Multi-endpoint streaming support with single FFmpeg process per group
- Per-endpoint bitrate configuration
- Automatic file looping for continuous streaming
- Auto-reconnection on stream failures
- Graceful shutdown handling (Ctrl+C)
- Comprehensive error handling and validation
- Detailed documentation in README.md
- Example configuration file (config.example.json)
- MIT License

### Features
- Stream single MP3 file to multiple Icecast endpoints simultaneously
- Group endpoints sharing the same source file and bitrate for optimized resource usage
- Support for custom stream names, usernames, and passwords per endpoint
- Real-time monitoring of all streaming processes
- Automatic restart of failed streams

### Technical Details
- Python 3.6+ required
- Uses FFmpeg for audio streaming
- No external Python dependencies (uses standard library only)
- Multi-threaded streaming architecture
- Process management for FFmpeg instances

[0.0.3]: https://github.com/alephcom/audio-push/releases/tag/v0.0.3

[0.0.2]: https://github.com/alephcom/audio-push/releases/tag/v0.0.2

[0.0.1]: https://github.com/alephcom/audio-push/releases/tag/v0.0.1

