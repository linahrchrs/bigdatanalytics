import os
import argparse
import hashlib
import random

def get_shingles(text, k=4):
    """Create a list of k-shingles (4-word chunks)."""
    words = text.lower().split()
    return [' '.join(words[i:i + k]) for i in range(len(words) - k + 1)]

def hash_shingle(shingle):
    """Return a 32-bit hash for a shingle."""
    return int(hashlib.md5(shingle.encode('utf-8')).hexdigest(), 16) % (2**32)

def generate_minhash_signature(shingles, num_hashes=100):
    """
    Compute a MinHash signature for a document.
    Each hash function is simulated by (a*x + b) % c.
    """
    max_hash = 2**32 - 1
    coeff_a = random.sample(range(1, max_hash), num_hashes)
    coeff_b = random.sample(range(0, max_hash), num_hashes)

    # Hash all shingles once
    shingle_hashes = [hash_shingle(s) for s in shingles]
    signature = []

    for i in range(num_hashes):
        min_hash = min(((a * x + b) % max_hash) for x in shingle_hashes)
        signature.append(min_hash)
    return signature

def read_file(filepath):
    """Read file contents."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def compress_file(filepath, k=4, num_hashes=100):
    """Compress a text file using MinHash."""
    text = read_file(filepath)
    shingles = get_shingles(text, k)
    signature = generate_minhash_signature(shingles, num_hashes)
    return signature

def main():
    parser = argparse.ArgumentParser(description="Compress text file(s) using MinHashing.")
    parser.add_argument("files", nargs="+", help="Path(s) to text file(s) to compress.")
    parser.add_argument("--k", type=int, default=4, help="Shingle size (default=4).")
    parser.add_argument("--num_hashes", type=int, default=100, help="Number of hash functions (default=100).")
    args = parser.parse_args()

    for file in args.files:
        print(f"\nProcessing: {file}")
        try:
            signature = compress_file(file, args.k, args.num_hashes)
            print(f"✔ Compressed signature ({len(signature)} values):")
            print(signature[:20], "...")  # print first 20 values
        except FileNotFoundError as e:
            print(f"⚠ {e}")

if __name__ == "__main__":
    main()
