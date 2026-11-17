import { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { motion } from 'framer-motion';

// Each browser gets its own conversation thread so visitors never see each other's chats.
function getSessionId() {
  let id = null;
  try { id = localStorage.getItem('wellness_session_id'); } catch {}
  if (!id) {
    id = crypto.randomUUID();
    try { localStorage.setItem('wellness_session_id', id); } catch {}
  }
  return id;
}

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'agent', text: "Hi there. I'm here to listen. How are you feeling today?" }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    const userText = input;
    setInput('');
    setIsLoading(true);

    setMessages((prev) => [...prev, { role: 'user', text: userText }, { role: 'agent', text: '' }]);

    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText, session_id: getSessionId() })
      });

      if (!response.body) throw new Error("Stream not supported.");

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let fullAgentText = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n\n'); 

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const dataStr = line.substring(6); 
            
            if (dataStr.trim() === '[DONE]') break;

            try {
              const parsed = JSON.parse(dataStr);
              fullAgentText += parsed.text;

              const displayText = fullAgentText.replace(/^(Wellness Agent:|Crisis System:)\s*/, '');

              setMessages((prev) => {
                const newMessages = [...prev];
                newMessages[newMessages.length - 1].text = displayText;
                return newMessages;
              });
            } catch (err) {
              // Ignore incomplete JSON chunks
            }
          }
        }
      }
    } catch (error) {
      console.error("Streaming error:", error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{ 
      fontFamily: 'system-ui, sans-serif', 
      maxWidth: '650px', 
      margin: '40px auto', 
      padding: '30px', 
      borderRadius: '24px', 
      boxShadow: '0 10px 40px rgba(0,0,0,0.04)', 
      background: 'linear-gradient(145deg, #ffffff, #f8fafc)',
      border: '1px solid #f1f5f9'
    }}>
      <h2 style={{ textAlign: 'center', color: '#475569', fontWeight: '600', marginBottom: '24px', letterSpacing: '-0.5px' }}>
        Mental Wellness Companion
      </h2>
      
      <div style={{ 
        height: '450px', 
        overflowY: 'auto', 
        padding: '24px', 
        backgroundColor: '#ffffff', 
        borderRadius: '20px', 
        marginBottom: '24px', 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '16px',
        boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.02)',
        border: '1px solid #f1f5f9'
      }}>
        {messages.map((msg, index) => (
          <motion.div 
            key={index} 
            initial={{ opacity: 0, y: 10, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            style={{ 
              alignSelf: msg.role === 'user' ? 'flex-end' : 'flex-start', 
              backgroundColor: msg.role === 'user' ? '#334155' : '#f8fafc', 
              color: msg.role === 'user' ? '#ffffff' : '#334155', 
              padding: '14px 20px', 
              borderRadius: msg.role === 'user' ? '20px 20px 4px 20px' : '20px 20px 20px 4px', 
              maxWidth: '80%', 
              lineHeight: '1.6',
              boxShadow: msg.role === 'user' ? '0 4px 12px rgba(51, 65, 85, 0.1)' : '0 2px 6px rgba(0,0,0,0.02)',
              border: msg.role === 'agent' ? '1px solid #e2e8f0' : 'none'
            }}
          >
            {msg.text}
          </motion.div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} style={{ display: 'flex', gap: '12px' }}>
        <input 
          type="text" 
          value={input} 
          onChange={(e) => setInput(e.target.value)} 
          placeholder="Share what's on your mind..." 
          style={{ 
            flex: 1, 
            padding: '16px 20px', 
            borderRadius: '100px', 
            border: '1px solid #e2e8f0', 
            outline: 'none',
            fontSize: '15px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.02)',
            transition: 'border-color 0.2s, box-shadow 0.2s',
          }}
          disabled={isLoading}
        />
        <motion.button 
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          type="submit" 
          disabled={isLoading} 
          style={{ 
            padding: '0 24px', 
            backgroundColor: '#334155', 
            color: 'white', 
            border: 'none', 
            borderRadius: '100px', 
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            boxShadow: '0 4px 12px rgba(51, 65, 85, 0.15)'
          }}
        >
          <Send size={18} />
        </motion.button>
      </form>
    </div>
  );
}