# Internal Employee Chatbot

This is a chatbot application designed for internal employee use, powered by Ollama and FastAPI.

## Prerequisites

1. Python 3.8 or higher of 64 bit
2. Ollama installed and running locally
3. At least one model pulled in Ollama (e.g., llama2, mistral)

## Setup

1. Install Ollama:
   - Download the installer: https://ollama.com/download
   - Run the .exe installer and follow the instructions
   - Pull a model: `ollama pull mistral`
        >> Mistral model is small enough to run on most Windows machines with 8–16 GB RAM, and it handles structured data queries and basic natural language tasks quite well.
   - Open your browser and run this http://localhost:11434
        >> We should see "Ollama is running"

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Application

1. Start the FastAPI server:
   ```bash
   python app.py
   ```

2. The API will be available at `http://localhost:8000`

## API Endpoints

### Chat Endpoint
- **URL**: `/chat`
- **Method**: POST
- **Request Body**:
  ```json
  {
    "messages": [
      {
        "role": "user",
        "content": "Your message here"
      }
    ],
    "model": "llama2"
  }
  ```

### Health Check
- **URL**: `/`
- **Method**: GET
- **Response**: Status of the API

## Usage Example

You can test the API using curl:

```bash
curl -X POST "http://localhost:8000/chat" \
     -H "Content-Type: application/json" \
     -d '{
           "messages": [
             {
               "role": "user",
               "content": "Hello, how can I help you today?"
             }
           ],
           "model": "llama2"
         }'
```

## Development

- The application uses FastAPI for the web server
- Ollama is used for the LLM backend
- The default model is set to "llama2", but you can change it in the code or specify it in the request 