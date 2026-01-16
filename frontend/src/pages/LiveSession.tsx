import React, { useState } from 'react';
import { MicIcon, MicOffIcon, VideoIcon, VideoOffIcon, PhoneOffIcon, MessageSquareIcon, UsersIcon, HandIcon, ScreenShareIcon } from 'lucide-react';
interface LiveSessionProps {
  course: any;
  studentName: string;
  onLeave: () => void;
}

export const LiveSession: React.FC<LiveSessionProps> = ({
  course,
  studentName,
  onLeave
}) => {
  const [audioEnabled, setAudioEnabled] = useState(true);
  const [videoEnabled, setVideoEnabled] = useState(true);
  const [handRaised, setHandRaised] = useState(false);
  const [showChat, setShowChat] = useState(true);
  const [message, setMessage] = useState('');
  const [chatMessages, setChatMessages] = useState([{
    id: 1,
    sender: course.instructor,
    message: "Welcome to today's session!",
    time: '14:01',
    isInstructor: true
  }, {
    id: 2,
    sender: 'Alice Johnson',
    message: 'Looking forward to this class!',
    time: '14:02',
    isInstructor: false
  }]);
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!message.trim()) return;
    const newMessage = {
      id: chatMessages.length + 1,
      sender: studentName,
      message: message.trim(),
      time: new Date().toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit'
      }),
      isInstructor: false
    };
    setChatMessages([...chatMessages, newMessage]);
    setMessage('');
  };
  return <div className="h-screen bg-gray-900 flex flex-col">
      {/* Header */}
      <div className="bg-gray-800 px-6 py-4 flex items-center justify-between border-b border-gray-700">
        <div>
          <h1 className="text-white text-lg font-semibold">{course.title}</h1>
          <p className="text-gray-400 text-sm">{course.instructor}</p>
        </div>
        <div className="flex items-center space-x-4">
          <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-blue-900 text-blue-200">
            <span className="w-2 h-2 mr-2 bg-blue-400 rounded-full animate-pulse"></span>
            LIVE
          </span>
          <div className="flex items-center text-gray-400 text-sm">
            <UsersIcon className="h-4 w-4 mr-2" />
            {course.participants} participants
          </div>
        </div>
      </div>
      {/* Main Content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Video Area */}
        <div className="flex-1 flex flex-col">
          {/* Main Video */}
          <div className="flex-1 bg-black relative">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="w-32 h-32 bg-indigo-600 rounded-full flex items-center justify-center text-white text-4xl font-bold mb-4 mx-auto">
                  {course.instructor.charAt(0)}
                </div>
                <p className="text-white text-xl font-medium">
                  {course.instructor}
                </p>
                <p className="text-gray-400 text-sm mt-2">Presenting</p>
              </div>
            </div>
            {/* Participant Videos */}
            <div className="absolute bottom-4 right-4 flex space-x-2">
              {[1, 2, 3].map(i => <div key={i} className="w-32 h-24 bg-gray-800 rounded-lg border-2 border-gray-700 flex items-center justify-center">
                  <div className="text-white text-sm">Participant {i}</div>
                </div>)}
              {/* Your Video */}
              <div className="w-32 h-24 bg-gray-800 rounded-lg border-2 border-indigo-500 flex items-center justify-center relative">
                <div className="text-white text-sm">You</div>
                <div className="absolute top-1 right-1 bg-indigo-600 text-white text-xs px-2 py-0.5 rounded">
                  Me
                </div>
              </div>
            </div>
          </div>
          {/* Controls */}
          <div className="bg-gray-800 px-6 py-4 flex items-center justify-center space-x-4">
            <button onClick={() => setAudioEnabled(!audioEnabled)} className={`p-4 rounded-full transition-colors ${audioEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'}`} title={audioEnabled ? 'Mute' : 'Unmute'}>
              {audioEnabled ? <MicIcon className="h-6 w-6 text-white" /> : <MicOffIcon className="h-6 w-6 text-white" />}
            </button>
            <button onClick={() => setVideoEnabled(!videoEnabled)} className={`p-4 rounded-full transition-colors ${videoEnabled ? 'bg-gray-700 hover:bg-gray-600' : 'bg-red-600 hover:bg-red-700'}`} title={videoEnabled ? 'Stop Video' : 'Start Video'}>
              {videoEnabled ? <VideoIcon className="h-6 w-6 text-white" /> : <VideoOffIcon className="h-6 w-6 text-white" />}
            </button>
            <button className="p-4 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors" title="Share Screen">
              <ScreenShareIcon className="h-6 w-6 text-white" />
            </button>
            <button onClick={() => setHandRaised(!handRaised)} className={`p-4 rounded-full transition-colors ${handRaised ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-gray-700 hover:bg-gray-600'}`} title={handRaised ? 'Lower Hand' : 'Raise Hand'}>
              <HandIcon className="h-6 w-6 text-white" />
            </button>
            <button onClick={() => setShowChat(!showChat)} className="p-4 rounded-full bg-gray-700 hover:bg-gray-600 transition-colors" title="Toggle Chat">
              <MessageSquareIcon className="h-6 w-6 text-white" />
            </button>
            <button onClick={onLeave} className="p-4 rounded-full bg-red-600 hover:bg-red-700 transition-colors ml-8" title="Leave Class">
              <PhoneOffIcon className="h-6 w-6 text-white" />
            </button>
          </div>
        </div>
        {/* Chat Sidebar */}
        {showChat && <div className="w-80 bg-gray-800 border-l border-gray-700 flex flex-col">
            <div className="px-4 py-3 border-b border-gray-700">
              <h3 className="text-white font-medium">Chat</h3>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {chatMessages.map(msg => <div key={msg.id} className="flex items-start space-x-2">
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${msg.isInstructor ? 'bg-indigo-600' : 'bg-gray-600'}`}>
                    {msg.sender.charAt(0)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <span className="text-white text-sm font-medium">
                        {msg.sender}
                      </span>
                      {msg.isInstructor && <span className="text-xs text-indigo-400">
                          Instructor
                        </span>}
                      <span className="text-xs text-gray-500">{msg.time}</span>
                    </div>
                    <p className="text-gray-300 text-sm mt-1">{msg.message}</p>
                  </div>
                </div>)}
            </div>
            <div className="p-4 border-t border-gray-700">
              <form onSubmit={handleSendMessage} className="flex space-x-2">
                <input type="text" value={message} onChange={e => setMessage(e.target.value)} placeholder="Type a message..." className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                <button type="submit" className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium">
                  Send
                </button>
              </form>
            </div>
          </div>}
      </div>
    </div>;
};
