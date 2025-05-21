from google.adk.agents import LlmAgent, SequentialAgent

from . import prompt

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

PURCHASE_ORDER_JSON = "purchase_order_json"

purchase_order_bill_parser_agent = LlmAgent(
    name="PurchaseOrderBillParser",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Directly extracts supplier name and food line items from a bill image into a JSON array.",
    instruction="""You are an AI assistant highly specialized in processing images of bills or invoices. Your goal is to accurately extract the supplier name and detailed food line items. Your absolute priority is accuracy and faithfulness to the provided image.

    An image of a bill or invoice has been provided as part of your input.

    Your task is to:
    1.  Meticulously examine the provided image to identify and extract the **supplier_name** (The name of the vendor, store, or supplier issuing the bill).
    2.  Identify all **line items** in the image that appear to be **food products**.
    3.  For each distinct food line item clearly visible and legible, extract the following details:
        * `sku` (the exact name or identifier of the food item as it appears, e.g., "Organic Apples", "Whole Milk 1L")
        * `quantity` (the number of units purchased for that item)
        * `rate` (the price per single unit of the item)
        * `amount` (the total cost for that line item, usually quantity * rate)
        * `unit` (the unit of measure for the quantity, e.g., "kg", "g", "lb", "liter", "ml", "pack", "bottle", "each", "item", "bunch").

    **CRITICAL ACCURACY GUIDELINES:**
    - **DO NOT GUESS OR INVENT ANY INFORMATION.** If the supplier name or any part of a line item's details (sku, quantity, rate, amount, unit) is not clearly visible, legible, or confidently determinable from the image, you MUST use the string placeholder "n/a" where appropriate (e.g., for the supplier_name's value, or for values within line item objects).
    - **Extract ONLY what is present in the image.** Do not add items or details not listed or supported by clear visual evidence.
    - If a line item is ambiguous or might not be a food item, err on the side of caution and DO NOT include it.

    **Output Format:**
    - You MUST output a single JSON array.
    - The **first element** of this array MUST be a JSON object containing a single key `supplier_name` and its string value. Example: `{{"supplier_name": "<SUPPLIER_NAME_VALUE_OR_NA>"}}`.
    - All **subsequent elements** in the array MUST be JSON objects, each representing one extracted food line item.
    - The structure for each food line item object should be:
      `{{ "sku": "<SKU_VALUE>", "quantity": <QUANTITY_VALUE_OR_NA>, "rate": <RATE_VALUE_OR_NA>, "amount": <AMOUNT_VALUE_OR_NA>, "unit": "<UNIT_VALUE_OR_NA>" }}`
    - The overall output structure will be:
      ```json
      [
        {{ "supplier_name": "<ACTUAL_SUPPLIER_NAME_OR_NA>" }},
        {{
          "sku": "<SKU_1>", "quantity": <Q1_OR_NA>, "rate": <R1_OR_NA>, "amount": <A1_OR_NA>, "unit": "<U1_OR_NA>"
        }},
        {{
          "sku": "<SKU_2>", "quantity": <Q2_OR_NA>, "rate": <R2_OR_NA>, "amount": <A2_OR_NA>, "unit": "<U2_OR_NA>"
        }}
        // ... more items if present
      ]
      ```
    - `quantity`, `rate`, and `amount` should be numeric if possible, otherwise "n/a". Other fields are strings.

    **Handling Missing Information (Reiteration):**
    - If `supplier_name` cannot be determined, its value in the first object of the array MUST be "n/a".
    - For any property within a food line item that cannot be determined, use "n/a" for its value.

    **Specific Cases:**
    - If no food line items can be confidently identified according to these strict guidelines, the output array MUST contain only the supplier name object. For example: `[ {{"supplier_name": "<SUPPLIER_NAME_VALUE_OR_NA>"}} ]`.
    - If the image is unreadable or you determine it contains no discernible text for the supplier name, the first object MUST be `{{"supplier_name": "n/a"}}`. If, additionally, no food items are found, the output array will just be `[ {{"supplier_name": "n/a"}} ]`.

    **Important Constraints:**
    - Output *only* the single JSON array described. Do not include any other text, explanations, apologies, or introductory/closing remarks.
    - Ensure the output is a valid JSON.
    """,
    output_key=PURCHASE_ORDER_JSON,
)


purchase_order_workflow_agent = SequentialAgent(
    name="PurchaseOrderWorkflow",
    sub_agents=[
        purchase_order_bill_parser_agent,
    ],
    description="Processes Purchase Order Bill image and returns extracted food line items in JSON format.",
)


coordinator = LlmAgent(
    name="ProcurementCoordinator",
    model=MODEL_GEMINI_2_0_FLASH,
    description="A comprehensive procurement assistant that helps manage purchase orders",
    instruction=prompt.PRECUREMENT_COORDINATOR_PROMPT,
    sub_agents=[purchase_order_workflow_agent],
)
root_agent = coordinator
