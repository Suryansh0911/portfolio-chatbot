import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

export const maxDuration = 60;

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
        // Use the Vercel rewrite proxy we set up, falling back to local if developing locally
        const targetUrl = process.env.NODE_ENV === 'production' 
          ? '/api-backend/chat' 
          : `${process.env.RAG_BACKEND_URL || "http://127.0.0.1:8000"}/chat`;

        const response = await fetch(
          targetUrl,
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

        const data = await response.json();
        // Extract the answer text from your FastAPI JSON response
        const answerText = data.answer || JSON.stringify(data);

        const textId = `rag-${Date.now()}`;

        writer.write({
          type: "text-start",
          id: textId,
        });

        writer.write({
          type: "text-delta",
          id: textId,
          delta: answerText,
        });

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