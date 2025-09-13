import os
import logging
import json
from google import genai
from dotenv import load_dotenv
import time
import demjson3
from google.genai import errors as genai_errors

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

class Classifier:
    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.client = genai.Client(api_key=API_KEY)
        self.model_name = model_name

    def build_prompt(self, content: str, final_data: list) -> str:
        return (
            "You are an assistant that classifies university exam questions into topics.\n"
            "You will be given:\n"
            "1. A new question paper.\n"
            "2. The current list of topics (as JSON).\n\n"
            "Your task is to update the JSON with the new questions. Follow these rules:\n"
            "- Be extremely specific"
            "- Do NOT rename existing topics.\n"
            "- Keep the existing topics in the JSON.\n"
            "- Keep the topics as specific as possible.\n"
            "- Try to classify the questions into existing topics.\n"
            "- Merge similar topics into a single topic key.\n"
            "- Some questions may refer to figures or diagrams. If so, rephrase them to be self-contained without referring to any figure.\n"
            "- For questions or subparts that are incomplete (e.g. 'i) Priority Queue'), rephrase them into full questions (e.g. 'Explain what a priority queue is.').\n"
            "- Do NOT include sub-labels like (a), (b), (i), etc. in the question text.\n"
            "- Remove duplicates across all topics.\n"
            "- Do NOT wrap the output in triple backticks or provide any explanation. Output only valid, complete JSON.\n\n"
            "- Order the topics into the order they must be studied in.\n"
            "- Escape quotes in the question text.\n"
            "Remember to not rename existing topics.\n"
            # "- For questions involving math, enclose the math expressions in dollar signs (e.g. $x^2 + y^2 = z^2$).\n\n"
            "Format example:\n"
            "{\n"
            "  \"Topic A\": [\"What is memory management?\", \"Explain paging.\\nExplain segmentation.\"],\n"
            "  \"Topic B\": [\"Define recursion.\", \"Differentiate between BFS and DFS.\"]\n"
            "}\n\n"
            f"New Question Paper:\n{content}\n\n"
            f"Current JSON:\n{json.dumps(final_data, indent=2, ensure_ascii=False)}\n"
        )

    def generate_text(self, prompt, max_retries=5, base_delay=5):
        """
        Call Google GenAI with retries/backoff for transient errors like 503.
        """
        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                )
                return response.text  # or whatever attribute your SDK returns

            except genai_errors.ServerError as e:
                wait_time = base_delay * attempt
                logging.warning(
                    f"⚠️ Model overloaded (503). Attempt {attempt}/{max_retries}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)

            except Exception as e:
                logging.error(f"❌ Unexpected error in generate_text: {e}")
                raise

        # If all retries fail:
        raise RuntimeError(f"Failed to get response from model after {max_retries} retries")


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

    def classify_questions(self, text_files_dir: str, max_retries: int = 3, delay: int = 2):
        final_data = set()
        os.makedirs("./output", exist_ok=True)

        for idx, filename in enumerate(os.listdir(text_files_dir)):
            if not filename.endswith(".txt"):
                continue

            filepath = os.path.join(text_files_dir, filename)
            try:
                with open(filepath, "r", encoding="utf-8") as file:
                    content = file.read()
            except Exception as e:
                logging.error(f"❌ Failed to read {filepath}: {e}")
                continue

            # Retry loop for API / parsing
            for attempt in range(1, max_retries + 1):
                try:
                    prompt = self.build_prompt(content, list(final_data))
                    response_text = self.generate_text(prompt)
                    new_data = self.clean_json(response_text)

                    output_path = f"./output/classified_questions_{idx}.json"
                    with open(output_path, "w", encoding="utf-8") as outfile:
                        json.dump(new_data, outfile, indent=2, ensure_ascii=False)

                    if final_data:
                        final_data.update(new_data.keys())

                    logging.info(f"✅ Processed {filename} -> {output_path}")
                    break  # success, exit retry loop

                except Exception as e:
                    logging.warning(f"⚠️ Error processing {filename} (attempt {attempt}/{max_retries}): {e}")
                    if attempt < max_retries:
                        time.sleep(delay * attempt)  # exponential-ish backoff
                    else:
                        logging.error(f"❌ Giving up on {filename} after {max_retries} attempts")

            time.sleep(2)  # prevent rate limiting
