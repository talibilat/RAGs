'use client';

import { useState, useEffect, useRef } from 'react';
import Image from 'next/image';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface Reference {
  page_url: string;
  page_title: string;
}

interface Message {
  id: string;
  type: 'user' | 'agent';
  text: string;
  references?: Reference[];
  scores?: {
    factual_accuracy: number;
    relevance: number;
    completeness: number;
    context_usage: number;
  };
}

interface LoadingState {
  stage: 'understanding' | 'searching' | 'generating' | null;
  dots: number;
}

export default function ChatPage() {
  const [question, setQuestion] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingState, setLoadingState] = useState<LoadingState>({ stage: null, dots: 0 });
  const [messages, setMessages] = useState<Message[]>([]);
  const [showReferences, setShowReferences] = useState<{[key: string]: boolean}>({});
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Loading animation effect
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (loading) {
      let stageIndex = 0;
      const stages: ('understanding' | 'searching' | 'generating')[] = ['understanding', 'searching', 'generating'];
      
      interval = setInterval(() => {
        setLoadingState(prev => {
          const newDots = (prev.dots + 1) % 4;
          if (newDots === 0) {
            stageIndex = (stageIndex + 1) % stages.length;
          }
          return {
            stage: stages[stageIndex],
            dots: newDots
          };
        });
      }, 500);
    } else {
      setLoadingState({ stage: null, dots: 0 });
    }

    return () => clearInterval(interval);
  }, [loading]);

  const getConfidenceColor = (score: number) => {
    if (score > 8) return 'bg-green-100 text-green-800';
    if (score < 5) return 'bg-red-100 text-red-800';
    return 'bg-yellow-100 text-yellow-800';
  };

  const getLoadingMessage = () => {
    if (!loadingState.stage) return '';
    const dots = '.'.repeat(loadingState.dots);
    const messages = {
      understanding: 'Understanding your query',
      searching: 'Searching through knowledge base',
      generating: 'Generating helpful response'
    };
    return `${messages[loadingState.stage]}${dots}`;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;

    // Add user message
    const userMessageId = Date.now().toString();
    const userMessage: Message = {
      id: userMessageId,
      type: 'user',
      text: question
    };
    setMessages(prev => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      
      if (!res.ok) throw new Error('Failed to get response');
      
      const data = await res.json();
      
      // Add agent message with empathetic prefix
      const agentMessageId = (Date.now() + 1).toString();
      const questionTopic = question.toLowerCase().split(' ').slice(0, 3).join(' ');
      const agentMessage: Message = {
        id: agentMessageId,
        type: 'agent',
        text: `${questionTopic}. Here's what I found:\n\n${data.answer}`,
        references: data.references,
        scores: data.scores
      };
      setMessages(prev => [...prev, agentMessage]);
      setShowReferences(prev => ({ ...prev, [agentMessageId]: false }));
    } catch (error) {
      console.error('Error:', error);
      // Add error message
      setMessages(prev => [...prev, {
        id: (Date.now() + 1).toString(),
        type: 'agent',
        text: "I apologize, but I encountered an error while processing your request. Please try asking your question again."
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="flex flex-col h-screen bg-gray-50">
      <div className="flex justify-between items-center p-4 bg-white shadow-sm">
        <Image src="/voy-logo.svg" alt="Voy Logo" width={100} height={40} />
        <button className="text-[#39225F] font-medium">Sign in</button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'} gap-4`}
          >
            {message.type === 'agent' && (
              <div className="w-8 h-8 rounded-full bg-[#39225F] flex items-center justify-center text-white text-sm">
                VA
              </div>
            )}
            
            <div className={`max-w-[70%] ${message.type === 'user' ? 'bg-[#39225F] text-white' : 'bg-white'} rounded-lg shadow-sm p-4`}>
              <div className={`prose prose-sm max-w-none ${message.type === 'user' ? 'text-white' : 'text-gray-800'}`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.text}
                </ReactMarkdown>
              </div>
              
              {message.type === 'agent' && message.scores && (
                <div className="mt-3 space-y-2 border-t border-gray-100 pt-3">
                  <p className="text-sm font-medium text-gray-700">Evaluation Scores:</p>
                  <div className="grid grid-cols-2 gap-2">
                    {Object.entries(message.scores).map(([key, score]) => (
                      <div key={key} className="text-sm">
                        <span className="capitalize">{key.replace(/_/g, ' ')}: </span>
                        <span className={`inline-block px-2 py-0.5 rounded-full text-xs ${getConfidenceColor(score)}`}>
                          {score.toFixed(1)}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {message.type === 'agent' && message.references && message.references.length > 0 && (
                <div className="mt-3 border-t border-gray-100 pt-3">
                  <button
                    onClick={() => setShowReferences(prev => ({ 
                      ...prev, 
                      [message.id]: !prev[message.id] 
                    }))}
                    className="text-[#39225F] text-sm font-medium hover:underline focus:outline-none"
                  >
                    {showReferences[message.id] ? 'Hide References' : 'Show References'}
                  </button>
                  
                  {showReferences[message.id] && (
                    <div className="mt-2 space-y-1">
                      {message.references.map((ref, index) => (
                        <a
                          key={index}
                          href={ref.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="block text-sm text-gray-600 hover:text-[#39225F] hover:underline"
                        >
                          {ref.page_title}
                        </a>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {message.type === 'user' && (
              <div className="w-8 h-8 rounded-full bg-gray-200 flex items-center justify-center text-gray-600 text-sm">
                U
              </div>
            )}
          </div>
        ))}
        
        {loading && (
          <div className="flex justify-start gap-4">
            <div className="w-8 h-8 rounded-full bg-[#39225F] flex items-center justify-center text-white text-sm">
              VA
            </div>
            <div className="bg-white rounded-lg shadow-sm p-4">
              <p className="text-gray-600 text-sm">{getLoadingMessage()}</p>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      <div className="p-4 bg-white border-t">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Type your question..."
            className="flex-1 p-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-[#39225F]"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-[#39225F] text-white px-6 rounded-lg hover:bg-[#2D1A4F] transition-colors disabled:opacity-50"
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </div>
    </main>
  );
}
