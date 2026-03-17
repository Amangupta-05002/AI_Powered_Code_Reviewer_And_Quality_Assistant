# utility_functions.py

# Function 1: Add two numbers
def add_numbers(a, b):
    return a + b


# Function 2: Subtract two numbers
def subtract_numbers(a, b):
    return a - b


# Function 3: Multiply two numbers
def multiply_numbers(a, b):
    return a * b


# Function 4: Divide two numbers
def divide_numbers(a, b):
    if b == 0:
        return "Error: Cannot divide by zero"
    return a / b


# Function 5: Check if a number is even
def is_even(number):
    return number % 2 == 0


# Function 6: Find maximum number from a list
def find_max(numbers):
    return max(numbers)


# Function 7: Count words in a sentence
def word_count(sentence):
    words = sentence.split()
    return len(words)


# Main function to test all functions
def main():
    print("Addition:", add_numbers(10, 5))
    print("Subtraction:", subtract_numbers(10, 5))
    print("Multiplication:", multiply_numbers(10, 5))
    print("Division:", divide_numbers(10, 5))

    print("Is 8 Even?", is_even(8))
    print("Max number:", find_max([3, 7, 2, 9, 5]))
    print("Word Count:", word_count("Python is very easy to learn"))


# Run the program
if __name__ == "__main__":
    main()