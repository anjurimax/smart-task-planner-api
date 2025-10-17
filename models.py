from pydantic import BaseModel, Field
from typing import List

# -----------------
# Task Structure
# -----------------
class Task(BaseModel):
    """Defines a single actionable task."""
    task_id: int = Field(..., description="A unique integer ID for the task.")
    name: str = Field(..., description="A clear, actionable description of the task.")
    estimated_days: float = Field(..., description="The estimated time to complete the task in days (e.g., 1.5).")
    suggested_deadline: str = Field(..., description="The relative deadline, e.g., 'Day 3', 'End of Week 1'.")
    dependencies: List[int] = Field(..., description="A list of task_ids that must be completed before this task starts. Empty if none.")

# -----------------
# Final Plan Structure
# -----------------
class TaskPlan(BaseModel):
    """The complete structured output for the Smart Task Planner."""
    goal_title: str = Field(..., description="The original goal, reformatted as a title.")
    total_estimated_days: float = Field(..., description="The sum of all estimated_days for all tasks.")
    tasks: List[Task] = Field(..., description="The detailed, ordered list of tasks required to achieve the goal.")