from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool

from . import prompt

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

APP_NAME = "precurement"
USER_ID = "sanchitrk"
SESSION_ID = "1"

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

session_service = InMemorySessionService()

session = session_service.create_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID)


image_to_text_agent = LlmAgent(
    name="ImageToTextAgent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Extracts all visible text from an image bill provided in the input.",
    instruction="""An image of a bill or invoice has been provided as part of your input.
    Your task is to carefully examine this image and extract all textual content you can identify.
    Present the extracted text as a single block of text.
    Ensure your output is *only* the text extracted from the image, without any additional commentary, summarization, or conversational filler, unless the image is unreadable.
    If the image is unreadable or you determine it contains no discernible text, respond with only the phrase: "No text could be extracted from the image."

    After processing, place the extracted text into the session state under the key 'extracted_raw_text'.
    Your final response to the user/workflow should be just the extracted text itself, or the 'no text' message.
    """,
)

purchase_order_workflow_agent = SequentialAgent(
    name="PurchaseOrderWorkflowAgent",
    sub_agents=[image_to_text_agent],
    description="Processes an uploaded purchase order image by extracting its text content.",
)


coordinator = LlmAgent(
    name="ProcurementCoordinator",
    model=MODEL_GEMINI_2_0_FLASH,
    description="A comprehensive procurement assistant that helps manage purchase orders, supplier information, and bill processing.",
    instruction=prompt.PRECUREMENT_COORDINATOR_PROMPT,
    tools=[AgentTool(agent=purchase_order_workflow_agent)],
)
root_agent = coordinator
