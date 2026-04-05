def validate_words_for_game(game, submitted_words):
    if not isinstance(submitted_words, list):
        return {"valid": False, "error": "Submitted words must be a list."}

    normalized = [w.lower().strip() for w in submitted_words]

    if len(normalized) != len(set(normalized)):
        return {"valid": False, "error": "Duplicate words submitted."}

    legal_words = set(game.possible_words)
    invalid = [w for w in normalized if w not in legal_words]

    if invalid:
        return {"valid": False, "invalid_words": invalid}

    return {"valid": True}
