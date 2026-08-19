import re

class ThinkStreamFilter:

    def __init__(self):
        self.buffer = ""
        self.in_think = False

    def feed(self, chunk: str) -> str:

        self.buffer += chunk
        output = ""

        while self.buffer:

            if self.in_think:

                end = self.buffer.lower().find(
                    "</think>"
                )

                if end == -1:
                    self.buffer = ""
                    break

                self.buffer = self.buffer[
                    end + len("</think>"):
                ]

                self.in_think = False

                continue

            start = self.buffer.lower().find(
                "<think>"
            )

            if start == -1:
                safe_length = max(
                    0,
                    len(self.buffer) - 7
                )

                output += self.buffer[
                    :safe_length
                ]

                self.buffer = self.buffer[
                    safe_length:
                ]

                break

            output += self.buffer[:start]

            self.buffer = self.buffer[
                start + len("<think>"):
            ]

            self.in_think = True

        return output

    def flush(self) -> str:

        if self.in_think:
            return ""

        remaining = self.buffer

        self.buffer = ""

        return remaining

def clean_model_output(text: str) -> str:
    """
    Remove exposed model reasoning and common formatting artifacts.
    """

    if not text:
        return ""

    text = re.sub(
        r"<think>.*?</think>",
        "",
        text,
        flags=re.DOTALL | re.IGNORECASE
    ).strip()

    # Remove accidental fenced JSON/text blocks when present.
    text = re.sub(
        r"^```(?:json|text)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def clean_stream_text(text: str) -> str:
    """
    Best-effort cleanup for individual streamed chunks.

    Do NOT rely on this alone for <think> removal because
    tags can be split across chunks. The streaming wrapper
    below handles that case.
    """

    return clean_model_output(text)