content = open('generate_answers_pdf.py', encoding='utf-8').read()
content = content.replace('print(f"PDF generated: {OUTPUT_FILE}")', 'print("PDF generated: " + OUTPUT_FILE)')
# Also replace any remaining checkmark emoji
content = content.replace('\u2705', '')
open('generate_answers_pdf.py', 'w', encoding='utf-8').write(content)
print("Fixed")
