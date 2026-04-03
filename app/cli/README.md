# LION Q&A CLI

Interactive command-line interface for the LION Q&A system using the RAG API.

## Installation

The CLI requires the API to be running. Make sure you have:

1. API server running:
```bash
cd /home/decode/workspace/lion
source venv/bin/activate
uvicorn app.api.app:app --host 127.0.0.1 --port 8001
```

2. Optional: Install `rich` for better formatting:
```bash
pip install rich
```

## Usage

### Interactive Mode (Default)

Start an interactive Q&A session:

```bash
# Navigate to project root
cd /home/decode/workspace/lion
source venv/bin/activate

# Run CLI in interactive mode
python -m app.cli.qa
```

Then type your questions at the prompt:
```
🦁 Question: EU DEVO DECLARAR IMPOSTO DE RENDA?
```

Type `exit` or `quit` to exit, or `help` for help.

### Single Question Mode

Ask a single question:

```bash
python -m app.cli.qa "EU DEVO DECLARAR IMPOSTO DE RENDA. RECEBO 1000 POR MES."
```

With optional context:

```bash
python -m app.cli.qa "Como abrir empresa?" --context "Preciso saber os passos básicos"
```

### Batch Mode

Process multiple questions from a file:

```bash
python -m app.cli.qa --batch app/cli/example_questions.txt
```

File format:
- One question per line
- Lines starting with `#` are treated as comments
- Empty lines are ignored

Results are saved to `app/cli/batch_results_YYYYMMDD_HHMMSS.json` with full response data.

### Custom API Endpoint

Specify a different API URL:

```bash
python -m app.cli.qa "Your question" --api http://localhost:8002
```

### Command Line Options

```
usage: python -m app.cli.qa [-h] [-i] [-b FILE] [-c CONTEXT] [--api API] [-v] [question]

positional arguments:
  question              Question to ask (if not provided, enters interactive mode)

optional arguments:
  -h, --help            show this help message and exit
  -i, --interactive     Interactive mode
  -b, --batch FILE      Batch mode - read questions from file
  -c, --context CONTEXT Optional context information
  --api API             API endpoint URL (default: http://127.0.0.1:8001)
  -v, --version         show program's version number and exit
```

## Examples

### Start interactive session
```bash
python -m app.cli.qa
python -m app.cli.qa -i
```

### Single question
```bash
python -m app.cli.qa "Qual é o limite de renda para declarar imposto?"
```

### Batch processing
```bash
python -m app.cli.qa --batch example_questions.txt
```

### With context
```bash
python -m app.cli.qa "Como abrir?" --context "Preciso de informações sobre empresa"
```

### Custom API
```bash
python -m app.cli.qa "Question?" --api http://myserver:8001
```

## Output

### With Rich (Pretty Output)

When `rich` is installed, the CLI shows formatted output with:
- Colored panels for questions and answers
- Formatted metadata table
- Confidence indicator (green/yellow/red based on score)

### Without Rich (Plain Text)

Plain text output with:
- Clear separation between Q/A
- Confidence score
- Source attribution

## Response Format

Each response includes:

- **answer**: The generated answer from the RAG system
- **confidence**: Confidence score (0.0 - 1.0) based on retrieval scores
- **source**: Attribution (e.g., "RAG (retriever + GroqProvider)")

## Batch Results

Batch mode saves results with timestamp to `app/cli/batch_results_YYYYMMDD_HHMMSS.json`:

```json
[
  {
    "question": "EU DEVO DECLARAR IMPOSTO DE RENDA?",
    "response": {
      "answer": "...",
      "confidence": 0.85,
      "source": "RAG (retriever + GroqProvider)"
    }
  },
  ...
]
```

## Troubleshooting

### "Cannot reach API" error

Make sure the API server is running:

```bash
# In another terminal
cd /home/decode/workspace/lion
source venv/bin/activate
uvicorn app.api.app:app --host 127.0.0.1 --port 8001
```

### Slow responses

The first request may be slow as the retrieval system initializes:
- HybridRetriever loads the vector store and BM25 index
- Subsequent requests are faster

For batch processing, the CLI adds small delays between requests.

### Import errors

If you get import errors, make sure you're:
1. In the correct virtual environment: `source venv/bin/activate`
2. In the project root: `cd /home/decode/workspace/lion`
3. Have installed dependencies: `pip install -r app/api/requirements.txt`

## Architecture

The CLI uses a `LIONClient` class to communicate with the API:

1. **Connection Verification**: Checks API health before processing
2. **Request Handling**: Sends questions to `/ask` endpoint
3. **Response Formatting**: Displays results with optional rich formatting
4. **Error Handling**: Graceful error messages for connection/timeout issues

## Configuration

The CLI reads from the same `.env` file as the API:

```env
# API endpoint
# Default: http://127.0.0.1:8001

# Retrieval type (set in API, not CLI)
RETRIEVAL_TYPE=hybrid
TOP_K=5
HYBRID_ALPHA=0.7
```

See API documentation for configuration details.
