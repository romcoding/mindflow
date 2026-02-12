/**
 * AIChatWidget - OpenClaw AI Assistant
 * A floating chat widget that provides conversational AI for MindFlow.
 * Supports creating/editing tasks, stakeholders, notes, and generating insights.
 */
import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  MessageCircle, X, Send, Bot, User, Loader2, Sparkles, 
  ChevronDown, Trash2, Mic, MicOff, Minimize2, Maximize2,
  CheckSquare, Users, StickyNote, BarChart3, Zap
} from 'lucide-react';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { aiAPI } from '../lib/api';
import ReactMarkdown from 'react-markdown';

// Quick action suggestions
const QUICK_ACTIONS = [
  { icon: CheckSquare, label: 'Create a task', prompt: 'Create a new task: ' },
  { icon: Users, label: 'Add a contact', prompt: 'Add a new stakeholder: ' },
  { icon: StickyNote, label: 'Save a note', prompt: 'Save a note: ' },
  { icon: BarChart3, label: 'Show insights', prompt: 'Give me insights about my productivity' },
  { icon: Zap, label: 'Weekly review', prompt: 'Give me a weekly review of my tasks and progress' },
];

const AIChatWidget = ({ onDataChange }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: "Hey! I'm **OpenClaw**, your MindFlow AI assistant. 🧠\n\nI can help you:\n- **Create & manage tasks** — just tell me what needs doing\n- **Add contacts** — describe a person and I'll save them\n- **Take notes** — capture thoughts instantly\n- **Generate insights** — ask about your productivity\n\nHow can I help you today?",
      timestamp: new Date()
    }
  ]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [showQuickActions, setShowQuickActions] = useState(true);
  const [unreadCount, setUnreadCount] = useState(0);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Focus input when opened
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 300);
      setUnreadCount(0);
    }
  }, [isOpen]);

  // Send message to AI
  const sendMessage = async (text) => {
    if (!text.trim() || isLoading) return;
    
    const userMessage = {
      role: 'user',
      content: text.trim(),
      timestamp: new Date()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);
    setShowQuickActions(false);
    
    try {
      // Build history for context
      const history = messages.map(m => ({
        role: m.role,
        content: m.content
      }));
      
      const response = await aiAPI.chat(text.trim(), history);
      
      if (response.data?.success) {
        const assistantMessage = {
          role: 'assistant',
          content: response.data.message,
          actions: response.data.actions || [],
          hasActions: response.data.has_actions || false,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        
        // If actions were taken (create/update/delete), notify parent to refresh data
        if (response.data.has_actions && onDataChange) {
          onDataChange();
        }
        
        if (!isOpen) {
          setUnreadCount(prev => prev + 1);
        }
      } else {
        throw new Error(response.data?.error || 'Unknown error');
      }
    } catch (error) {
      console.error('AI chat error:', error);
      const errorMessage = {
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error.response?.data?.error || error.message || 'Please try again.'}`,
        isError: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle form submit
  const handleSubmit = (e) => {
    e.preventDefault();
    sendMessage(inputText);
  };

  // Handle quick action click
  const handleQuickAction = (action) => {
    if (action.prompt.endsWith(': ')) {
      setInputText(action.prompt);
      inputRef.current?.focus();
    } else {
      sendMessage(action.prompt);
    }
  };

  // Voice input
  const toggleVoiceInput = () => {
    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition not supported in your browser.');
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';
    recognitionRef.current = recognition;

    recognition.onresult = (event) => {
      let transcript = '';
      for (let i = 0; i < event.results.length; i++) {
        transcript += event.results[i][0].transcript;
      }
      setInputText(transcript);
    };

    recognition.onend = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };

    recognition.onerror = () => {
      setIsRecording(false);
      recognitionRef.current = null;
    };

    recognition.start();
    setIsRecording(true);
  };

  // Clear chat
  const clearChat = () => {
    setMessages([{
      role: 'assistant',
      content: "Chat cleared! How can I help you?",
      timestamp: new Date()
    }]);
    setShowQuickActions(true);
  };

  // Keyboard shortcut (Cmd/Ctrl + J to toggle)
  useEffect(() => {
    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'j') {
        e.preventDefault();
        setIsOpen(prev => !prev);
      }
      // Escape to close
      if (e.key === 'Escape' && isOpen) {
        setIsOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen]);

  // Render a single message
  const renderMessage = (msg, index) => {
    const isUser = msg.role === 'user';
    
    return (
      <div
        key={index}
        className={`flex gap-2 mb-3 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}
      >
        {/* Avatar */}
        <div className={`flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center ${
          isUser 
            ? 'bg-blue-600 text-white' 
            : msg.isError 
              ? 'bg-red-100 text-red-600'
              : 'bg-gradient-to-br from-purple-500 to-indigo-600 text-white'
        }`}>
          {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
        </div>
        
        {/* Message bubble */}
        <div className={`max-w-[85%] rounded-xl px-3 py-2 text-sm ${
          isUser 
            ? 'bg-blue-600 text-white rounded-tr-sm' 
            : msg.isError
              ? 'bg-red-50 text-red-800 border border-red-200 rounded-tl-sm'
              : 'bg-gray-100 text-gray-900 rounded-tl-sm'
        }`}>
          <div className={`prose prose-sm max-w-none ${isUser ? 'prose-invert' : ''}`}>
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-1 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="mb-1 ml-4 list-disc">{children}</ul>,
                ol: ({ children }) => <ol className="mb-1 ml-4 list-decimal">{children}</ol>,
                li: ({ children }) => <li className="mb-0.5">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
                code: ({ children }) => <code className="bg-black/10 rounded px-1 text-xs">{children}</code>,
              }}
            >
              {msg.content}
            </ReactMarkdown>
          </div>
          
          {/* Action badges */}
          {msg.hasActions && msg.actions?.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-gray-200">
              {msg.actions.map((action, i) => (
                <Badge key={i} variant="outline" className="text-xs bg-white/80">
                  {action.function.replace('_', ' ')}
                </Badge>
              ))}
            </div>
          )}
          
          {/* Timestamp */}
          <div className={`text-[10px] mt-1 ${isUser ? 'text-blue-200' : 'text-gray-400'}`}>
            {msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}
          </div>
        </div>
      </div>
    );
  };

  return (
    <>
      {/* Floating Action Button */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-r from-purple-600 to-indigo-600 rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center group hover:scale-105"
          title="Open AI Assistant (Ctrl+J)"
        >
          <Bot className="w-6 h-6 text-white group-hover:scale-110 transition-transform" />
          {unreadCount > 0 && (
            <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold">
              {unreadCount}
            </span>
          )}
          <span className="absolute -top-8 right-0 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
            OpenClaw AI (⌘J)
          </span>
        </button>
      )}

      {/* Chat Panel */}
      {isOpen && (
        <div className={`fixed z-50 bg-white rounded-xl shadow-2xl border border-gray-200 flex flex-col transition-all duration-300 ${
          isExpanded 
            ? 'bottom-4 right-4 left-4 top-4 md:left-auto md:w-[600px] md:top-4' 
            : 'bottom-4 right-4 w-[380px] h-[560px] max-h-[80vh] overflow-hidden'
        }`}>
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b bg-gradient-to-r from-purple-600 to-indigo-600 rounded-t-xl">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">OpenClaw AI</h3>
                <p className="text-purple-200 text-xs">Your MindFlow Assistant</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={clearChat}
                className="text-white/70 hover:text-white hover:bg-white/10 h-8 w-8 p-0"
                title="Clear chat"
              >
                <Trash2 className="w-4 h-4" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsExpanded(!isExpanded)}
                className="text-white/70 hover:text-white hover:bg-white/10 h-8 w-8 p-0"
                title={isExpanded ? "Minimize" : "Expand"}
              >
                {isExpanded ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="text-white/70 hover:text-white hover:bg-white/10 h-8 w-8 p-0"
                title="Close (Esc)"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* Messages Area */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-1">
              {messages.map((msg, i) => renderMessage(msg, i))}
              
              {/* Loading indicator */}
              {isLoading && (
                <div className="flex gap-2 mb-3">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-3.5 h-3.5 text-white" />
                  </div>
                  <div className="bg-gray-100 rounded-xl rounded-tl-sm px-3 py-2">
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      <span>Thinking...</span>
                    </div>
                  </div>
                </div>
              )}
              
              <div ref={messagesEndRef} />
            </div>
          </ScrollArea>

          {/* Quick Actions */}
          {showQuickActions && messages.length <= 1 && (
            <div className="px-4 pb-2 flex-shrink-0">
              <p className="text-xs text-gray-400 mb-2">Quick actions:</p>
              <div className="flex flex-wrap gap-1.5">
                {QUICK_ACTIONS.map((action, i) => {
                  const Icon = action.icon;
                  return (
                    <button
                      key={i}
                      onClick={() => handleQuickAction(action)}
                      className="flex items-center gap-1.5 px-2.5 py-1.5 text-xs bg-gray-50 hover:bg-purple-50 hover:text-purple-700 border border-gray-200 hover:border-purple-200 rounded-lg transition-colors"
                    >
                      <Icon className="w-3 h-3" />
                      {action.label}
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {/* Input Area */}
          <div className="border-t p-3 flex-shrink-0">
            <form onSubmit={handleSubmit} className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' && !e.shiftKey) {
                      e.preventDefault();
                      handleSubmit(e);
                    }
                  }}
                  placeholder="Ask OpenClaw anything..."
                  className="w-full resize-none rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent min-h-[40px] max-h-[120px]"
                  rows={1}
                  disabled={isLoading}
                />
              </div>
              <div className="flex gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={toggleVoiceInput}
                  className={`h-9 w-9 p-0 ${isRecording ? 'text-red-500 animate-pulse bg-red-50' : 'text-gray-400 hover:text-purple-600'}`}
                  title={isRecording ? 'Stop recording' : 'Voice input'}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={!inputText.trim() || isLoading}
                  className="h-9 w-9 p-0 bg-purple-600 hover:bg-purple-700"
                >
                  <Send className="w-4 h-4" />
                </Button>
              </div>
            </form>
            <p className="text-[10px] text-gray-400 mt-1.5 text-center">
              Powered by OpenClaw AI • Press ⌘J to toggle
            </p>
          </div>
        </div>
      )}
    </>
  );
};

export default AIChatWidget;
