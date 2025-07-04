import json
import demjson3

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

    def convert_to_typst(self, output_path: str = 'output.typ'):
        typst_code = """
        #let question(body) = [
            #body
        ]\n
        """
        with open(self.json_file_path, 'r', encoding='utf-8') as file:
            data = demjson3.decode(file.read())

            for key, value in data.items():
                typst_code += f"#smallcaps()[== {key}]\n#line(length: 100%, stroke: 0.3pt)\n"
                for question in value:
                    escaped = json.dumps(question)[1:-1]  # escape quotes and slashes
                    typst_code += f'+ #question("{escaped}")\n\n'

        with open(output_path, 'w') as output_file:
            output_file.write(typst_code)

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

