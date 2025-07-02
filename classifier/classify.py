import os
import json
from google import genai
from dotenv import load_dotenv
import demjson3

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

class Classifier:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = model_name

    def build_prompt(self, content: str, final_data: dict) -> str:
        return (
            "You are an assistant that classifies university exam questions into topics.\n"
            "You will be given:\n"
            "1. A new question paper.\n"
            "2. The current JSON structure of previously classified questions.\n\n"
            "Your task is to update the JSON with the new questions. Follow these rules:\n"
            "- Merge similar topics into a single topic key.\n"
            "- Some questions may refer to figures or diagrams. If so, rephrase them to be self-contained without referring to any figure.\n"
            "- For questions or subparts that are incomplete (e.g. 'i) Priority Queue'), rephrase them into full questions (e.g. 'Explain what a priority queue is.').\n"
            "- Do NOT include sub-labels like (a), (b), (i), etc. in the question text.\n"
            "- Remove duplicates across all topics.\n"
            "- Do NOT wrap the output in triple backticks or provide any explanation. Output only valid, complete JSON.\n\n"
            "- Order the topics into the order they must be studied in.\n"
            "- Escape quotes in the question text.\n"
            "Format example:\n"
            "{\n"
            "  \"Topic A\": [\"What is memory management?\", \"Explain paging.\\nExplain segmentation.\"],\n"
            "  \"Topic B\": [\"Define recursion.\", \"Differentiate between BFS and DFS.\"]\n"
            "}\n\n"
            f"New Question Paper:\n{content}\n\n"
            f"Current JSON:\n{json.dumps(final_data, indent=2, ensure_ascii=False)}\n"
        )

    def generate_text(self, prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
        )
        return response.text

    def clean_json(self, json_data: str):
        json_data = json_data.strip()
        if json_data.startswith("```json"):
            json_data = json_data[7:].strip()
        if json_data.endswith("```"):
            json_data = json_data[:-3].strip()
        try:
            return demjson3.decode(json_data)
        except demjson3.JSONDecodeError as e:
            print(f"[!] Failed to decode response: {e}")
            return {}

    def classify_questions(self, text_files_dir: str):
        final_data = {}

        for filename in os.listdir(text_files_dir):
            if filename.endswith(".txt"):
                with open(os.path.join(text_files_dir, filename), "r", encoding="utf-8") as file:
                    content = file.read()
                    prompt = self.build_prompt(content, final_data)
                    response_text = self.generate_text(prompt)
                    new_data = self.clean_json(response_text)

                    for topic, questions in new_data.items():
                        if topic not in final_data:
                            final_data[topic] = []
                        for q in questions:
                            if q not in final_data[topic]:  # deduplication
                                final_data[topic].append(q)

                json.dump(final_data, open("./output/classified_questions.json", "w", encoding="utf-8"), indent=2, ensure_ascii=False)
                # print(f"Processed file: {filename}")
                # print(final_data)

        return final_data

