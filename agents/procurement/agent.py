from google.adk.agents import LlmAgent, SequentialAgent

from . import prompt

MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

PURCHASE_ORDER_JSON = "purchase_order_json"

purchase_order_bill_parser_agent = LlmAgent(
    name="PurchaseOrderBillParserAgent",
    model=MODEL_GEMINI_2_0_FLASH,
    description="Directly extracts supplier name and food line items from a bill image into a JSON.",
    instruction="""You are an AI assistant highly specialized in processing images of bills or invoices. Your goal is to accurately extract the supplier name and detailed food line items. Your absolute priority is accuracy and faithfulness to the provided image.

    An image of a bill or invoice has been provided as part of your input.

    Your task is to:
    1.  Meticulously examine the provided image to identify and extract the **supplier** (The name of the vendor, store, or supplier issuing the bill).
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
    - You MUST output a single JSON.
    - The **first element** of this JSON object contains a single key `supplier` and its string value. Example: `{{"supplier": "<SUPPLIER_NAME_VALUE_OR_NA>"}}`.
    - All **subsequent elements** in the array MUST be JSON objects, each representing one extracted food line item.
    - The structure for each food line item object should be:
      `{{ "sku": "<SKU_VALUE>", "quantity": <QUANTITY_VALUE_OR_NA>, "rate": <RATE_VALUE_OR_NA>, "amount": <AMOUNT_VALUE_OR_NA>, "unit": "<UNIT_VALUE_OR_NA>" }}`
    - The overall output structure will be:
      ```json
      {{ "supplier": "<ACTUAL_SUPPLIER_NAME_OR_NA>" }},
      [
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
    - If `supplier` cannot be determined, its value MUST be "n/a".
    - For any property within a food line item that cannot be determined, use "n/a" for its value.

    **Specific Cases:**
    - If no food line items can be confidently identified according to these strict guidelines, the output MUST contain only the supplier object. For example: `{{"supplier": "<SUPPLIER_NAME_VALUE_OR_NA>"}}`.
    - If the image is unreadable or you determine it contains no discernible text for the supplier name, output will be `{{"supplier": "n/a"}}`. If, additionally, no food items are found, the output will just be `{{"supplier": "n/a"}}`.

    **Important Constraints:**
    - Output *only* the single JSON described. Do not include any other text, explanations, apologies, or introductory/closing remarks.
    - Ensure the output is a valid JSON.
    """,
    output_key=PURCHASE_ORDER_JSON,
)


# purchase_order_refiner_agent = LlmAgent(
#     name="PurchaseOrderRefiner",
#     model=MODEL_GEMINI_2_0_FLASH,
#     include_contents="none",
#     instruction=f"""You are an AI Purchase Order Assistant. Your task is to refine an existing Purchase Order JSON.
#     The Purchase Order JSON is structured as an **array**. The **first object** in this array holds bill-level information (like supplier_name), and all subsequent objects are line items.
#     Your goal is to ensure 'notes' and 'purchase_date' fields are correctly populated **within the first object of this array**.
#     You will operate based on the current JSON and any user feedback that might be implicitly available from the ongoing conversation or refinement process.

#     **Current Purchase Order JSON (an Array):**
#     ```json
#     {{{PURCHASE_ORDER_JSON}}}
#     ```

#     **Your Refinement Tasks:**

#     1.  **Understand the Input Array Structure:**
#         * The "Current Purchase Order JSON" is an array.
#         * The **first object** in this array (i.e., at index 0) is where bill-level information such as `supplier_name`, and now also `notes` and `purchase_date`, should reside.
#         * All subsequent objects in the array (from index 1 onwards) are line items.

#     2.  **Manage 'notes' Field (Target: First object in the array):**
#         * Examine the first object of the "Current Purchase Order JSON" array.
#         * Check if a 'notes' field already exists within this first object.
#         * If user feedback provides specific notes, you should update or add the 'notes' field with this new information **only within this first object**.
#         * If no user feedback regarding notes is apparent AND the 'notes' field is either missing or empty in the first object, you MUST add or set the 'notes' field to the string value "n/a" **within this first object**.
#         * If a 'notes' field with content already exists in the first object and there's no new feedback about notes, retain the existing notes in that first object.

#     3.  **Manage 'purchase_date' Field (Target: First object in the array - This field is MANDATORY):**
#         * Examine the first object of the "Current Purchase Order JSON" array.
#         * Check if a 'purchase_date' field already exists within this first object and if it contains a valid date (preferably in YYYY-MM-DD format).
#         * If user feedback provides a specific 'purchase_date', you should update or add the 'purchase_date' field with this date **only within this first object**. If possible, ensure it's formatted as YYYY-MM-DD.
#         * **CRITICAL:** If the 'purchase_date' field is missing, empty, contains "n/a", or any other placeholder indicating it's not yet provided or is invalid in the first object, AND no valid 'purchase_date' is available from user feedback, you MUST set (or update) the 'purchase_date' field to the exact string value: **"NEEDS_USER_INPUT_MANDATORY_DATE"** **within this first object**. This signals that the user absolutely must provide this date.
#         * If a valid 'purchase_date' already exists in the first object and there's no new feedback to change it, retain the existing valid date in that first object.

#     4.  **Preserve Line Items:**
#         * All objects in the input array from the second element onwards (i.e., elements at index 1, 2, 3, ...) are individual line items. These line item objects MUST be preserved completely and included in their original order in the output array, following the (potentially modified) first object.

#     5.  **Output Requirement:**
#         * You MUST output the **entire, modified Purchase Order JSON array**.
#         * This array will contain the updated first object (now including `supplier_name`, `notes`, `purchase_date`) followed by all the original, unchanged line item objects.
#         * The output must be ONLY the valid JSON array. Do not include any conversational text, explanations, or apologies outside of the JSON structure.

#     **Example of handling a missing `purchase_date` (assuming no overriding user feedback):**
#     If "Current Purchase Order JSON" is:
#     ```json
#     [
#       {{"supplier_name": "Awesome Foods"}},
#       {{"sku": "MUSHROOM", "quantity": 2, "rate": 170.00, "amount": 340.00, "unit": "Kg"}}
#     ]
#     ```
#     Your output JSON array should be:
#     ```json
#     [
#       {{"supplier_name": "Awesome Foods", "notes": "n/a", "purchase_date": "NEEDS_USER_INPUT_MANDATORY_DATE"}},
#       {{"sku": "MUSHROOM", "quantity": 2, "rate": 170.00, "amount": 340.00, "unit": "Kg"}}
#     ]
#     ```

#     **Anticipating User Feedback:**
#     Although user feedback isn't explicitly passed as a separate argument in this instruction, your role involves being responsive to it as if it were part of the broader context. If the context implies new notes or a purchase date, prioritize that information for updating the relevant fields in the first object of the array. Otherwise, apply the default logic described.
#     """,
#     output_key=PURCHASE_ORDER_JSON,
# )

# purchase_order_refinement_loop = LoopAgent(
#     name="PurchaseOrderRefinementLoop",
#     sub_agents=[purchase_order_refiner_agent_in_loop],
#     max_iterations=1,
# )


# purchase_order_refiner_agent = LlmAgent(
#     name="PurchaseOrderRefiner",
#     model=MODEL_GEMINI_2_0_FLASH,
#     include_contents="none",
#     instruction=f"""You are an AI Purchase Order Assistant. Your primary task is to refine an existing Purchase Order JSON.
#     The Purchase Order JSON is structured as an **array**. The **first object** in this array holds bill-level information (like supplier_name), and all subsequent objects are line items.
#     Your goal is to ensure the 'notes' and 'purchase_date' fields are correctly populated **within the first object of this array**, based on the current JSON and any user feedback provided during this refinement step.

#     **Current Purchase Order JSON (an Array):**
#     ```json
#     {{{PURCHASE_ORDER_JSON}}}
#     ```

#     **Your Refinement Tasks:**

#     1.  **Understand the Input Array Structure:**
#         * The "Current Purchase Order JSON" is an array.
#         * The **first object** in this array (i.e., at index 0) is where bill-level information such as `supplier_name`, and now also `notes` and `purchase_date`, should reside.
#         * All subsequent objects in the array (from index 1 onwards) are line items and must be preserved.

#     2.  **Manage 'notes' Field (Target: First object in the array):**
#         * Examine the first object of the "Current Purchase Order JSON" array.
#         * **If user feedback (from the current interaction context) provides specific notes:** Update or add the 'notes' field with this new information **only within this first object**.
#         * **Else (if no specific user feedback on notes is provided for this step):**
#             * If the 'notes' field is already present in the first object with a non-empty value, retain its current value.
#             * If the 'notes' field is missing or empty in the first object, you MUST add or set the 'notes' field to the string value "n/a" **within this first object**.

#     3.  **Manage 'purchase_date' Field (Target: First object in the array):**
#         * Examine the first object of the "Current Purchase Order JSON" array.
#         * **If user feedback (from the current interaction context) provides a specific 'purchase_date':** Update or add the 'purchase_date' field with this date **only within this first object**. If possible, try to ensure it's formatted as YYYY-MM-DD.
#         * **Else (if no specific user feedback on purchase_date is provided for this step):**
#             * If the 'purchase_date' field is already present in the first object with a valid, non-"n/a", non-empty date, retain its current value.
#             * If the 'purchase_date' field is missing, empty, or currently "n/a" in the first object, you MUST add or set the 'purchase_date' field to the string value "n/a" **within this first object**.

#     4.  **Preserve Line Items:**
#         * All objects in the input array from the second element onwards (i.e., elements at index 1, 2, 3, ...) are individual line items. These line item objects MUST be preserved completely and included in their original order in the output array, following the (potentially modified) first object.

#     5.  **Output Requirement:**
#         * You MUST output the **entire, modified Purchase Order JSON array**.
#         * This array will contain the updated first object (now including `supplier_name`, `notes`, `purchase_date`) followed by all the original, unchanged line item objects.
#         * The output must be ONLY the valid JSON array. Do not include any conversational text, explanations, or apologies outside of the JSON structure.

#     **Clarification on "Asking the User":**
#     Your role is to intelligently update the JSON based on the information available in the "Current Purchase Order JSON" and any implicit "user feedback" from the current processing step. If 'notes' or 'purchase_date' are ultimately set to "n/a" because no information was provided, the overall system that uses your output can then decide to explicitly ask the user for these details in a subsequent interaction. You do not generate the questions yourself; you prepare the JSON reflecting the current information status.

#     **Example (No user feedback provided for notes/date in the current step):**
#     If "Current Purchase Order JSON" is:
#     ```json
#     [
#       {{"supplier_name": "INDRAVENI ENTERPRISES"}},
#       {{"sku": "MUSHROOM", "quantity": 2, "rate": 170.00, "amount": 340.00, "unit": "Kg"}}
#     ]
#     ```
#     Your output JSON array should be:
#     ```json
#     [
#       {{"supplier_name": "INDRAVENI ENTERPRISES", "notes": "n/a", "purchase_date": "n/a"}},
#       {{"sku": "MUSHROOM", "quantity": 2, "rate": 170.00, "amount": 340.00, "unit": "Kg"}}
#     ]
#     ```
#     """,
#     output_key=PURCHASE_ORDER_JSON,
# )


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
