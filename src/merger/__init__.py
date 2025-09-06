import os
import time
import google.genai
import json
from dotenv import load_dotenv
from google import genai
import demjson3

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

class Merger:
    def __init__(self, json_path, model_name: str = "gemini-2.5-flash"):
        self.json_path = json_path
        self.model_name = model_name
        self.client = genai.Client(api_key=API_KEY)
        self.cleaned_data = {}
        self.data = {}

    def load_data(self):
        filename = "classified_questions.json"
        if not os.path.exists(self.json_path):
            raise FileNotFoundError(f"JSON file not found at {self.json_path}")
        with open(self.json_path, 'r', encoding='utf-8') as file:
            self.data = json.load(file)
        return self.data

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
    
    def merge_data(self):
        prompt = f"""
        You are a data merger. You'll be given a JSON object containing questions of a particular topic, your job is to remove duplicate questions.

        You must return your response in the following JSON format:
        {{
            "topic1": ["question1", "question2", ...],
            "topic2": ["question1", "question2", ...],
            ...
        }}

        Do not enclose the output in backticks
        """

        for topic in self.data.keys():
            questions = self.data[topic]
            if not questions:
                continue
            print(f"{prompt}\n\nTopic: {topic}\nQuestions: {json.dumps(questions, ensure_ascii=False)}")
            result = self.generate_text(f"{prompt}\n\nTopic: {topic}\nQuestions: {json.dumps(questions, ensure_ascii=False)}")
            cleaned_data = self.clean_json(result)
            if cleaned_data:
                for topic in cleaned_data:
                    cleaned_data[topic] = [q.replace("\\n", "\n") for q in cleaned_data[topic]]
                self.cleaned_data[topic] = cleaned_data[topic]

        time.sleep(2)
        return self.cleaned_data

if __name__ == "__main__":
    merger = Merger(json_path="../../output/MACHINE_LEARNING/classified_questions.json")
    merger.load_data()
    merged_data = merger.merge_data()
    with open("merged_questions.json", "w", encoding="utf-8") as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=4)
    print("Merged data saved to merged_questions.json")

