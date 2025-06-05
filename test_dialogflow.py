from google.cloud import dialogflow

project_id = "recipebot-kqou"
session_id = "test-session"
text = "hi"

session_client = dialogflow.SessionsClient()
session = session_client.session_path(project_id, session_id)

text_input = dialogflow.TextInput(text=text, language_code="en")
query_input = dialogflow.QueryInput(text=text_input)

try:
    response = session_client.detect_intent(request={"session": session, "query_input": query_input})
    print("Detected Intent:", response.query_result.intent.display_name)
    print("Response:", response.query_result.fulfillment_text)
except Exception as e:
    print("Error:", e)
