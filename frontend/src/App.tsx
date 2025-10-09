import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, MoreVertical, Sparkles, RotateCcw, Trash2, Mic, MicOff, Moon, Sun } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import rehypeHighlight from 'rehype-highlight';
import 'highlight.js/styles/github-dark.css';
import './App.css';
import FaviconLogo from './favicon.svg';

// Types
interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: Date;
}

interface Profile {
  id: 'krishna' | 'tejuu';
  name: string;
  initials: string;
  title: string;
  color: string;
}

// Profile configurations
const profiles: Profile[] = [
  {
    id: 'krishna',
    name: 'Krishna',
    initials: 'KS',
    title: 'Data Engineer & ML',
    color: 'bg-blue-600'
  },
  {
    id: 'tejuu',
    name: 'Tejuu',
    initials: 'TJ',
    title: 'Business Analyst & BI',
    color: 'bg-pink-600'
  }
];

// Mode configurations per profile
const profileModes = {
  krishna: [
    { id: 'de', name: '📊 DE Mode', description: 'Data Engineering' },
    { id: 'ai', name: '🧠 AI/ML/GenAI Mode', description: 'AI/ML/GenAI' }
  ],
  tejuu: [
    { id: 'bi', name: '📊 BI Mode', description: 'Business Intelligence' }
  ]
};

function App() {
  // RAG AI Chatbot with Light/Dark Theme Support
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentProfile, setCurrentProfile] = useState<'krishna' | 'tejuu'>('krishna');
  const [currentMode, setCurrentMode] = useState<{[key: string]: string}>({
    krishna: 'de',
    tejuu: 'bi'
  });
  const [chatHistory, setChatHistory] = useState<{[key: string]: Message[]}>({
    krishna: [],
    tejuu: []
  });
  const [conversations, setConversations] = useState<{title: string, messages: Message[], timestamp: number}[]>([]);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isProfileDropdownOpen, setIsProfileDropdownOpen] = useState(false);
  const [showFullHistory, setShowFullHistory] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [isTranscribing, setIsTranscribing] = useState(false);
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Helper function to get mode-specific title
  const getModeSpecificTitle = (profile: string, mode: string) => {
    if (profile === 'krishna') {
      if (mode === 'de') return 'Data Engineer';
      if (mode === 'ai') return 'AI/ML/GenAI';
      return 'Data Engineer'; // fallback
    }
    return profiles.find(p => p.id === profile)?.title || '';
  };

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Load theme from localStorage
  useEffect(() => {
    const savedTheme = localStorage.getItem('ragTheme');
    if (savedTheme) {
      setIsDarkMode(savedTheme === 'dark');
    } else {
      // Default to light mode if no preference is saved
      setIsDarkMode(false);
    }
  }, []);

  // Apply theme to document
  useEffect(() => {
    document.documentElement.classList.toggle('dark', isDarkMode);
    localStorage.setItem('ragTheme', isDarkMode ? 'dark' : 'light');
  }, [isDarkMode]);

  // Toggle theme function
  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  // Load chat history from localStorage
  useEffect(() => {
    const savedHistory = localStorage.getItem('ragChatHistory');
    const savedConversations = localStorage.getItem('ragConversations');
    
    if (savedHistory) {
      try {
        const parsed = JSON.parse(savedHistory);
        setChatHistory(parsed);
        const profileMessages = parsed[currentProfile] || [];
        
        // If no messages for this profile, show welcome message
        if (profileMessages.length === 0) {
          const title = getModeSpecificTitle(currentProfile, currentMode[currentProfile]);
          const welcomeMessage: Message = {
            id: Date.now().toString(),
            content: `Hello! ${profiles.find(p => p.id === currentProfile)?.name}, I'm Kish your ${title} assistant. How can I help you today?`,
            role: 'assistant',
            timestamp: new Date()
          };
          setMessages([welcomeMessage]);
        } else {
          setMessages(profileMessages);
        }
      } catch (error) {
        console.error('Error loading chat history:', error);
      }
    } else {
      // No saved history at all, show welcome message
      const title = getModeSpecificTitle(currentProfile, currentMode[currentProfile]);
      const welcomeMessage: Message = {
        id: Date.now().toString(),
        content: `Hello! ${profiles.find(p => p.id === currentProfile)?.name}, I'm Kish your ${title} assistant. How can I help you today?`,
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages([welcomeMessage]);
    }
    
    if (savedConversations) {
      try {
        const parsed = JSON.parse(savedConversations);
        if (Array.isArray(parsed)) {
          // Handle both old format (string[]) and new format (object[])
          if (parsed.length > 0 && typeof parsed[0] === 'string') {
            // Convert old format to new format
            const newFormat = parsed.map((title: string, index: number) => ({
              title: title.trim(),
              messages: [],
              timestamp: Date.now() - (parsed.length - index) * 1000 // Spread timestamps
            }));
            setConversations(newFormat);
            localStorage.setItem('ragConversations', JSON.stringify(newFormat));
          } else {
            // New format - remove duplicates based on title
            const uniqueConversations = parsed.filter((conv: any, index: number, array: any[]) => 
              array.findIndex(item => item.title?.trim() === conv.title?.trim()) === index
            );
            setConversations(uniqueConversations);
            if (uniqueConversations.length !== parsed.length) {
              localStorage.setItem('ragConversations', JSON.stringify(uniqueConversations));
            }
          }
        } else {
          setConversations([]);
        }
      } catch (error) {
        console.error('Error loading conversations:', error);
        setConversations([]);
      }
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Save chat history to localStorage
  const saveChatHistory = useCallback((newMessages: Message[], profile: string) => {
    setChatHistory(prev => {
      const newHistory = { ...prev, [profile]: newMessages };
      localStorage.setItem('ragChatHistory', JSON.stringify(newHistory));
      return newHistory;
    });
  }, []);

  useEffect(() => {
    if (messages.length > 0 && !isDeleting) {
      saveChatHistory(messages, currentProfile);
    }
  }, [messages, currentProfile, saveChatHistory, isDeleting]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [inputValue]);

  // Handle profile switch
  const handleProfileSwitch = (profileId: 'krishna' | 'tejuu') => {
    if (profileId !== currentProfile) {
      // Save current chat
      saveChatHistory(messages, currentProfile);
      
      // Load new profile chat
      setCurrentProfile(profileId);
      const newMessages = chatHistory[profileId] || [];
      setMessages(newMessages);
      
      // Add welcome message if no history for this profile
      if (newMessages.length === 0) {
        const title = getModeSpecificTitle(profileId, currentMode[profileId]);
        const welcomeMessage: Message = {
          id: Date.now().toString(),
          content: `Hello! ${profiles.find(p => p.id === profileId)?.name}, I'm Kish your ${title} assistant. How can I help you today?`,
          role: 'assistant',
          timestamp: new Date()
        };
        setMessages([welcomeMessage]);
      }
    }
  };

  // Send message
  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      content: inputValue,
      role: 'user',
      timestamp: new Date()
    };

    // Note: Conversation will be saved after getting the assistant's response

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: inputValue,
          mode: currentMode[currentProfile],
          profile: currentProfile
        })
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: data.answer,
        role: 'assistant',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
      
      // Only save conversation if it's a meaningful exchange (multiple messages or explicit new conversation)
      const currentMessages = [...messages, userMessage, assistantMessage];
      const shouldSaveConversation = currentMessages.length > 2 || currentMessages.filter(msg => msg.role === 'user').length > 1;
      
      if (shouldSaveConversation) {
        // Update conversation with complete message history
        const conversationTitle = inputValue.substring(0, 30) + (inputValue.length > 30 ? '...' : '');
        const updatedConversations = conversations.map(conv => {
          if (conv.title.trim() === conversationTitle.trim()) {
            return {
              ...conv,
              messages: currentMessages
            };
          }
          return conv;
        });
        
        // If conversation doesn't exist, create it with full messages
        const existingConv = updatedConversations.find(conv => conv.title.trim() === conversationTitle.trim());
        if (!existingConv) {
          const conversationData = {
            title: conversationTitle,
            messages: currentMessages,
            timestamp: Date.now()
          };
          updatedConversations.unshift(conversationData);
        }
        
        // Keep only the most recent 10 conversations
        const finalConversations = updatedConversations.slice(0, 10);
        setConversations(finalConversations);
        localStorage.setItem('ragConversations', JSON.stringify(finalConversations));
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        content: 'Sorry, I encountered an error. Please try again.',
        role: 'assistant',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
      
      // Only save conversation if it's a meaningful exchange (multiple messages or explicit new conversation)
      const currentMessages = [...messages, userMessage, errorMessage];
      const shouldSaveConversation = currentMessages.length > 2 || currentMessages.filter(msg => msg.role === 'user').length > 1;
      
      if (shouldSaveConversation) {
        // Update conversation with user message and error message
        const conversationTitle = inputValue.substring(0, 30) + (inputValue.length > 30 ? '...' : '');
        const updatedConversations = conversations.map(conv => {
          if (conv.title.trim() === conversationTitle.trim()) {
            return {
              ...conv,
              messages: currentMessages
            };
          }
          return conv;
        });
        
        // If conversation doesn't exist, create it with messages including error
        const existingConv = updatedConversations.find(conv => conv.title.trim() === conversationTitle.trim());
        if (!existingConv) {
          const conversationData = {
            title: conversationTitle,
            messages: currentMessages,
            timestamp: Date.now()
          };
          updatedConversations.unshift(conversationData);
        }
        
        const finalConversations = updatedConversations.slice(0, 10);
        setConversations(finalConversations);
        localStorage.setItem('ragConversations', JSON.stringify(finalConversations));
      }
      
    } finally {
      setIsLoading(false);
    }
  };

  // Handle key press
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // Clear chat
  const clearChat = () => {
    // Save current conversation to recent conversations if it has user messages
    const userMessages = messages.filter(msg => msg.role === 'user');
    if (userMessages.length > 0) {
      const firstUserMessage = userMessages[0];
      const conversationTitle = firstUserMessage.content.substring(0, 50) + (firstUserMessage.content.length > 50 ? '...' : '');
      
      // Create conversation object with full message history
      const conversationData = {
        title: conversationTitle,
        messages: [...messages], // Save all messages from this conversation
        timestamp: Date.now()
      };
      
      // Add to conversations list if not already present (check for exact match)
      const isDuplicate = conversations.some(conv => conv.title.trim() === conversationTitle.trim());
      if (!isDuplicate) {
        const newConversations = [conversationData, ...conversations.slice(0, 9)];
        setConversations(newConversations);
        localStorage.setItem('ragConversations', JSON.stringify(newConversations));
      }
    }
    
    // Set deleting flag to prevent useEffect from saving
    setIsDeleting(true);
    
    const title = getModeSpecificTitle(currentProfile, currentMode[currentProfile]);
    const welcomeMessage: Message = {
      id: Date.now().toString(),
      content: `Hello! ${profiles.find(p => p.id === currentProfile)?.name}, I'm Kish your ${title} assistant. How can I help you today?`,
      role: 'assistant',
      timestamp: new Date()
    };
    
    // Clear the profile's history completely from localStorage
    setChatHistory(prev => {
      const newHistory = { ...prev, [currentProfile]: [] };
      localStorage.setItem('ragChatHistory', JSON.stringify(newHistory));
      return newHistory;
    });
    
    setMessages([welcomeMessage]);
    
    // Reset deleting flag after a short delay
    setTimeout(() => {
      setIsDeleting(false);
    }, 100);
  };

  // Handle profile dropdown toggle
  const toggleProfileDropdown = () => {
    setIsProfileDropdownOpen(!isProfileDropdownOpen);
  };

  // Handle history dropdown toggle (unused - using full history modal instead)
  // const toggleHistoryDropdown = () => {
  //   setIsHistoryDropdownOpen(!isHistoryDropdownOpen);
  //   setIsProfileDropdownOpen(false); // Close profile dropdown
  // };

  // Handle full history toggle
  const toggleFullHistory = () => {
    setShowFullHistory(!showFullHistory);
    setIsProfileDropdownOpen(false);
  };

  // Audio recording functions
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      const chunks: BlobPart[] = [];

      recorder.ondataavailable = (event) => {
        chunks.push(event.data);
      };

      recorder.onstop = async () => {
        const audioBlob = new Blob(chunks, { type: 'audio/wav' });
        await transcribeAudio(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      recorder.start();
      setMediaRecorder(recorder);
      setIsRecording(true);
    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorder && isRecording) {
      mediaRecorder.stop();
      setIsRecording(false);
    }
  };

  const transcribeAudio = async (audioBlob: Blob) => {
    try {
      setIsTranscribing(true);
      const formData = new FormData();
      formData.append('audio_file', audioBlob, 'recording.webm');

      const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/api/transcribe`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Transcription failed');
      }

      const data = await response.json();
      const transcribedText = data.transcript.trim();
      
      if (transcribedText) {
        // Set the transcribed text and automatically send to chat
        setInputValue(transcribedText);
        
        // Create a user message
        const userMessage: Message = {
          id: Date.now().toString(),
          content: transcribedText,
          role: 'user',
          timestamp: new Date()
        };

        // Note: Conversation will be saved after getting the assistant's response

        // Add user message to chat
        setMessages(prev => [...prev, userMessage]);
        setInputValue('');
        setIsLoading(true);

        try {
          const conversationTitle = transcribedText.substring(0, 30) + (transcribedText.length > 30 ? '...' : '');
          const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
          const response = await fetch(`${apiUrl}/api/chat`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              message: transcribedText,
              mode: currentMode[currentProfile],
              profile: currentProfile
            })
          });

          if (!response.ok) {
            throw new Error('Failed to get response');
          }

          const data = await response.json();
          
          const botMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: data.answer,
            role: 'assistant',
            timestamp: new Date()
          };

          setMessages(prev => [...prev, botMessage]);
          
          // Only save conversation if it's a meaningful exchange (multiple messages or explicit new conversation)
          const currentMessages = [...messages, userMessage, botMessage];
          const shouldSaveConversation = currentMessages.length > 2 || currentMessages.filter(msg => msg.role === 'user').length > 1;
          
          if (shouldSaveConversation) {
            // Update conversation with complete message history
            const updatedConversations = conversations.map(conv => {
              if (conv.title.trim() === conversationTitle.trim()) {
                return {
                  ...conv,
                  messages: currentMessages
                };
              }
              return conv;
            });
            
            // If conversation doesn't exist, create it with full messages
            const existingConv = updatedConversations.find(conv => conv.title.trim() === conversationTitle.trim());
            if (!existingConv) {
              const conversationData = {
                title: conversationTitle,
                messages: currentMessages,
                timestamp: Date.now()
              };
              updatedConversations.unshift(conversationData);
            }
            
            // Keep only the most recent 10 conversations
            const finalConversations = updatedConversations.slice(0, 10);
            setConversations(finalConversations);
            localStorage.setItem('ragConversations', JSON.stringify(finalConversations));
          }

        } catch (error) {
          console.error('Error getting bot response:', error);
          const conversationTitle = transcribedText.substring(0, 30) + (transcribedText.length > 30 ? '...' : '');
          const errorMessage: Message = {
            id: (Date.now() + 1).toString(),
            content: 'Sorry, I encountered an error. Please try again.',
            role: 'assistant',
            timestamp: new Date()
          };
          setMessages(prev => [...prev, errorMessage]);
          
          // Only save conversation if it's a meaningful exchange (multiple messages or explicit new conversation)
          const currentMessages = [...messages, userMessage, errorMessage];
          const shouldSaveConversation = currentMessages.length > 2 || currentMessages.filter(msg => msg.role === 'user').length > 1;
          
          if (shouldSaveConversation) {
            // Update conversation with user message and error message
            const updatedConversations = conversations.map(conv => {
              if (conv.title.trim() === conversationTitle.trim()) {
                return {
                  ...conv,
                  messages: currentMessages
                };
              }
              return conv;
            });
            
            // If conversation doesn't exist, create it with messages including error
            const existingConv = updatedConversations.find(conv => conv.title.trim() === conversationTitle.trim());
            if (!existingConv) {
              const conversationData = {
                title: conversationTitle,
                messages: currentMessages,
                timestamp: Date.now()
              };
              updatedConversations.unshift(conversationData);
            }
            
            const finalConversations = updatedConversations.slice(0, 10);
            setConversations(finalConversations);
            localStorage.setItem('ragConversations', JSON.stringify(finalConversations));
          }
          
        } finally {
          setIsLoading(false);
        }
      } else {
        alert('No speech detected. Please try again.');
      }
    } catch (error) {
      console.error('Transcription error:', error);
      alert('Failed to transcribe audio. Please try again.');
    } finally {
      setIsTranscribing(false);
    }
  };

  // Handle profile selection
  const handleProfileSelection = (profileId: 'krishna' | 'tejuu') => {
    handleProfileSwitch(profileId);
    setIsProfileDropdownOpen(false); // Auto-collapse
  };

  // Handle mode selection
  const handleModeSelection = (modeId: string) => {
    setCurrentMode(prev => ({ ...prev, [currentProfile]: modeId }));
    setIsProfileDropdownOpen(false); // Auto-collapse
  };

  // Load conversation from saved conversation data
  const loadConversation = (conversationTitle: string) => {
    // Find the conversation in the conversations list
    const conversation = conversations.find(conv => 
      conv.title.trim() === conversationTitle.trim()
    );
    
    if (conversation && conversation.messages.length > 0) {
      // Load the full conversation messages
      setMessages(conversation.messages);
      setShowFullHistory(false); // Close full history modal
      return;
    }

    // If no conversation found, try to find in chat history
    const currentProfileMessages = chatHistory[currentProfile] || [];
    
    // Look for a conversation that starts with similar content
    const matchingConversation = currentProfileMessages.find(msg => 
      msg.role === 'user' && 
      msg.content.toLowerCase().includes(conversationTitle.toLowerCase().substring(0, 20))
    );
    
    if (matchingConversation) {
      // Find the index of this user message
      const userMessageIndex = currentProfileMessages.findIndex(msg => msg.id === matchingConversation.id);
      
      // Get all messages from this conversation (from the user message to the end)
      const conversationMessages = currentProfileMessages.slice(userMessageIndex);
      
      // Set the messages to show this conversation
      setMessages(conversationMessages);
      setShowFullHistory(false); // Close full history modal
    } else {
      // Try to find by partial title match
      const partialMatch = currentProfileMessages.find(msg => 
        msg.role === 'user' && 
        conversationTitle.toLowerCase().includes(msg.content.toLowerCase().substring(0, 20))
      );
      
      if (partialMatch) {
        const userMessageIndex = currentProfileMessages.findIndex(msg => msg.id === partialMatch.id);
        const conversationMessages = currentProfileMessages.slice(userMessageIndex);
        setMessages(conversationMessages);
        setShowFullHistory(false);
      } else {
        // Show a more helpful message
        const errorMessage: Message = {
          id: Date.now().toString(),
          content: `I couldn't find that conversation. It might have been cleared or the conversation data is incomplete. Try starting a new conversation.`,
          role: 'assistant',
          timestamp: new Date()
        };
        setMessages([errorMessage]);
        setShowFullHistory(false);
      }
    }
  };

  // Delete individual conversation
  const deleteConversation = (conversationIndex: number) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      const newConversations = conversations.filter((_, index) => index !== conversationIndex);
      setConversations(newConversations);
      localStorage.setItem('ragConversations', JSON.stringify(newConversations));
      
      // Clear current chat and start fresh
      clearChat();
    }
  };

  const currentProfileData = profiles.find(p => p.id === currentProfile);

  return (
    <div className={`min-h-screen w-full p-0 flex flex-col mobile-full-height ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
      <div className={`w-full flex-1 flex flex-col ${isDarkMode ? 'bg-[#1E1E1E]' : 'bg-white'}`}>
        {/* Window Controls Bar - Visible on both mobile and desktop */}
        <div className={`flex h-6 items-center px-3 flex-shrink-0 ${isDarkMode ? 'bg-[#2A2A2A]' : 'bg-gray-100'}`}>
          <div className="flex items-center space-x-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
          </div>
        </div>
        
        {/* App Content */}
        <div className="flex flex-1 min-h-0">
          {/* Desktop Sidebar - Always visible on desktop */}
          <div className={`w-64 flex flex-col border-r hidden md:flex flex-shrink-0 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-50 border-gray-300'}`}>
            {/* Brand Name */}
            <div className={`p-4 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
              <div className="flex items-center justify-center space-x-2">
                <img src={FaviconLogo} alt="Logo" className="h-6 w-6" />
                <h1 className={`text-lg font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>RAG AI CHAT BOT</h1>
              </div>
            </div>
            
            {/* New Chat Button - Desktop Only */}
            <div className="p-4">
              <button 
                onClick={clearChat}
                className={`w-full flex items-center justify-center rounded-md border px-3 py-2 text-sm font-medium transition-colors ${
                  isDarkMode 
                    ? 'border-gray-600 hover:bg-gray-700 text-white' 
                    : 'border-gray-300 hover:bg-gray-100 text-gray-700'
                }`}
              >
                New chat
              </button>
            </div>
            
            {/* Profile Selection */}
            <div className="px-4 pb-4">
              <h3 className={`text-xs font-medium mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Profile</h3>
              <select 
                value={currentProfile}
                onChange={(e) => handleProfileSwitch(e.target.value as 'krishna' | 'tejuu')}
                className={`w-full px-3 py-2 rounded-md text-sm border transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                  isDarkMode 
                    ? 'bg-gray-700 text-white border-gray-600 hover:bg-gray-600' 
                    : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50'
                }`}
              >
                {profiles.map(profile => (
                  <option key={profile.id} value={profile.id}>
                    {profile.name} - {profile.title}
                  </option>
                ))}
              </select>
            </div>

            {/* Mode Selection */}
            <div className="px-4 pb-4">
              <h3 className={`text-xs font-medium mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Mode</h3>
              <div className="grid grid-cols-2 gap-1">
                {profileModes[currentProfile].map((mode) => (
                  <button
                    key={mode.id}
                    onClick={() => setCurrentMode(prev => ({ ...prev, [currentProfile]: mode.id }))}
                    className={`text-left rounded-md px-2 py-1.5 text-xs transition-colors ${
                      currentMode[currentProfile] === mode.id 
                        ? (isDarkMode ? 'bg-gray-700 text-white' : 'bg-blue-100 text-blue-700')
                        : (isDarkMode ? 'text-gray-400 hover:bg-gray-700' : 'text-gray-600 hover:bg-gray-100')
                    }`}
                  >
                    <div className="font-medium">{mode.name}</div>
                  </button>
                ))}
              </div>
            </div>
            
            {/* Recent Conversations */}
            <div className="flex-1 overflow-y-auto">
              <div className="px-3 py-2">
                <h3 className={`text-xs font-medium mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>Recent</h3>
                <div className="space-y-1">
                  {conversations.slice(0, 10).map((conv, idx) => (
                    <div
                      key={idx}
                      className={`w-full rounded-md px-3 py-2 text-sm flex items-center justify-between group transition-colors cursor-pointer ${
                        isDarkMode 
                          ? 'hover:bg-gray-700 text-gray-300' 
                          : 'hover:bg-gray-100 text-gray-700'
                      }`}
                      onClick={() => loadConversation(conv.title)}
                    >
                        <div className="flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-xs">
                          {conv.title}
                        </div>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteConversation(idx);
                        }}
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-red-500 hover:bg-opacity-20 transition-all"
                        title="Delete conversation"
                      >
                        <Trash2 className="h-3 w-3 text-red-400 hover:text-red-300" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            

            {/* User Profile Info */}
            <div className={`border-t p-3 ${isDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
              <button className={`w-full text-left rounded-md px-3 py-2 text-sm flex items-center justify-between transition-colors ${
                isDarkMode 
                  ? 'hover:bg-gray-700 text-white' 
                  : 'hover:bg-gray-100 text-gray-700'
              }`}>
                <div className="flex items-center">
                  <div className={`h-7 w-7 rounded-full ${currentProfileData?.color} flex items-center justify-center mr-2`}>
                    <span className="text-xs font-medium">{currentProfileData?.initials}</span>
                  </div>
                  <span className="text-sm">{currentProfileData?.name}</span>
                </div>
                <MoreVertical className={`h-4 w-4 ${isDarkMode ? 'text-gray-400' : 'text-gray-500'}`} />
              </button>
            </div>
          </div>
          


          {/* Main Chat Area */}
          <div className="flex-1 flex flex-col min-h-0 relative mobile-chat-area">
            {/* Mobile Header - Compact Design */}
            <div className={`md:hidden relative border-b flex-shrink-0 ${isDarkMode ? 'bg-gray-800 border-gray-700' : 'bg-gray-100 border-gray-300'}`}>
              {/* Main Header Bar */}
              <div className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center space-x-3">
                  {/* App Logo + Name */}
                  <div className="flex items-center space-x-3">
                    <img src={FaviconLogo} alt="Logo" className="h-5 w-5" />
                    <h1 className={`text-sm font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>RAG AI CHAT BOT</h1>
                  </div>
                </div>
                
                <div className="flex items-center space-x-3">
                  {/* Profile Dropdown Button */}
                  <button 
                    onClick={toggleProfileDropdown}
                    className={`px-3 py-2 rounded-lg text-xs transition-all duration-200 flex items-center space-x-2 shadow-sm ${
                      isDarkMode 
                        ? 'bg-gray-700 text-white hover:bg-gray-600' 
                        : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                    }`}
                  >
                    <span>👤</span>
                    <span>Profile</span>
                    <span className="text-xs opacity-70">{isProfileDropdownOpen ? '▲' : '▼'}</span>
                  </button>
                  
                  {/* History Button */}
                  <button 
                    onClick={toggleFullHistory}
                    className={`px-3 py-2 rounded-lg text-xs transition-all duration-200 flex items-center space-x-2 shadow-sm ${
                      isDarkMode 
                        ? 'bg-gray-700 text-white hover:bg-gray-600' 
                        : 'bg-white text-gray-700 hover:bg-gray-50 border border-gray-300'
                    }`}
                  >
                    <span>📋</span>
                    <span>History</span>
                  </button>
                  
                  {/* Theme Toggle Button */}
                  <button 
                    onClick={toggleTheme}
                    className={`p-2 rounded-lg flex items-center justify-center transition-all duration-200 shadow-sm ${
                      isDarkMode 
                        ? 'bg-gray-700 hover:bg-gray-600 text-white' 
                        : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300'
                    }`}
                    title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
                  >
                    {isDarkMode ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
                  </button>

                  {/* New Chat Button */}
                  <button 
                    onClick={clearChat}
                    className={`p-2 rounded-lg transition-all duration-200 shadow-sm ${
                      isDarkMode 
                        ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                        : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300'
                    }`}
                    title="New chat"
                  >
                    <span className="text-sm font-bold">+</span>
                  </button>
                  
                  {/* Refresh Button */}
                  <button 
                    onClick={clearChat}
                    className={`p-2 rounded-lg transition-all duration-200 shadow-sm flex items-center justify-center ${
                      isDarkMode 
                        ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                        : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300'
                    }`}
                    title="Clear chat"
                  >
                    <RotateCcw className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {/* Profile Dropdown */}
              {isProfileDropdownOpen && (
                <div className="border-t border-gray-700 bg-gray-750 shadow-lg">
                  {/* Profile Selection */}
                  <div className="p-4 border-b border-gray-700">
                    <h3 className="text-xs text-gray-400 font-semibold mb-3 uppercase tracking-wide">Select Profile</h3>
                    <div className="space-y-2">
                      {profiles.map(profile => (
                        <button
                          key={profile.id}
                          onClick={() => handleProfileSelection(profile.id)}
                          className={`w-full text-left px-4 py-3 rounded-lg text-xs transition-all duration-200 ${
                            currentProfile === profile.id 
                              ? 'bg-blue-600 text-white shadow-sm' 
                              : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                          }`}
                        >
                          <div className="font-medium">{profile.name}</div>
                          <div className="text-xs opacity-75 mt-0.5">{profile.title}</div>
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Mode Selection */}
                  <div className="p-4">
                    <h3 className="text-xs text-gray-400 font-semibold mb-3 uppercase tracking-wide">Select Mode</h3>
                    <div className="grid grid-cols-2 gap-2">
                      {profileModes[currentProfile].map((mode) => (
                        <button
                          key={mode.id}
                          onClick={() => handleModeSelection(mode.id)}
                          className={`text-left rounded-lg px-3 py-2.5 text-xs hover:bg-gray-700 transition-all duration-200 ${
                            currentMode[currentProfile] === mode.id 
                              ? 'bg-blue-600 text-white shadow-sm' 
                              : 'text-gray-300 hover:text-white'
                          }`}
                        >
                          <div className="font-medium">{mode.name}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )}

            </div>

            {/* Desktop Chat Header - Minimal and Clean */}
            <div className={`hidden md:flex border-b p-4 items-center justify-between flex-shrink-0 ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-300 bg-gray-100'}`}>
              <div className="flex items-center space-x-4">
                <h2 className={`text-lg font-semibold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                  Chat with {currentProfileData?.name}
                </h2>
                <span className={`px-3 py-1 rounded-md text-sm ${
                  isDarkMode 
                    ? 'bg-gray-700 text-gray-300' 
                    : 'bg-gray-200 text-gray-700'
                }`}>
                  {getModeSpecificTitle(currentProfile, currentMode[currentProfile])}
                </span>
              </div>
              <div className="flex items-center space-x-2">
                {/* Theme Toggle Button */}
                <button 
                  onClick={toggleTheme}
                  className={`p-2 rounded-lg flex items-center justify-center transition-all duration-200 ${
                    isDarkMode 
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                      : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300'
                  }`}
                  title={isDarkMode ? "Switch to light mode" : "Switch to dark mode"}
                >
                  {isDarkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
                </button>
                
                <button 
                  onClick={clearChat}
                  className={`p-2 rounded-lg transition-all duration-200 ${
                    isDarkMode 
                      ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                      : 'bg-white hover:bg-gray-50 text-gray-700 border border-gray-300'
                  }`}
                  title="Clear chat"
                >
                  <RotateCcw className="h-5 w-5" />
                </button>
              </div>
            </div>
            
            {/* Chat Messages */}
            <div className={`flex-1 overflow-y-auto p-3 md:p-4 space-y-4 md:space-y-6 min-h-0 mobile-chat-messages-area ${isDarkMode ? 'bg-gray-900' : 'bg-gray-50'}`}>
              {messages.map((message) => (
                <div key={message.id} className="flex items-start animate-fade-in">
                  <div className={`h-8 w-8 md:h-8 md:w-8 rounded-full ${
                    message.role === 'user' ? currentProfileData?.color : 'bg-green-600'
                  } flex items-center justify-center flex-shrink-0 mr-2 md:mr-3`}>
                    {message.role === 'user' ? (
                      <span className="text-xs font-medium text-white">{currentProfileData?.initials}</span>
                    ) : (
                      <Sparkles className="h-4 w-4 text-white" />
                    )}
                  </div>
                  <div className={`flex-1 min-w-0 rounded-lg p-3 md:p-4 ${isDarkMode ? 'bg-gray-700' : 'bg-gray-100'}`}>
                    <div className={`text-sm ${isDarkMode ? 'text-gray-200' : 'text-gray-700'}`}>
                      <p className={`mb-2 font-semibold text-sm md:text-sm ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>{message.role === 'user' ? 'You' : 'Kish'}</p>
                      {message.role === 'assistant' ? (
                      <div className={`prose prose-sm max-w-none ${isDarkMode ? 'prose-invert' : 'prose-slate'}`}>
                        <ReactMarkdown rehypePlugins={[rehypeHighlight]}>
                          {message.content}
                        </ReactMarkdown>
                      </div>
                      ) : (
                        <p className="whitespace-pre-wrap break-words">{message.content}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {/* Loading Indicator */}
              {isLoading && (
                <div className="flex items-start animate-fade-in">
                  <div className="h-8 w-8 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0 mr-2 md:mr-3">
                    <Sparkles className="h-4 w-4 text-white" />
                  </div>
                  <div className="flex-1">
                    <div className="text-sm text-gray-200">
                      <p className="mb-2 font-semibold">Kish</p>
                      <p className="typing-indicator flex space-x-1">
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></span>
                        <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></span>
                      </p>
                    </div>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            {/* Input Area */}
            <div className={`p-3 md:p-4 border-t flex-shrink-0 mobile-chat-input-area ${isDarkMode ? 'border-gray-700 bg-gray-800' : 'border-gray-300 bg-gray-100'}`}>
              <div className={`relative rounded-lg border shadow-sm ${isDarkMode ? 'border-gray-600 bg-gray-700' : 'border-gray-300 bg-white'}`}>
                <textarea
                  ref={textareaRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyPress}
                  placeholder={`Message ${currentProfileData?.name}...`}
                  className={`w-full p-3 pr-24 text-sm md:text-sm bg-transparent focus:outline-none resize-none ${isDarkMode ? 'text-white placeholder-gray-400' : 'text-gray-900 placeholder-gray-500'}`}
                  rows={1}
                  style={{ maxHeight: '120px' }}
                />
                <div className="absolute right-2 bottom-2 flex items-center space-x-1">
                  {/* Microphone Button */}
                  <button
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={isTranscribing}
                    className={`p-2 md:p-1.5 rounded-md transition-colors ${
                      isTranscribing
                        ? 'bg-yellow-600 text-white cursor-not-allowed'
                        : isRecording 
                          ? 'bg-red-600 hover:bg-red-700 text-white' 
                          : 'text-gray-400 hover:bg-gray-600'
                    }`}
                    title={
                      isTranscribing 
                        ? "Transcribing audio..." 
                        : isRecording 
                          ? "Stop recording" 
                          : "Start recording"
                    }
                  >
                    {isTranscribing ? (
                      <div className="animate-spin h-5 w-5 md:h-5 md:w-5 border-2 border-white border-t-transparent rounded-full" />
                    ) : isRecording ? (
                      <MicOff className="h-5 w-5 md:h-5 md:w-5" />
                    ) : (
                      <Mic className="h-5 w-5 md:h-5 md:w-5" />
                    )}
                  </button>
                  
                  {/* Send Button */}
                  <button
                    onClick={sendMessage}
                    disabled={!inputValue.trim() || isLoading}
                    className="p-2 md:p-1.5 rounded-md text-gray-400 hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Send className="h-5 w-5 md:h-5 md:w-5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Full Screen History Overlay */}
      {showFullHistory && (
        <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
          <div className={`rounded-lg shadow-2xl w-full max-w-4xl max-h-[90vh] flex flex-col ${isDarkMode ? 'bg-gray-800' : 'bg-white'}`}>
            {/* History Header */}
            <div className={`flex items-center justify-between p-6 border-b ${isDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
              <div>
                <h2 className={`text-xl font-bold ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>Conversation History</h2>
                <p className={`text-sm mt-1 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>
                  Tap the 🗑️ icon to delete conversations
                </p>
              </div>
              <button
                onClick={toggleFullHistory}
                className={`p-2 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'bg-gray-700 hover:bg-gray-600 text-gray-300' 
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                <span className="text-xl">×</span>
              </button>
            </div>

            {/* History Content */}
            <div className="flex-1 overflow-y-auto p-6">
              {conversations.length > 0 ? (
                <div className="space-y-3">
                  {conversations.map((conv, idx) => (
                    <div
                      key={idx}
                      className={`rounded-lg p-4 transition-colors cursor-pointer group ${
                        isDarkMode 
                          ? 'bg-gray-700 hover:bg-gray-600' 
                          : 'bg-gray-100 hover:bg-gray-200'
                      }`}
                      onClick={() => {
                        loadConversation(conv.title);
                        setShowFullHistory(false);
                      }}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className={`font-medium text-sm mb-1 ${isDarkMode ? 'text-white' : 'text-gray-900'}`}>
                            Conversation {idx + 1}
                          </div>
                          <div className={`text-xs ${isDarkMode ? 'text-gray-300' : 'text-gray-600'}`}>
                            {conv.title.length > 100 ? `${conv.title.substring(0, 100)}...` : conv.title}
                          </div>
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              deleteConversation(idx);
                            }}
                            className="opacity-100 md:opacity-0 md:group-hover:opacity-100 p-2 rounded-lg hover:bg-red-500 hover:bg-opacity-20 transition-all duration-200"
                            title="Delete conversation"
                          >
                            <Trash2 className="h-4 w-4 text-red-400 hover:text-red-300" />
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className={`text-lg mb-2 ${isDarkMode ? 'text-gray-400' : 'text-gray-600'}`}>No conversations yet</div>
                  <div className={`text-sm ${isDarkMode ? 'text-gray-500' : 'text-gray-500'}`}>Start a new conversation to see your history here</div>
                </div>
              )}
            </div>

            {/* History Footer */}
            <div className={`p-6 border-t ${isDarkMode ? 'border-gray-700' : 'border-gray-300'}`}>
              <button
                onClick={toggleFullHistory}
                className={`w-full py-3 px-4 rounded-lg transition-colors ${
                  isDarkMode 
                    ? 'bg-blue-600 hover:bg-blue-700 text-white' 
                    : 'bg-blue-500 hover:bg-blue-600 text-white'
                }`}
              >
                Close History
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;