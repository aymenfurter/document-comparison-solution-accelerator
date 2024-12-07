# Document Comparison Solution Accelerator

A FastAPI-based solution for comparing Word documents and generating intelligent changelogs using Azure OpenAI and Azure Document Intelligence.

## Features

- DOCX to HTML conversion using Pandoc with Azure Document Intelligence fallback
- Intelligent document comparison with content-aware diffing
- Smart changelog generation using Azure OpenAI
- Support for complex document structures (tables, lists, images, etc.)
- Robust HTML normalization for accurate comparisons

## Prerequisites

- Python 3.11+
- Pandoc
- Azure OpenAI account
- Azure Document Intelligence account
- Poetry (recommended) or pip

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/document-comparison-solution-accelerator.git
cd document-comparison-solution-accelerator
```

2. Install dependencies:
```bash
poetry install
# or using pip
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and configure your settings:
```bash
cp .env.example .env
```

4. Configure environment variables in `.env`

## Configuration

Required environment variables:
- Azure OpenAI settings
- Azure Document Intelligence credentials
- Application settings

See `.env.example` for all available options.

## Usage

1. Start the server:
```bash
uvicorn app.main:app --reload
```

2. API endpoints:
- `POST /api/v1/upload`: Upload two documents for comparison
- `GET /api/v1/status/{job_id}`: Check comparison status
- `GET /health`: Application health check

## API Documentation

Once running, access the API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

Run tests:
```bash
PYTHONPATH=./ pytest
```

Enable debug logging:
```bash
PYTHONPATH=./ LOG_LEVEL=DEBUG uvicorn app.main:app --reload
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.