import os

# Unit tests that don't hit the OpenAI API still instantiate ChatOpenAI /
# OpenAIEmbeddings clients (constructor only checks a key is present, not
# that it's valid) — set a dummy key so import-time construction doesn't
# warn or fail when a real backend/.env isn't present in CI.
os.environ.setdefault("OPENAI_API_KEY", "sk-test-dummy-key-for-unit-tests")
