import ctypes

levenshtein = ctypes.CDLL("./levenshtein.so")


def levenshtein_distance(a, b):
    return levenshtein.levenshtein_distance(a.encode("utf-8"), b.encode("utf-8"))

print(levenshtein_distance("kitten", "sitting"))  # 3