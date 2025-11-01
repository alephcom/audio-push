# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.0.1]: https://github.com/alephcom/audio-push/releases/tag/v0.0.1

