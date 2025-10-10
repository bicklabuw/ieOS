from Display import SCREEN_WIDTH

def add_newlines_to_oveflowing_text(text: str, size: int, screen_size: int = SCREEN_WIDTH, split_at_whitespace: bool = True) -> str:
    """
    Adds newlines to the text if it overflows the screen size.
    
    :param text: The text to be processed.
    :param size: The size of the text in pixels.
    :param screen_size: The maximum allowed size in pixels.
    :return: The processed text with newlines added if necessary.
    """
    if size <= screen_size:
        return text
    
    # Determine longest line by characters and determine the max number of characters per line
    lines = text.split('\n')
    longest_line_len = max(len(line) for line in lines)
    char_size = size / longest_line_len
    max_chars_per_line = screen_size // char_size
    if max_chars_per_line <= 0:
        ValueError("Max characters per line must be greater than 0")

    # Split the text into lines based on the max characters per line
    new_lines = []
    for line in lines:
        if len(line) <= max_chars_per_line:
            new_lines.append(line)
        else:
            if split_at_whitespace:
                # Split at whitespace
                words = line.split()
                current_line = ""
                for word in words:
                    if len(current_line) + len(word) + 1 <= max_chars_per_line:
                        current_line += (word + " ")
                    else:
                        new_lines.append(current_line.strip())
                        current_line = word + " "
                if current_line:
                    new_lines.append(current_line.strip())
            else:
                # Split at character limit
                for i in range(0, len(line), max_chars_per_line):
                    new_lines.append(line[i:i + max_chars_per_line])

    # Join the new lines with newline characters
    return '\n'.join(new_lines)
