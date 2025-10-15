import re
import hashlib
import numpy as np
from collections import defaultdict
from typing import Set, List, Dict, Tuple
import random


def create_character_shingles(text: str, k: int) -> Set[str]:
    """Create k-character shingles from text."""
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    shingles = set()
    for i in range(len(text) - k + 1):
        shingle = text[i:i + k]
        shingles.add(shingle)
    return shingles


def jaccard_similarity(set1: Set, set2: Set) -> float:
    """Calculate Jaccard similarity between two sets."""
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    if union == 0:
        return 0.0
    return intersection / union


def create_hash_functions(num_hashes: int, max_value: int = 2**32 - 1) -> List[Tuple[int, int, int]]:
    """Create hash function parameters."""
    p = 2**31 - 1  # Mersenne prime
    hash_funcs = []
    for _ in range(num_hashes):
        a = random.randint(1, p - 1)
        b = random.randint(0, p - 1)
        hash_funcs.append((a, b, p))
    return hash_funcs


def compute_minhash_signature(shingles: Set[str], hash_functions: List[Tuple[int, int, int]]) -> List[int]:
    """Compute minhash signature for a set of shingles."""
    signature = []
    for a, b, p in hash_functions:
        min_hash = float('inf')
        for shingle in shingles:
            shingle_hash = int(hashlib.md5(shingle.encode()).hexdigest(), 16)
            hash_value = (a * shingle_hash + b) % p
            min_hash = min(min_hash, hash_value)
        signature.append(min_hash)
    return signature


def estimate_jaccard_from_signatures(sig1: List[int], sig2: List[int]) -> float:
    """Estimate Jaccard similarity from minhash signatures."""
    if len(sig1) != len(sig2):
        raise ValueError("Signatures must have same length")
    matches = sum(1 for i in range(len(sig1)) if sig1[i] == sig2[i])
    return matches / len(sig1)


class LSH:
    """Locality-Sensitive Hashing for minhash signatures."""
    
    def __init__(self, num_bands: int, rows_per_band: int):
        self.num_bands = num_bands
        self.rows_per_band = rows_per_band
        self.signature_length = num_bands * rows_per_band
        self.hash_tables = [defaultdict(list) for _ in range(num_bands)]
    
    def hash_band(self, band_values: List[int]) -> int:
        """Hash a band to a bucket."""
        return hash(tuple(band_values))
    
    def add_signature(self, doc_id: int, signature: List[int]) -> None:
        """Add a document signature to the LSH structure."""
        if len(signature) != self.signature_length:
            raise ValueError(f"Signature length must be {self.signature_length}")
        
        for band_idx in range(self.num_bands):
            start = band_idx * self.rows_per_band
            end = start + self.rows_per_band
            band = signature[start:end]
            bucket_id = self.hash_band(band)
            self.hash_tables[band_idx][bucket_id].append(doc_id)
    
    def find_candidates(self) -> Set[Tuple[int, int]]:
        """Find all candidate pairs."""
        candidates = set()
        for hash_table in self.hash_tables:
            for bucket in hash_table.values():
                if len(bucket) > 1:
                    for i in range(len(bucket)):
                        for j in range(i + 1, len(bucket)):
                            pair = tuple(sorted([bucket[i], bucket[j]]))
                            candidates.add(pair)
        return candidates


class PlagiarismDetector:
    """Complete plagiarism detection system."""
    
    def __init__(self, k: int = 5, num_hashes: int = 100, num_bands: int = 20, threshold: float = 0.3):
        self.k = k
        self.num_hashes = num_hashes
        self.num_bands = num_bands
        self.rows_per_band = num_hashes // num_bands
        self.threshold = threshold
        
        random.seed(42)
        self.hash_funcs = create_hash_functions(num_hashes)
        
        self.documents = []
        self.filenames = []
        self.shingle_sets = []
        self.signatures = []
        self.lsh = LSH(num_bands, self.rows_per_band)
    
    def add_document(self, text: str, filename: str) -> int:
        """Add a document to the system."""
        doc_id = len(self.documents)
        self.documents.append(text)
        self.filenames.append(filename)
        
        shingles = create_character_shingles(text, self.k)
        self.shingle_sets.append(shingles)
        
        signature = compute_minhash_signature(shingles, self.hash_funcs)
        self.signatures.append(signature)
        
        self.lsh.add_signature(doc_id, signature)
        
        return doc_id
    
    def find_plagiarism(self) -> List[Tuple[int, int, float]]:
        """Find all plagiarized pairs above threshold."""
        candidates = self.lsh.find_candidates()
        results = []
        
        for doc1, doc2 in candidates:
            similarity = estimate_jaccard_from_signatures(
                self.signatures[doc1],
                self.signatures[doc2]
            )
            
            if similarity >= self.threshold:
                results.append((doc1, doc2, similarity))
        
        return sorted(results, key=lambda x: x[2], reverse=True)
    
    def get_highlighted_sections(self, doc1_id: int, doc2_id: int, window_size: int = 100) -> List[Dict]:
        """Get highlighted matching sections between two documents."""
        text1 = self.documents[doc1_id]
        text2 = self.documents[doc2_id]
        shingles1 = self.shingle_sets[doc1_id]
        shingles2 = self.shingle_sets[doc2_id]
        
        common_shingles = shingles1.intersection(shingles2)
        
        matches = []
        
        # Find positions of common shingles in both documents
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        for shingle in list(common_shingles)[:10]:  # Limit to top 10 for performance
            pos1 = text1_lower.find(shingle)
            pos2 = text2_lower.find(shingle)
            
            if pos1 != -1 and pos2 != -1:
                start1 = max(0, pos1 - window_size // 2)
                end1 = min(len(text1), pos1 + len(shingle) + window_size // 2)
                
                start2 = max(0, pos2 - window_size // 2)
                end2 = min(len(text2), pos2 + len(shingle) + window_size // 2)
                
                matches.append({
                    'text1': text1[start1:end1],
                    'text2': text2[start2:end2],
                    'position1': pos1,
                    'position2': pos2
                })
        
        return matches
    
    def generate_report(self) -> Dict:
        """Generate comprehensive plagiarism report."""
        plagiarism_cases = self.find_plagiarism()
        
        report = {
            'total_documents': len(self.documents),
            'total_comparisons': len(self.documents) * (len(self.documents) - 1) // 2,
            'candidates_checked': len(self.lsh.find_candidates()),
            'plagiarism_cases': []
        }
        
        for doc1, doc2, similarity in plagiarism_cases:
            # Calculate actual Jaccard similarity for more precision
            actual_sim = jaccard_similarity(self.shingle_sets[doc1], self.shingle_sets[doc2])
            
            case = {
                'document1': self.filenames[doc1],
                'document2': self.filenames[doc2],
                'similarity': round(similarity * 100, 2),
                'actual_similarity': round(actual_sim * 100, 2),
                'severity': self._get_severity(similarity),
                'matched_sections': self.get_highlighted_sections(doc1, doc2)
            }
            report['plagiarism_cases'].append(case)
        
        return report
    
    def _get_severity(self, similarity: float) -> str:
        """Determine severity level based on similarity score."""
        if similarity >= 0.8:
            return "Critical"
        elif similarity >= 0.6:
            return "High"
        elif similarity >= 0.4:
            return "Medium"
        else:
            return "Low"
    
    def get_statistics(self) -> Dict:
        """Get detection statistics."""
        candidates = len(self.lsh.find_candidates())
        total_pairs = len(self.documents) * (len(self.documents) - 1) // 2
        
        return {
            'num_documents': len(self.documents),
            'total_pairs': total_pairs,
            'candidate_pairs': candidates,
            'reduction_factor': total_pairs / candidates if candidates > 0 else 0,
            'parameters': {
                'k': self.k,
                'num_hashes': self.num_hashes,
                'num_bands': self.num_bands,
                'threshold': self.threshold
            }
        }