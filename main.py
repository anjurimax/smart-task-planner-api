import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field # Ensure Field is imported

# Gemini SDK imports
from google import genai
from google.genai import types

# Local models
from models import TaskPlan

# Load environment variables ONCE at the top
load_dotenv()

# --- Core Initialization ---

# Initialize FastAPI App (Crucial: This must be the first major object defined)
# If this line is reached, the 'app' attribute will be available to Uvicorn.
app = FastAPI(
    title="Smart Task Planner API",
    description="A backend API that uses Gemini LLM for structured task planning."
)

# --- LLM Helper Function ---
def get_gemini_client():
    """Retrieves the API key and initializes the client, checking for errors."""
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    
    if not GEMINI_API_KEY:
        # Raise an HTTP exception instead of a script-stopping ValueError
        raise HTTPException(
            status_code=500,
            detail="Server Error: GEMINI_API_KEY not configured. Check the .env file."
        )
    
    # Initialize the Gemini Client
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_task_plan(goal: str) -> TaskPlan:
    """
    Calls the Gemini API to break down a goal into a structured task plan.
    """
    try:
        # Get the client here. If the key is missing, it raises an HTTPException.
        client = get_gemini_client() 
    except HTTPException:
        raise # Re-raise the error so FastAPI catches it.

    # 1. Define the system instruction for reasoning
    system_instruction = (
        "You are an expert project manager. Your task is to break down a user's high-level goal "
        "into a series of concrete, actionable tasks. You must provide a plan that includes "
        "suggested deadlines and logical dependencies. All output must strictly follow the "
        "provided JSON Schema."
    )
    
    # 2. Define the user prompt
    user_prompt = f"Break down this goal into actionable tasks: '{goal}'. " \
                  f"The total timeline implied by the goal is the constraint for the total_estimated_days."

    # 3. Configure the generation with the Pydantic schema for structured output
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=TaskPlan.model_json_schema(),
        system_instruction=system_instruction
    )

    try:
        # Call the Gemini model
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[user_prompt],
            config=config,
        )
        
        # Parse the JSON string output from the model
        json_output = json.loads(response.text)
        
        # Validate and return the plan using the Pydantic model
        return TaskPlan.model_validate(json_output)

    except (genai.errors.APIError, json.JSONDecodeError, Exception) as e:
        # Catch API errors or malformed JSON responses
        print(f"LLM/API Error: {e}")
        # Raise an exception that FastAPI will handle and return as a 500
        raise HTTPException(
            status_code=500, 
            detail=f"Error generating plan: The AI failed to produce a valid structure or API failed. Details: {type(e).__name__}"
        )


# --- Request Body Model for API Input ---
class GoalInput(BaseModel):
    goal_text: str = Field(..., example="Launch a product in 2 weeks")


# --- API Endpoint ---
@app.post("/api/v1/plan_goal", response_model=TaskPlan, tags=["Task Planner"])
def plan_goal_endpoint(goal_input: GoalInput):
    """
    Accepts a user goal and returns a structured, actionable task plan.
    """
    goal = goal_input.goal_text
    
    # Generate the plan
    task_plan = generate_task_plan(goal)
    
    # Return the validated plan (FastAPI handles serialization to JSON)
    return task_plan

# --- Root Endpoint for Health Check ---
@app.get("/", tags=["Health"])
def read_root():
    return {"status": "ok", "service": "Smart Task Planner API"}