import os
import time

# Import the necessary components from the fdx library
try:
    from fdx import read_fdx, FinalDraft
    print("Successfully imported read_fdx and FinalDraft from fdx library.")
except ImportError as e:
    print(f"Error: The 'fdx' library (busdriverbuddha/python-fdx) is not installed or not found correctly: {e}")
    print("Please ensure it's installed via: pip install git+https://github.com/busdriverbuddha/python-fdx.git")
    print("And that you are running this script within the correct virtual environment.")
    exit(1)


class ScriptElement:
    """
    Represents a single parsed element from a film script.
    """
    def __init__(self, type, text=None, character_name=None, dialogue_text=None, original_line_num=None):
        self.type = type  # e.g., "scene_heading", "character", "dialogue", "action", etc.
        self.text = text  # General text (for scene heading, action, parenthetical, etc.)
        self.character_name = character_name
        self.dialogue_text = dialogue_text  # Specific for dialogue elements
        self.original_line_num = original_line_num  # Useful for debugging/context

    def __repr__(self):
        if self.type == "character" and self.character_name:
            return f"<{self.type}: {self.character_name}>"
        elif self.type == "dialogue" and self.dialogue_text:
            return f"<{self.type}: '{self.dialogue_text[:50]}{'...' if len(self.dialogue_text) > 50 else ''}'>"
        elif self.text:
            return f"<{self.type}: '{self.text[:50]}{'...' if len(self.text) > 50 else ''}'>"
        else:
            return f"<{self.type}>"


class ScriptParser:
    """
    Parses a film script FDX file and extracts structured elements
    using the 'busdriverbuddha/python-fdx' library's actual API.
    """
    def __init__(self):
        self.parsed_elements = []
        self._current_character_element = None

    def parse_file(self, script_path):
        """
        Reads and parses the script FDX file, populating self.parsed_elements.

        Args:
            script_path (str): The file path to the FDX script.

        Returns:
            list: A list of ScriptElement objects.
        """
        self.parsed_elements = []
        self._current_character_element = None
        screenplay: FinalDraft = None

        try:
            screenplay = read_fdx(script_path)

            if screenplay is None:
                print("Error: read_fdx returned None. Cannot proceed with parsing.")
                return []

            if not hasattr(screenplay, 'paragraphs'):
                print("DEBUG: WARNING: 'screenplay' object DOES NOT have 'paragraphs' attribute.")
                print(f"DEBUG: Available attributes on 'screenplay' object: {dir(screenplay)}")
                return []

            line_number = 0
            for fdx_paragraph in screenplay.paragraphs:
                line_number += 1
                paragraph_type = fdx_paragraph.paragraph_type
                paragraph_text = fdx_paragraph.plain_text

                if paragraph_type == "Scene Heading":
                    self.parsed_elements.append(ScriptElement(
                        "scene_heading",
                        text=paragraph_text,
                        original_line_num=line_number
                    ))
                    self._current_character_element = None

                elif paragraph_type == "Character":
                    character_name = paragraph_text
                    new_character_element = ScriptElement(
                        "character",
                        character_name=character_name,
                        original_line_num=line_number
                    )
                    self.parsed_elements.append(new_character_element)
                    self._current_character_element = new_character_element

                elif paragraph_type == "Parenthetical":
                    self.parsed_elements.append(ScriptElement(
                        "parenthetical",
                        text=paragraph_text,
                        original_line_num=line_number
                    ))
                    # Don't reset _current_character_element here — parentheticals belong to the current character.

                elif paragraph_type == "Dialogue":
                    if self._current_character_element:
                        self.parsed_elements.append(ScriptElement(
                            "dialogue",
                            character_name=self._current_character_element.character_name,
                            dialogue_text=paragraph_text,
                            text=paragraph_text,
                            original_line_num=line_number
                        ))
                    else:
                        print(f"Warning: Dialogue found without preceding character at line {line_number}: '{paragraph_text}'")
                        self.parsed_elements.append(ScriptElement(
                            "action",
                            text=paragraph_text,
                            original_line_num=line_number
                        ))  # Fallback
                    self._current_character_element = None  # Dialogue ends character's turn

                elif paragraph_type == "Action":
                    self.parsed_elements.append(ScriptElement(
                        "action",
                        text=paragraph_text,
                        original_line_num=line_number
                    ))
                    self._current_character_element = None

                elif paragraph_type == "Transition":
                    self.parsed_elements.append(ScriptElement(
                        "transition",
                        text=paragraph_text,
                        original_line_num=line_number
                    ))
                    self._current_character_element = None

                else:
                    # Fallback for unknown types
                    self.parsed_elements.append(ScriptElement(
                        "action",
                        text=paragraph_text,
                        original_line_num=line_number
                    ))
                    self._current_character_element = None

            return self.parsed_elements

        except FileNotFoundError:
            print(f"Error: Script file not found at {script_path}")
            return []

        except Exception as e:
            print(f"An error occurred during FDX script parsing: {e}")
            return []


# -------------------- Example Usage --------------------

if __name__ == "__main__":
    script_to_parse = os.path.join("scripts", "The Purloined Millstone by E.A. Sprechmann.fdx")

    print(f"Attempting to parse FDX script from: {script_to_parse}")
    if not os.path.exists(script_to_parse):
        print(f"Error: Script file '{script_to_parse}' not found.")
        print("Please ensure your FDX script is saved in the 'scripts' folder with the correct filename.")
        print("For this test, you'll need a proper Final Draft FDX file.")
    else:
        parser = ScriptParser()

        start_time = time.perf_counter()
        parsed_elements = parser.parse_file(script_to_parse)
        end_time = time.perf_counter()

        elapsed_time = end_time - start_time

        print("\n--- Parsed Script Elements ---")
        if parsed_elements:
            for element in parsed_elements:
                print(element)
        else:
            print("No elements parsed.")

        print(f"\nFinished FDX script parsing test. Parsing took: {elapsed_time:.4f} seconds.")
