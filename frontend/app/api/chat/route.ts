import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

export const maxDuration = 60;

const BACKEND_URL =
  process.env.RAG_BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();

    const messages = body.messages ?? [];

    if (!messages.length) {
      return new Response("No messages provided", {
        status: 400,
      });
    }

    // Get the latest user message
    const lastMessage = messages[messages.length - 1];

    const userText = (lastMessage.parts ?? [])
      .filter((part: any) => part.type === "text")
      .map((part: any) => part.text)
      .join("");

    if (!userText.trim()) {
      return new Response("Empty message", {
        status: 400,
      });
    }

    const conversationId =
      body.conversationId ?? "portfolio-web";

    const stream = createUIMessageStream({
      async execute({ writer }) {
        const response = await fetch(
          `${BACKEND_URL}/chat/stream`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              message: userText,
              conversation_id: conversationId,
            }),
          }
        );

        if (!response.ok) {
          const errorText = await response.text();

          throw new Error(
            `FastAPI returned ${response.status}: ${errorText}`
          );
        }

        if (!response.body) {
          throw new Error(
            "FastAPI returned an empty response body."
          );
        }

        const textId = `rag-${Date.now()}`;

        writer.write({
          type: "text-start",
          id: textId,
        });

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
          while (true) {
            const { done, value } = await reader.read();

            if (done) {
              break;
            }

            const chunk = decoder.decode(value, {
              stream: true,
            });

            if (!chunk) {
              continue;
            }

            writer.write({
              type: "text-delta",
              id: textId,
              delta: chunk,
            });
          }
          const finalChunk = decoder.decode();

          if (finalChunk) {
            writer.write({
              type: "text-delta",
              id: textId,
              delta: finalChunk,
            });
          }
        } finally {
          reader.releaseLock();
        }

        writer.write({
          type: "text-end",
          id: textId,
        });
      },

      onError(error) {
        console.error("RAG backend error:", error);

        return "Sorry, something went wrong while processing your request.";
      },
    });

    return createUIMessageStreamResponse({
      stream,
    });
  } catch (error) {
    console.error("Chat route error:", error);

    return new Response(
      JSON.stringify({
        error: "Failed to process chat request.",
      }),
      {
        status: 500,
        headers: {
          "Content-Type": "application/json",
        },
      }
    );
  }
}