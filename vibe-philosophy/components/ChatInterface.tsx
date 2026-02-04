import React, { useEffect, useRef, useState } from 'react';
import { Message } from '../types';
import { Send, Stars, Bot, User as UserIcon, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface ChatInterfaceProps {
  messages: Message[];
  isLoading: boolean;
  onSendMessage: (text: string) => void;
  isLightMode?: boolean;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({ messages, isLoading, onSendMessage, isLightMode = false }) => {
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  // AI 응답 완료 후 입력창에 자동 포커스
  useEffect(() => {
    if (!isLoading && inputRef.current) {
      // 약간의 지연을 두고 포커스 (애니메이션 완료 후)
      const timer = setTimeout(() => {
        inputRef.current?.focus();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isLoading]);

  const handleSend = () => {
    if (!inputValue.trim()) return;
    onSendMessage(inputValue);
    setInputValue('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full relative">

      {/* Messages Area - 정상 스크롤, 메시지 적을 때만 아래 정렬 */}
      <div className="flex-1 overflow-y-auto px-4 py-4 md:px-6 md:py-6 z-10 scrollbar-hide pt-24">
        <div className="min-h-full flex flex-col">
          {/* 스페이서: 메시지 적을 때 아래로 밀어줌 */}
          <div className="flex-1 min-h-0" />
          <div className="space-y-6">
            {messages.length === 0 && (
            <div className={`flex flex-col items-center justify-center text-center opacity-80 animate-fadeIn pb-10 ${isLightMode ? 'text-amber-700' : 'text-gray-500'}`}>
                <div className={`w-16 h-16 rounded-full flex items-center justify-center border mb-4 shadow-2xl relative ${
                  isLightMode ? 'bg-amber-100 border-amber-300' : 'bg-void-800 border-void-700'
                }`}>
                    <div className={`absolute inset-0 rounded-full animate-pulse-slow ${isLightMode ? 'bg-amber-300/20' : 'bg-gold-400/10'}`}></div>
                    <Stars className={`w-6 h-6 ${isLightMode ? 'text-amber-500' : 'text-gold-300'}`} />
                </div>
                <p className={`font-serif text-xl mb-2 tracking-wide ${isLightMode ? 'text-amber-800' : 'text-gold-100'}`}>운명의 대화를 시작합니다</p>
                <p className={`text-sm font-light ${isLightMode ? 'text-amber-600' : 'text-gray-500'}`}>당신의 이야기가 별들에게 닿기를 기다립니다.</p>
            </div>
            )}
            
            {messages.map((msg) => (
            <div
                key={msg.id}
                className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
            >
                <div className={`flex max-w-[90%] md:max-w-[80%] gap-3 md:gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                
                {/* Avatar */}
                <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 shadow-lg border ${
                    msg.role === 'user'
                    ? isLightMode
                      ? 'bg-amber-100 border-amber-300 text-amber-700'
                      : 'bg-void-800 border-void-600 text-gray-300'
                    : isLightMode
                      ? 'bg-amber-50 border-amber-400 text-amber-600'
                      : 'bg-void-900 border-gold-500/30 text-gold-400'
                }`}>
                    {msg.role === 'user' ? <UserIcon size={18} /> : <Bot size={18} />}
                </div>

                {/* Bubble */}
                <div className={`relative px-5 py-4 rounded-2xl shadow-xl transition-all ${
                    msg.role === 'user'
                    ? isLightMode
                      ? 'bg-white border border-amber-200 text-gray-800 rounded-tr-none'
                      : 'bg-gradient-to-br from-void-800 to-void-900 border border-void-700 text-gray-100 rounded-tr-none'
                    : isLightMode
                      ? 'bg-amber-50 border border-amber-200 text-gray-800 rounded-tl-none'
                      : 'glass-panel text-gray-100 rounded-tl-none border-gold-500/10'
                }`}>
                    <div className={`prose max-w-none break-keep leading-relaxed ${
                        isLightMode ? 'prose-amber' : 'prose-invert'
                    } ${
                        msg.role === 'model'
                          ? `font-book text-lg ${isLightMode ? 'text-gray-800' : 'text-gray-100'}`
                          : `font-sans text-base ${isLightMode ? 'text-gray-700' : 'text-gray-100'}`
                    }`}>
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                    </div>
                    <div className={`text-[10px] opacity-40 mt-1 text-right font-sans ${isLightMode ? 'text-amber-700' : ''}`}>
                    {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                </div>
                </div>
            </div>
            ))}

            {isLoading && (
            <div className="flex w-full justify-start pl-[54px]"> {/* Align with bot messages */}
                <div className={`px-5 py-3 rounded-2xl rounded-tl-none flex items-center gap-3 ${
                  isLightMode
                    ? 'bg-amber-50 border border-amber-200 text-amber-600'
                    : 'glass-panel border-gold-500/10 text-gold-400'
                }`}>
                <Loader2 size={18} className={`animate-spin ${isLightMode ? 'text-amber-500' : 'text-gold-500'}`} />
                <span className={`text-sm font-serif opacity-80 tracking-widest ${isLightMode ? 'text-amber-700' : 'text-gold-200'}`}>운명의 흐름을 읽는 중...</span>
                </div>
            </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>
      </div>

      {/* Input Area - Compact Design */}
      <div className={`px-3 pb-3 pt-2 z-20 transition-colors duration-500 ${
        isLightMode
          ? 'bg-gradient-to-t from-amber-50 via-amber-50 to-transparent'
          : 'bg-gradient-to-t from-void-950 via-void-950 to-transparent'
      }`}>
        <div className="max-w-4xl mx-auto relative group">
          <div className={`absolute -inset-0.5 rounded-full opacity-50 blur group-hover:opacity-75 transition duration-500 ${
            isLightMode
              ? 'bg-gradient-to-r from-amber-400/30 to-orange-400/30'
              : 'bg-gradient-to-r from-gold-500/20 to-violet-500/20'
          }`}></div>
          <div className={`relative flex items-center gap-2 rounded-full p-1.5 border shadow-2xl ${
            isLightMode
              ? 'bg-white border-amber-200'
              : 'bg-void-900 border-void-700'
          }`}>
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="무엇이든 물어보세요..."
              disabled={isLoading}
              className={`flex-1 bg-transparent border-none px-5 py-3 focus:ring-0 focus:outline-none font-sans text-base ${
                isLightMode
                  ? 'text-gray-800 placeholder-amber-400'
                  : 'text-gray-200 placeholder-gray-500'
              }`}
            />
            <button
              onClick={handleSend}
              disabled={isLoading || !inputValue.trim()}
              className={`p-3 rounded-full transition-all duration-300 flex items-center justify-center ${
                isLoading || !inputValue.trim()
                  ? isLightMode
                    ? 'bg-amber-100 text-amber-300'
                    : 'bg-void-800 text-gray-600'
                  : isLightMode
                    ? 'bg-amber-500 hover:bg-amber-400 text-white shadow-[0_0_15px_rgba(245,158,11,0.4)] transform hover:scale-105'
                    : 'bg-gold-500 hover:bg-gold-400 text-void-950 shadow-[0_0_15px_rgba(212,175,55,0.4)] transform hover:scale-105'
              }`}
            >
              <Send size={20} />
            </button>
          </div>
        </div>
        <p className={`text-center text-[10px] mt-1.5 font-sans tracking-wide ${isLightMode ? 'text-amber-500' : 'text-gray-600'}`}>
            AI는 운명의 조언자일 뿐, 선택은 당신의 몫입니다.
        </p>
      </div>
    </div>
  );
};

export default ChatInterface;