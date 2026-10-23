"""Node 3: generate.

Three ways to produce text:
  mock   : fake, deterministic, no network (the default)
  hf     : Hugging Face router (OpenAI-compatible), needs HF_TOKEN
  ollama : a model running on your own machine

Each generator is one plain function. generate() picks one by name.
"""

import hashlib
import json
import os
import urllib.error
import urllib.request
from typing import Dict, Optional

HF_URL = "https://router.huggingface.co/v1/chat/completions"
# Which models are free can change. Check the Hugging Face site if this fails.
DEFAULT_HF_MODEL = "meta-llama/Llama-3.2-3B-Instruct"

OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_OLLAMA_MODEL = "llama3.2"

TIMEOUT_SECONDS = 60

GENERATOR_NAMES = ["mock", "hf", "ollama"]


class GeneratorError(Exception):
    """Raised with a friendly message when a generator cannot produce text."""


# ---------------------------------------------------------------- mock

# Canned phrases. The mock picks from these using a hash of the prompt.
MOCK_OPENERS = [
    "Presenting",
    "A clean studio shot of",
    "Meet",
    "Image of",
    "Oops, here is",
    "Soft light on",
]
MOCK_CLOSERS = [
    ".",
    ", ready for your next project.",
    ". Please try again.",
    ", shown with calm colours and gentle contrast, in a style that feels warm.",
    ", 24 hours a day.",
    ".",
]


def prompt_to_number(prompt: str) -> int:
    """Turn a prompt into a stable number.

    Python's built-in hash() changes between runs, so we use sha256 instead.
    The same prompt always gives the same number.
    """
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return int(digest[:8], 16)


def mock_generate(prompt: str, variables: Dict[str, str]) -> str:
    """Build fake output from the prompt: a canned opener, the key
    variables, and a canned closer. Deterministic, so reports are stable."""
    n = prompt_to_number(prompt)
    opener = MOCK_OPENERS[n % len(MOCK_OPENERS)]
    closer = MOCK_CLOSERS[(n // 7) % len(MOCK_CLOSERS)]

    values = []
    for name in sorted(variables.keys()):
        values.append(str(variables[name]))
    body = ", ".join(values)
    return opener + " " + body + closer


# ---------------------------------------------------------------- hf

def check_hf_token() -> str:
    """Return the token from the environment or raise a friendly error."""
    token = os.environ.get("HF_TOKEN", "")
    if token == "":
        raise GeneratorError(
            "HF_TOKEN is not set. Create a free token at "
            "https://huggingface.co/settings/tokens and run: "
            "export HF_TOKEN=your_token_here"
        )
    return token


def post_json(url: str, payload: Dict, headers: Dict[str, str]) -> Dict:
    """Send a JSON POST with urllib and return the decoded JSON reply."""
    body = json.dumps(payload).encode("utf-8")
    all_headers = {"Content-Type": "application/json"}
    all_headers.update(headers)
    request = urllib.request.Request(url, data=body, headers=all_headers, method="POST")
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return json.loads(response.read().decode("utf-8"))


def hf_generate(prompt: str, model: Optional[str]) -> str:
    token = check_hf_token()
    model_name = model or DEFAULT_HF_MODEL
    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 200,
    }
    headers = {"Authorization": "Bearer " + token}
    try:
        reply = post_json(HF_URL, payload, headers)
        return reply["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as error:
        raise GeneratorError(
            "Hugging Face returned HTTP " + str(error.code) + " for model '"
            + model_name + "'. The model may be unavailable or your token "
            "may lack access."
        )
    except urllib.error.URLError as error:
        raise GeneratorError("Could not reach Hugging Face: " + str(error.reason))
    except (KeyError, IndexError, ValueError):
        raise GeneratorError("Hugging Face sent a reply in an unexpected format.")
    except OSError as error:
        # Covers timeouts.
        raise GeneratorError("Hugging Face request failed: " + str(error))


# ---------------------------------------------------------------- ollama

def ollama_generate(prompt: str, model: Optional[str]) -> str:
    model_name = model or DEFAULT_OLLAMA_MODEL
    payload = {"model": model_name, "prompt": prompt, "stream": False}
    try:
        reply = post_json(OLLAMA_URL, payload, {})
        return reply["response"].strip()
    except urllib.error.HTTPError as error:
        raise GeneratorError(
            "Ollama returned HTTP " + str(error.code) + ". Is the model '"
            + model_name + "' installed? Try: ollama pull " + model_name
        )
    except urllib.error.URLError:
        raise GeneratorError(
            "Could not reach Ollama at localhost:11434. "
            "Install it from https://ollama.com and start it with: ollama serve"
        )
    except (KeyError, ValueError):
        raise GeneratorError("Ollama sent a reply in an unexpected format.")
    except OSError as error:
        raise GeneratorError("Ollama request failed: " + str(error))


# ---------------------------------------------------------------- entry points

def check_ready(name: str) -> None:
    """Fail fast (before any prompts run) if a generator cannot work."""
    if name not in GENERATOR_NAMES:
        raise GeneratorError(
            "Unknown generator '" + name + "'. Choose from: " + ", ".join(GENERATOR_NAMES)
        )
    if name == "hf":
        check_hf_token()


def generate(name: str, prompt: str, variables: Dict[str, str], model: Optional[str]) -> str:
    """Run the generator called `name` and return its text."""
    check_ready(name)
    if name == "mock":
        return mock_generate(prompt, variables)
    if name == "hf":
        return hf_generate(prompt, model)
    return ollama_generate(prompt, model)


def model_label(name: str, model: Optional[str]) -> str:
    """The model name to show in reports."""
    if name == "mock":
        return "mock (fake, no model)"
    if name == "hf":
        return model or DEFAULT_HF_MODEL
    return model or DEFAULT_OLLAMA_MODEL
