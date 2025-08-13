from agents import Agent, Runner, TResponseInputItem, function_tool, WebSearchTool
import os
import json
import uuid
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel
from starlette.status import HTTP_403_FORBIDDEN
import requests
from dotenv import load_dotenv
from agents import Agent, Runner, gen_trace_id, trace, ModelSettings
from agents.mcp import MCPServerStdio, MCPServer

# Load environment variables
load_dotenv()

API_KEY = os.getenv("API_KEY")
API_KEY_NAME = "x-api-key"

STRIPE_API_KEY = os.getenv("STRIPE_API_KEY")

# Agent Function

conversation: list[TResponseInputItem] = []

async def run_quotation_agent(message: str):

  async with MCPServerStdio(
    name="Stripe MCP Server",
    params={
      "command": "npx",
      "args": [
        "-y",
        "@stripe/mcp",
        "--tools=all",
        "--api-key=" + STRIPE_API_KEY
      ]
    },
    client_session_timeout_seconds=180
  ) as stripe_mcp_server:

    # You should customise this agent's prompt to suit your needs and your business.

    invoicing_agent = Agent(
      name="Invoicing Agent",
      instructions=f"""
      <background>
      You are finance assistant that is responsible for generating and managing the invoicing process for a company. Your job is to enable the user to communicate with you using natural language to instruct you to perform tasks related to invoicing. You have the ability to create invoices, update invoices, manage customer accounts, send follow ups and more. Your invoicing capabilities are provided using the Stripe MCP server, which gives you access to Stripe's API.
      </background>
      <task>
      Using the information in the conversation history, you need to execute the actions instructed to you by the user. If you do not have enough information to complete the task or you run into any issues, you should ask the user for clarification or additional information.
      </task>
      <tools>
        - Stripe MCP Server (Stripe API)
      </tools>
      <output>
      Communicate with the end user in a polite and friendly tone. Your message responses should be clear and concise. Do not provide any unnecessary information or jargon.
      </output>
      """,
      output_type=str,
      mcp_servers=[stripe_mcp_server],
      model="gpt-4o",
      model_settings=ModelSettings(truncation="auto")
    )

    # Add the message to the conversation
    conversation.append({
      "role": "user",
      "content": message
    })

    result = await Runner.run(invoicing_agent, conversation)

    if result and result.final_output:
      conversation.append({
        "role": "assistant",
        "content": result.final_output
      })
    else:
      conversation.append({
        "role": "assistant",
        "content": "No response from agent."
      })

    return result

# FastAPI Setup

api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

app = FastAPI()

def verify_api_key(api_key: str = Depends(api_key_header)):
  if api_key != API_KEY:
    raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Invalid API Key")
  return api_key

@app.get("/")
def read_root(api_key: str = Depends(verify_api_key)):
  return {"message": "API is working"}

@app.post("/clear-chat")
def clear_chat(api_key: str = Depends(verify_api_key)):
  """Clear the conversation history"""
  global conversation
  conversation.clear()
  return {"message": "Chat history cleared successfully", "success": True}

class ConnectionManager:
  def __init__(self):
    self.active_connections: list[WebSocket] = []

  async def connect(self, websocket: WebSocket):
    await websocket.accept()
    self.active_connections.append(websocket)

  def disconnect(self, websocket: WebSocket):
    self.active_connections.remove(websocket)

  async def send_message(self, message: str, websocket: WebSocket):
    await websocket.send_text(message)

  async def broadcast(self, message: str):
    for connection in self.active_connections:
      await self.send_message(message, connection)

manager = ConnectionManager()

class ChatMessage(BaseModel):
  session_id: str
  message: str
  user_id: str = "user"
  timestamp: str | None = None
  message_type: str = "chat"

class ChatResponse(BaseModel):
  session_id: str
  message: str
  sender: str = "agent"
  timestamp: str
  message_type: str = "response"
  success: bool = True
  error: str | None = None

@app.websocket("/ws/chat")
async def websocket_endpoint(websocket: WebSocket):
  await manager.connect(websocket)
  session_id = str(uuid.uuid4())
  print(f"New WebSocket connection established with session ID: {session_id}")
  
  try:
    while True:
      # Receive message from client
      data = await websocket.receive_text()
      
      try:
        # Parse incoming JSON message
        message_data = json.loads(data)
        chat_message = ChatMessage(**message_data)
        
        # Check if this is a clear command
        if chat_message.message_type == "clear" or chat_message.message.lower().strip() == "/clear":
          global conversation
          conversation.clear()
          response = ChatResponse(
            session_id=chat_message.session_id,
            message="Chat history has been cleared.",
            timestamp=datetime.now().isoformat()
          )
        else:
          # Process the message with the agent
          agent_response = await process_chat_message(chat_message.message)
          
          # Create response
          response = ChatResponse(
            session_id=chat_message.session_id,
            message=agent_response,
            timestamp=datetime.now().isoformat()
          )
        
        # Send response back to client
        await manager.send_message(response.model_dump_json(), websocket)
          
      except json.JSONDecodeError:
        # Handle plain text messages for backward compatibility
        agent_response = await process_chat_message(data)
        response = ChatResponse(
          session_id=session_id,
          message=agent_response,
          timestamp=datetime.now().isoformat()
        )
        await manager.send_message(response.model_dump_json(), websocket)
          
      except Exception as e:
        # Handle errors
        error_response = ChatResponse(
          session_id=session_id,
          message="Sorry, I encountered an error processing your message.",
          timestamp=datetime.now().isoformat(),
          success=False,
          error=str(e)
        )
        await manager.send_message(error_response.model_dump_json(), websocket)
                
  except WebSocketDisconnect:
    manager.disconnect(websocket)
    print(f"WebSocket connection closed for session: {session_id}")

async def process_chat_message(message: str) -> str:
  """Process chat message with the quotation agent"""
  try:
    # Run the quotation agent with the user's message
    result = await run_quotation_agent(message)
    
    # Return the agent's final output
    if result and result.final_output:
      return result.final_output
    else:
      return "I couldn't process your request at the moment. Please try again."
          
  except Exception as e:
    print(f"Error processing message: {e}")
    return "I encountered an error while processing your message. Please try again."
