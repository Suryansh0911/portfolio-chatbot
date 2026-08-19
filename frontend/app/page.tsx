"use client";

import { useChat } from "@ai-sdk/react";
import ReactMarkdown from "react-markdown";
import { useEffect, useRef, useState } from "react";
import type { UIMessage } from "@ai-sdk/react";

// Define our saved chat structure
interface SavedChat {
  id: string;
  title: string;
  messages: UIMessage[];
}

export default function Chat() {
  // We extract setMessages to allow loading past chats into the active view
  const { messages, setMessages, sendMessage, status } = useChat();

  const [input, setInput] = useState("");
  const [savedChats, setSavedChats] = useState<SavedChat[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  
  // New state for file uploads
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isLoading = status === "submitted" || status === "streaming";
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to the latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load chat history from localStorage on initial mount
  useEffect(() => {
    const storedHistory = localStorage.getItem("portfolio_chat_history");
    if (storedHistory) {
      try {
        setSavedChats(JSON.parse(storedHistory));
      } catch (e) {
        console.error("Failed to parse chat history");
      }
    }
  }, []);

  // Save current chat to localStorage whenever messages change
  useEffect(() => {
    if (messages.length === 0) return;

    let chatId = currentChatId;
    if (!chatId) {
      chatId = Date.now().toString();
      setCurrentChatId(chatId);
    }

    // Generate a title based on the first user message
    const firstUserMsg = messages.find((m) => m.role === "user");
    
    let firstUserText = "New Conversation";
    if (firstUserMsg?.parts) {
      const textPart = firstUserMsg.parts.find((p) => p.type === "text");
      if (textPart) {
        firstUserText = textPart.text;
      }
    }

    const title = firstUserText.length > 25 
      ? firstUserText.slice(0, 25) + "..." 
      : firstUserText;

    setSavedChats((prev) => {
      const existingIndex = prev.findIndex((c) => c.id === chatId);
      const updatedChats = [...prev];
      
      if (existingIndex >= 0) {
        updatedChats[existingIndex] = { ...updatedChats[existingIndex], messages, title };
      } else {
        updatedChats.unshift({ id: chatId as string, title, messages }); // Add to top
      }
      
      localStorage.setItem("portfolio_chat_history", JSON.stringify(updatedChats));
      return updatedChats;
    });
  }, [messages, currentChatId]);

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    sendMessage({ text: input });
    setInput("");
  };

  const startNewChat = () => {
    setCurrentChatId(null);
    setMessages([]);
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  const loadChat = (id: string) => {
    const chat = savedChats.find((c) => c.id === id);
    if (chat) {
      setCurrentChatId(chat.id);
      setMessages(chat.messages);
    }
    if (window.innerWidth < 768) setIsSidebarOpen(false);
  };

  // Handle uploading a new resume
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/upload-resume`, {
        method: "POST",
        body: formData,
      });

      if (response.ok) {
        alert("Success! Your resume was parsed and the Vector Store is updated.");
        startNewChat(); // Start a fresh chat so the bot uses the new context
      } else {
        const errorData = await response.json();
        alert(`Failed to update resume: ${errorData.detail || 'Unknown error'}`);
      }
    } catch (error) {
      console.error(error);
      alert("Network error while uploading the resume.");
    } finally {
      setIsUploading(false);
      // Reset the file input so you can upload the same file again if needed
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  return (
    <div className="flex h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 font-sans overflow-hidden">
      
      {/* Sidebar Overlay for Mobile */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden" 
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar / Chat History Panel */}
      <aside 
        className={`absolute md:relative z-30 h-full w-64 bg-zinc-100 dark:bg-zinc-900 border-r border-zinc-200 dark:border-zinc-800 flex flex-col transition-transform duration-300 ease-in-out ${
          isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
      >
        <div className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center justify-between">
          <h2 className="font-semibold tracking-tight">Chat History</h2>
          {/* Mobile Close Button */}
          <button onClick={() => setIsSidebarOpen(false)} className="md:hidden p-1 text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-200">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18"/><path d="m6 6 12 12"/></svg>
          </button>
        </div>

        <div className="p-4 flex flex-col gap-2">
          <button 
            onClick={startNewChat}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 bg-zinc-900 hover:bg-zinc-800 dark:bg-white dark:hover:bg-zinc-200 text-white dark:text-zinc-900 rounded-lg text-sm font-medium transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14"/><path d="M12 5v14"/></svg>
            New Chat
          </button>
        </div>

        {/* Upload Resume Button Section */}
        <div className="px-4 pb-4 border-b border-zinc-200 dark:border-zinc-800">
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload} 
            className="hidden" 
            accept=".pdf,.txt,.docx" 
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="w-full flex items-center justify-center gap-2 py-2 px-4 border border-zinc-300 dark:border-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
          >
            {isUploading ? (
              <span className="animate-pulse">Rebuilding Database...</span>
            ) : (
              <>
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" x2="12" y1="3" y2="15"/></svg>
                Upload New Resume
              </>
            )}
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 pb-4 pt-2 space-y-1">
          {savedChats.length === 0 ? (
            <p className="text-sm text-zinc-500 text-center mt-4">No past chats</p>
          ) : (
            savedChats.map((chat) => (
              <button
                key={chat.id}
                onClick={() => loadChat(chat.id)}
                className={`w-full text-left px-3 py-2.5 rounded-lg text-sm truncate transition-colors ${
                  currentChatId === chat.id 
                    ? "bg-zinc-200/80 dark:bg-zinc-800/80 font-medium" 
                    : "hover:bg-zinc-200/50 dark:hover:bg-zinc-800/50 text-zinc-600 dark:text-zinc-400"
                }`}
              >
                {chat.title}
              </button>
            ))
          )}
        </div>
      </aside>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        
        {/* Header */}
        <header className="p-4 border-b border-zinc-200 dark:border-zinc-800 flex items-center bg-white/80 dark:bg-zinc-950/80 backdrop-blur-md z-10 shrink-0">
          <button 
            onClick={() => setIsSidebarOpen(true)}
            className="md:hidden mr-4 p-2 -ml-2 text-zinc-600 dark:text-zinc-400 hover:bg-zinc-100 dark:hover:bg-zinc-900 rounded-md"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="4" x2="20" y1="12" y2="12"/><line x1="4" x2="20" y1="6" y2="6"/><line x1="4" x2="20" y1="18" y2="18"/></svg>
          </button>
          <h1 className="text-lg font-semibold tracking-tight">AI Portfolio</h1>
        </header>

        {/* Chat Messages */}
        <main className="flex-1 overflow-y-auto p-4 md:p-8">
          <div className="max-w-3xl mx-auto space-y-6 pb-24">

            {/* Empty State */}
            {messages.length === 0 && (
              <div className="text-center text-zinc-500 mt-20">
                <p className="text-xl font-medium mb-2">
                  Hi, I'm the AI portfolio assistant.
                </p>
                <p>
                  Ask me about my experience, skills, or projects.
                </p>
              </div>
            )}

            {/* Message Bubbles */}
            {messages.map((message) => {
              const isUser = message.role === "user";

              return (
                <div
                  key={message.id}
                  className={`flex w-full ${isUser ? "justify-end" : "justify-start"}`}
                >
                  <div 
                    className={`flex flex-col space-y-1 max-w-[85%] md:max-w-[75%] ${isUser ? "items-end" : "items-start"}`}
                  >
                    <span className="text-xs text-zinc-500 font-medium px-1">
                      {isUser ? "You" : "AI Assistant"}
                    </span>
                    
                    <div 
                      className={`p-4 rounded-2xl ${
                        isUser 
                          ? "bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-tr-sm" 
                          : "bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-900 dark:text-zinc-100 rounded-tl-sm shadow-sm"
                      }`}
                    >
                      {/* Markdown rendering logic adapted for bubbles */}
                      <div className={`max-w-none leading-relaxed ${isUser ? "whitespace-pre-wrap" : "prose prose-zinc dark:prose-invert prose-sm md:prose-base"}`}>
                        {message.parts?.map((part, index) => {
                          if (part.type !== "text") return null;
                          if (isUser) {
                            return <span key={index}>{part.text}</span>;
                          }
                          return <ReactMarkdown key={index}>{part.text}</ReactMarkdown>;
                        })}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex w-full justify-start">
                <div className="flex flex-col space-y-1 items-start">
                  <span className="text-xs text-zinc-500 font-medium px-1">AI Assistant</span>
                  <div className="bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 p-4 rounded-2xl rounded-tl-sm shadow-sm">
                    <div className="flex gap-1 items-center h-5">
                      <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-zinc-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Scroll Target */}
            <div ref={messagesEndRef} />
          </div>
        </main>

        {/* Input Area */}
        <div className="shrink-0 p-4 bg-white dark:bg-zinc-950 border-t border-zinc-200 dark:border-zinc-800">
          <div className="max-w-3xl mx-auto">
            <form
              onSubmit={handleSubmit}
              className="relative flex items-center bg-zinc-50 dark:bg-zinc-900 border border-zinc-300 dark:border-zinc-700 rounded-full shadow-sm focus-within:ring-2 focus-within:ring-zinc-900 dark:focus-within:ring-zinc-100 overflow-hidden transition-all"
            >
              <input
                type="text"
                className="flex-1 bg-transparent py-3.5 pl-5 pr-12 outline-none placeholder:text-zinc-500 dark:placeholder:text-zinc-400 text-sm md:text-base"
                value={input}
                placeholder="Ask about my resume..."
                onChange={(e) => setInput(e.target.value)}
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !input.trim()}
                className="absolute right-1.5 p-2 bg-zinc-900 dark:bg-zinc-100 text-white dark:text-zinc-900 rounded-full hover:opacity-80 transition-opacity disabled:opacity-50"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/></svg>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}