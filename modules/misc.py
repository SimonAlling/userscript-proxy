# mitm[dump|proxy] cannot have hyphens in option keys.
def sanitize(optionName: str) -> str:
    return optionName.replace("-", "_")
