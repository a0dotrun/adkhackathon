from google.adk.agents import LlmAgent, SequentialAgent

from . import prompt

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

PURCHASE_ORDER_JSON = "purchase_order_json"


purchase_order_bill_parser_agent = LlmAgent(
    name="PurchaseOrderBillParser",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Directly extracts food line items (SKU, Quantity, Rate, Amount, Unit) from an image of a bill into JSON format.",  # New description
    instruction="""You are an AI assistant specialized in processing images of bills or invoices, with a focus on identifying food items.
    An image of a bill or invoice has been provided as part of your input.

    Your task is to:
    1. Carefully examine the provided image to identify all line items that appear to be food products.
    2. For each distinct food line item identified, extract the following details:
        - sku (the name of the food item, e.g., "Organic Apples", "Whole Milk 1L", "SNK045-Banana Chips")
        - quantity (the number of units purchased for that item)
        - rate (the price per single unit of the item)
        - amount (the total cost for that line item, usually quantity * rate)
        - unit (the unit of measure for the quantity, e.g., "kg", "g", "lb", "liter", "ml", "pack", "bottle", "each", "item", "bunch"). If the unit is part of the SKU or implied by the item description, extract it. If it's a count of individual items, "item" or "each" is appropriate.

    Output Format:
    - You MUST output the extracted food line items as a JSON array. Each object in the array should represent one food line item.
    - The format for each line item object should be:
      `{{"sku": "<SKU_VALUE>", "quantity": <QUANTITY_VALUE>, "rate": <RATE_VALUE>, "amount": <AMOUNT_VALUE>, "unit": "<UNIT_VALUE>"}}`

    Handling Missing Information:
    - For each food line item, if any of its properties (sku, quantity, rate, amount, unit) cannot be reliably determined from the image, you MUST use the string placeholder "n/a" for that property's value within that line item's JSON object.
    - Numeric values for quantity, rate, and amount should be represented as numbers in the JSON if possible (e.g., `10`, `15.75`). If they are truly unobtainable or cannot be reasonably inferred as numbers, use "n/a". Sku and unit are typically strings.

    Specific Cases:
    - If no food line items can be identified in the image, you MUST output an empty JSON array: `[]`.
    - If the image is unreadable or you determine it contains no discernible text relevant to food items, also output an empty JSON array: `[]`.

    Important Constraints:
    - Output *only* the JSON array. Do not include any other text, explanations, apologies, or introductory/closing remarks.
    - Ensure your output is a valid JSON.
    """,
    output_key=PURCHASE_ORDER_JSON,
)


purchase_order_workflow_agent = SequentialAgent(
    name="PurchaseOrderWorkflow",
    sub_agents=[
        purchase_order_bill_parser_agent,
    ],
    description="Processes a Purchase Order Bill image and returns extracted food line items in JSON format.",
)


coordinator = LlmAgent(
    name="ProcurementCoordinator",
    model=MODEL_GEMINI_2_0_FLASH,
    description="A comprehensive procurement assistant that helps manage purchase orders",
    instruction=prompt.PRECUREMENT_COORDINATOR_PROMPT,
    sub_agents=[purchase_order_workflow_agent],
)
root_agent = coordinator
