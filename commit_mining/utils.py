def print_star(is_star=True):
    # Counter to track the number of '*' or '#' printed
    global star_count
    try:
        star_count += 1
    except NameError:
        star_count = 1  # Initialize the counter if it doesn't exist
    
    # Choose the character to print based on the boolean argument
    if is_star:
        char_to_print = '*'
    else:
        char_to_print = '#'
    
    # Print the chosen character to the terminal
    print(char_to_print, end='', flush=True)
    
    # Check if 10 '*' or '#' have been printed
    if star_count % 24 == 0:
        print()  # Start a new line

import signal

class TimeoutError(Exception):
    pass

def handler(signum, frame):
    raise TimeoutError("Timeout occurred while processing commit")
