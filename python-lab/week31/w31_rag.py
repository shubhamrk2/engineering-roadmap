"""Week 31: embeddings and RAG, by hand.

Replace each `raise NotImplementedError` with your own code (embed, FakeLLM, count_words and the constants are supplied).
Run:  pytest week31

No network, no model, no GPU: embed() is a toy hashed bag-of-words so the tests are stable.
Toy embeddings match WORDS, not meaning. That is a feature here (tests are deterministic) and a limit in real life.
"""
import math
import re
import zlib

REFUSAL_MESSAGE = "I do not know based on the provided documents."
DIM = 64


def embed(text, dim=DIM):
    """SUPPLIED. Deterministic toy embedding: hashed bag of words, L2-normalised. Returns a list of floats.

    Same text -> same vector, always (crc32, not Python's salted hash()). Text with no words -> all zeros.
    """
    vec = [0.0] * dim
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        vec[zlib.crc32(word.encode()) % dim] += 1.0
    norm = math.sqrt(sum(x * x for x in vec))
    return [x / norm for x in vec] if norm else vec


class FakeLLM:
    """SUPPLIED. A stand-in for a model. complete(prompt) returns the canned reply and records the prompt."""

    def __init__(self, reply):
        self.reply = reply
        self.prompts = []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return self.reply


def count_words(text):
    """SUPPLIED. Default 'token counter': one token per whitespace-separated word (a crude stand-in)."""
    return len(text.split())


def cosine(a, b):
    """ex01. Cosine similarity of two equal-length lists of numbers: dot(a, b) / (|a| * |b|).

    Return 0.0 if either vector is all zeros. Raise ValueError if the lengths differ.
    Plain Python only: no numpy.
    """
    raise NotImplementedError


def chunk_text(text, size, overlap=0):
    """ex02. Split text into fixed-size character windows that overlap.

    Window i starts at i * (size - overlap) and holds at most `size` characters. The last window ends
    exactly at the end of the text, and no extra window is produced once a window has reached the end
    (so there is never a chunk that is only overlap). Empty text -> [].
    Raise ValueError unless size > 0 and 0 <= overlap < size.
    Example: chunk_text("abcdefghij", 4, 1) -> ["abcd", "defg", "ghij"]
    """
    raise NotImplementedError


def chunk_by_headings(markdown, source):
    """ex03. Split markdown at heading lines (a line starting with one or more '#' then a space).

    Return a list of dicts {"id", "source", "heading", "text"}, one per section that has non-empty body text:
      heading  the heading text without the '#' marks, stripped ("" for text before the first heading)
      text     the body lines joined with "\\n" and stripped (the heading line itself is not part of it)
      source   the `source` argument
      id       f"{source}#{n}" where n counts the EMITTED chunks from 0
    Sections whose body is empty are skipped and do not use up a number.
    """
    raise NotImplementedError


def top_k(query_vec, vectors, k):
    """ex04. Brute-force nearest neighbours by cosine similarity.

    Return a list of (index, score) for the k best rows of `vectors`, best first. Ties are broken by the
    lower index. If k exceeds the number of vectors, return them all. k <= 0 -> [].
    """
    raise NotImplementedError


def reciprocal_rank_fusion(rankings, k=60):
    """ex05. Fuse several ranked lists of ids into one.

    score(id) = sum over every ranking that contains id of 1 / (k + rank), where rank starts at 1.
    Return [(id, score), ...] sorted by score descending; ties are broken by id ascending.
    An id missing from a ranking simply gets nothing from it. No rankings -> [].
    """
    raise NotImplementedError


def build_context(chunks, max_tokens, count_tokens=count_words):
    """ex06. Pack chunks (already ordered best first) into a context string within a token budget.

    Each chunk is a dict with "id" and "text". Its entry is f"[{id}] {text}". Add entries in order while the
    running total of count_tokens(entry) stays <= max_tokens; STOP at the first entry that does not fit
    (never skip it to squeeze in a lower-ranked one). Entries are joined with "\\n\\n".
    Return (context_string, used_chunks) where used_chunks is the list of chunk dicts that made it in.
    max_tokens too small for even the first entry -> ("", []).
    """
    raise NotImplementedError


def answer_with_citations(question, chunks, llm):
    """ex07. Ask the model a grounded question and report which chunk ids its answer cites.

    Build a prompt that contains: the instruction line
        "Answer using ONLY the sources below and cite them like [id]."
    and the line
        "If the sources do not contain the answer, say: I do not know."
    then each chunk as f"[{id}] {text}" (one per line), then f"Question: {question}".
    Call llm.complete(prompt). Citations are every [something] in the answer, de-duplicated, in order of
    first appearance.  Return {"answer": str, "citations": [ids], "prompt": prompt}.
    """
    raise NotImplementedError


def verify_citations(citations, chunks):
    """ex08. Check that every cited id was actually among the chunks given to the model.

    Return (valid, invalid): two lists, each keeping the order of `citations`. An empty citation list
    gives ([], []). (A model that cites an id it was never shown is fabricating a source.)
    """
    raise NotImplementedError


def refuse_if_low_similarity(scored, threshold):
    """ex09. Decide whether to refuse before calling the model.

    `scored` is a list of (chunk_id, similarity) pairs in any order. Return REFUSAL_MESSAGE if the list is
    empty or its best similarity is strictly below `threshold`; otherwise return None (go ahead and answer).
    A best score exactly equal to the threshold is NOT refused.
    """
    raise NotImplementedError


def recall_at_k(results, expected, k):
    """ex10. Fraction of queries whose expected id appears in the first k results.

    results[i] is the ranked list of ids returned for query i; expected[i] is the one id that should be there.
    Raise ValueError if the two lists differ in length. No queries -> 0.0.
    """
    raise NotImplementedError


def mrr(results, expected):
    """ex11. Mean reciprocal rank: average of 1/rank of the expected id (rank from 1), or 0 if it is absent.

    Raise ValueError if the lists differ in length. No queries -> 0.0.
    """
    raise NotImplementedError
