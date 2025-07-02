import json

class Converter:
    def __init__(self, json_file_path: str, markdown_file_path: str):
        self.json_file_path = json_file_path
        self.markdown_file_path = markdown_file_path
        self.data = self.load_json()
    
    def load_json(self):
        """
        Loads JSON data from the specified file path
        """
        with open(self.json_file_path, 'r', encoding='utf-8') as json_file:
            return json.load(json_file)

    def convert_json(self):
        """
        Converts the loaded JSON data into Markdown
        """
        with open(self.markdown_file_path, 'w', encoding='utf-8') as md_file:
            for topic, questions in self.data.items():
                md_file.write(f"## {topic}\n\n")
                for question in questions:
                    md_file.write(f"- {question}\n")
                md_file.write("\n")

