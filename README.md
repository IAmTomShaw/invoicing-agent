# Invoicing Agent

This Invoicing Agent enables a user to interactively manage invoicing, customer details and more via a chat interface.

## Demo Purpose

This repository demonstrates how agents can use MCP servers to manage context, handle real-time communication, and provide intelligent assistance for business workflows like invoicing.

## 🚀 Features

- **Real-time WebSocket Communication**: Interactive chat interface with instant responses
- **Invoice Generation**: Paste or enter client invoice details and receive a professional invoice
- **Conversational Clarification**: Chat with the agent to clarify invoice items, request breakdowns, or ask questions about the invoice
- **Session Management**: Maintains conversation context across multiple interactions
- **Easy Reset**: Clear conversations both on the frontend and backend

## 🏗️ Architecture

The system consists of two main components:

1. **MCP WebSocket Agent** ([main.py](main.py)): Core AI agent with FastAPI WebSocket server, orchestrated via MCP
2. **Streamlit Frontend** ([frontend.py](frontend.py)): Web interface for interactive invoice creation and review

## 🛠️ Setup

### Prerequisites

- Python 3.13+
- OpenAI API key
- Stripe API Key (to be provided to the MCP Server)


### Installation

1. Clone the repository:
  ```bash
  git clone <repository-url>
  cd invoicing-agent
  ```

2. Install dependencies:
  ```bash
  pip install -r requirements.txt
  ```

3. Run the MCP WebSocket server:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port 8000
  ```

4. Run the Streamlit frontend:
  ```bash
  streamlit run frontend.py
  ```

5. Access the web interface at `http://localhost:8501` and connect to the WebSocket URL (default: `ws://localhost:8000/ws/chat`).



## 🔌 WebSocket API

### Connection

Connect to the WebSocket endpoint:

```
ws://localhost:8000/ws/chat
```

### Message Format

Send messages as JSON with the following structure:

```json
{
  "session_id": "unique-session-id",
  "message": "Please generate an invoice for Acme Corp, 3 items, total $1200.",
  "user_id": "user123",
  "timestamp": "2025-08-13T10:00:00Z",
  "message_type": "chat"
}
```

### Response Format

Receive responses in the following format:

```json
{
  "session_id": "unique-session-id",
  "message": "Invoice for Acme Corp generated. Total: $1200. Items: ...",
  "sender": "agent",
  "timestamp": "2025-08-13T10:00:01Z",
  "message_type": "response",
  "success": true,
  "error": null
}
```

### Special Commands

- Send `"/clear"` or set `message_type: "clear"` to reset conversation history



## 🛠️ Available Agent Actions

The agent can perform several invoice-related actions:

- **Generate Invoice**: Create a new invoice from client details and items
- **List Invoice Items**: Display all items included in the invoice
- **Clarify Invoice**: Answer questions about invoice breakdowns, totals, or terms
- **Reset Conversation**: Clear the current session and start fresh



## 🧪 Testing with Frontend

A Streamlit frontend is provided for interactive demo and testing:

```bash
streamlit run frontend.py
```

Access the web interface at `http://localhost:8501`



## 📊 Invoice Data Structure

The agent works with invoice data containing the following properties:

- **Client Name**
- **Invoice Items** (description, quantity, price)
- **Total Amount**
- **Due Date** (optional)
- **Payment Terms** (optional)



## 🔧 Configuration

Key configuration options in [main.py](main.py):

- **Model**: GPT-4o for optimal reasoning
- **Session Management**: UUID-based session tracking
- **Error Handling**: Comprehensive exception management



## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test with the WebSocket API or Streamlit frontend
5. Submit a pull request


## 📝 License

This project is licensed under the MIT License.

---

Built by [Tom Shaw](https://tomshaw.dev)