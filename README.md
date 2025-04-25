# YouTube Video Downloader

A Streamlit-based web application for downloading YouTube videos in highest resolution.

## Installation

1. Install UV package manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Set up project dependencies:

```bash
uv pip install -r requirements.txt
```

## Development Setup

We recommend using UV for dependency management:

```bash
uv venv  # Create virtual environment
uv run streamlit run app.py  # Start development server
```

## Features

- Download videos in MP4 format
- Supports both short and long videos
- Automatic resolution selection
- Simple web interface

## Installation

```bash
pip install -r requirements.txt
```

## Usage

1. Install dependencies with UV:

```bash
uv sync
```

2. Start application:

```bash
uv run streamlit run app.py
```

3. Enter YouTube URL
4. Click Download button

## License

MIT License
