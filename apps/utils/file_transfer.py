import pypandoc

def word_to_markdown(input_file, output_file):
    '''
    Convert Word document to Markdown format
    '''
    try:
        # Call pypandoc for conversion
        output = pypandoc.convert_file(input_file, 'markdown', outputfile=output_file)
        if output == '':
            print(f"Successfully converted {input_file} to {output_file}")
        else:
            print("Issue occurred during conversion:", output)
    except Exception as e:
        print(f"Conversion failed: {e}")


