import os
import json

def convert_json_to_typst(filename):
    typst_code = ""
    with open(filename, 'r') as file:
        data = file.read()
        # Assuming the JSON data is a simple key-value structure
        data = json.loads(data)
        for key, value in data.items():
            typst_code += f"#smallcaps()[== {key}]\n#line(length: 100%, stroke: 0.3pt)\n"

            for question in value:
                typst_code += f"+ #question(\"{question}\")\n\n"
    with open('output.typ', 'w') as output_file:
        output_file.write(typst_code)
    print(f"Typst code has been written to output.typ")

convert_json_to_typst(os.path.join('./all_papers_classified.json'))
