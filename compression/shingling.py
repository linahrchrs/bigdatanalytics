""" 1. Load files 
    d1 = open("d1.txt", "r+")
    d2 = ...
    either use ram or create file
    2. normlaize document: remove characters you dont need
    3. tokenize: create shingles either by characters(3-7) or by words(3-5)
    4. int to identify shingels=> minhash is much easier (using % operator, a%b , b>|a|, b should be a prime number: 2^N -1)
    5. computer the minhash for each document = elementwise min of each hash (smallest set)
    mainly iterate over 64-256 hash time
    it's bext to compute the jaccard from the min hashes instead of the shingles
"""

import os

def get_shingles(text, k=4):
    """
    Create a set of k-shingles (contiguous sequences of k words) from a text.
    """
    words = text.lower().split()
    shingles = set()
    for i in range(len(words) - k + 1):
        shingle = ' '.join(words[i:i + k])
        shingles.add(shingle)
    return shingles


def jaccard_similarity(shingles1, shingles2):
    """
    Compute the Jaccard similarity between two sets of shingles.
    """
    intersection = len(shingles1 & shingles2)
    union = len(shingles1 | shingles2)
    return intersection / union if union != 0 else 0


def read_file(filename):
    """
    Read text content from a file in the same folder as this script.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, filename)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


if __name__ == "__main__":
    # File names (in the same folder)
    file1 = "d1.txt"
    file2 = "d2.txt"

    # Read documents
    text1 = read_file(file1)
    text2 = read_file(file2)

    # Generate shingles and compute similarity
    k = 4
    shingles1 = get_shingles(text1, k)
    shingles2 = get_shingles(text2, k)

    similarity = jaccard_similarity(shingles1, shingles2)

    print(f"Number of shingles in {file1}: {len(shingles1)}")
    print(f"Number of shingles in {file2}: {len(shingles2)}")
    print(f"Jaccard similarity (k={k}): {similarity:.4f}")
