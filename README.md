# Audio Push to Icecast

A Python application that streams MP3 files to one or more Icecast servers in a continuous loop. Supports multiple endpoints with individual bitrate configuration.

**Repository:** [https://github.com/alephcom/audio-push](https://github.com/alephcom/audio-push)

## Requirements

- Python 3.6 or higher
- [FFmpeg](https://ffmpeg.org/) installed and available in your PATH

### Installing FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**Linux (RHEL/CentOS):**
```bash
sudo yum install ffmpeg
```

**Windows:**
Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html) and add to PATH.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alephcom/audio-push.git
   cd audio-push
   ```
2. Ensure FFmpeg is installed (see above)
3. No additional Python packages are required (uses standard library only)

## Usage

### Using JSON Configuration File (Recommended)

The recommended way to use this application is with a JSON configuration file that specifies one or more Icecast endpoints.

1. Create a JSON configuration file (see `config.example.json` for an example):

```json
{
  "endpoints": [
    {
      "host": "localhost",
      "port": 8000,
      "mount": "/stream.mp3",
      "username": "source",
      "password": "your_source_password",
      "stream_name": "My Radio Station",
      "bitrate": "128k",
      "source_file": "path/to/audio.mp3",
      "protocol": "http"
    },
    {
      "host": "icecast.example.com",
      "port": 8443,
      "mount": "/live.mp3",
      "username": "source",
      "password": "another_password",
      "stream_name": "Alternative Stream",
      "bitrate": "192k",
      "source_file": "path/to/audio2.mp3",
      "protocol": "https"
    }
  ]
}
```

2. Run the application:

```bash
python audio_streamer.py -c config.json
```

### JSON Configuration Format

Each endpoint in the configuration file must include:

- `host`: Icecast server hostname or IP address (required)
- `port`: Icecast server port, typically 8000 (required)
- `mount`: Icecast mount point, e.g., `/stream.mp3` (required)
- `password`: Icecast source password (required)
- `source_file`: Path to the source MP3 file to stream (required)
- `protocol`: Protocol to use, either `http` or `https` (optional, default: `http`)
- `username`: Icecast username (optional, default: `source`)
- `stream_name`: Name of the stream (optional, default: `Audio Stream`)
- `bitrate`: Audio bitrate, e.g., `128k`, `192k`, `64k` (optional, default: `128k`)

### Single Endpoint via Command Line (Legacy)

For backward compatibility, you can still specify a single endpoint via command-line arguments:

```bash
python audio_streamer.py -f audio.mp3 -H localhost -p 8000 -m /stream.mp3 -P password
```

### Command-Line Arguments

- `-f, --file`: Path to the MP3 file to stream (required)
- `-c, --config`: Path to JSON configuration file with endpoint(s) (recommended)
- `-H, --host`: Icecast server hostname or IP address (legacy, required if no config)
- `-p, --port`: Icecast server port (legacy, required if no config)
- `-m, --mount`: Icecast mount point (legacy, required if no config)
- `-P, --password`: Icecast source password (legacy, required if no config)
- `-u, --username`: Icecast username (legacy, default: `source`)
- `-n, --name`: Stream name (legacy, default: `Audio Stream`)

### Make it executable (optional)

```bash
chmod +x audio_streamer.py
./audio_streamer.py -c config.json
```

## How It Works

1. Loads endpoint configuration from JSON file or command-line arguments
2. Each endpoint specifies its own source MP3 file and protocol (HTTP/HTTPS)
3. Groups endpoints by (source_file, bitrate) combination for efficiency
4. Creates one FFmpeg process per group (multiple endpoints with same file/bitrate share a process)
5. Streams to all configured Icecast servers simultaneously using the specified protocol
6. Automatically loops the source file indefinitely for each endpoint
7. Handles reconnections if any stream drops
8. Each endpoint can have its own source file, bitrate, and protocol configuration

### Optimization

Endpoints sharing the same source file and bitrate are automatically grouped together and streamed using a single FFmpeg process. This reduces CPU usage and network overhead when streaming to multiple endpoints with the same configuration.

## Icecast Configuration

Make sure your Icecast server is configured to accept streams on the specified mount point. Your Icecast configuration file should include:

```xml
<mount>
    <mount-name>/stream.mp3</mount-name>
    <password>your_source_password</password>
</mount>
```

## Stopping the Stream

Press `Ctrl+C` to gracefully stop the stream.

## Troubleshooting

### FFmpeg not found
Make sure FFmpeg is installed and available in your PATH. Test with:
```bash
ffmpeg -version
```

### Connection refused
- Check that the Icecast server is running
- Verify the host, port, and mount point are correct
- Check firewall settings

### Authentication failed
- Verify the username and password are correct
- Check Icecast source password configuration

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Repository

GitHub: [https://github.com/alephcom/audio-push](https://github.com/alephcom/audio-push)
