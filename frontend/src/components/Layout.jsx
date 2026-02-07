import React, { useEffect, useState } from 'react';
import Sidebar from './Sidebar';
import { HiBell, HiSearch, HiUserCircle } from 'react-icons/hi';
import ToastProvider, { useToast } from './ui/ToastProvider';
import api from '../api';

const Layout = ({ children }) => {
  const Wrapper = () => {
    const toast = useToast();
    const [pollInterval] = useState(20);

    useEffect(() => {
      let cancelled = false;
      const fetchNotifications = async () => {
        try {
          const res = await api.get('/notifications?unread=true');
          const notifs = res.data || [];
          for (const n of notifs) {
            // Show toast
            const msg = n.payload && n.payload.message ? n.payload.message : (n.payload && n.payload.reminder_id ? `Reminder: ${n.payload.message || ''}` : 'Notification');
            toast.addToast(msg, 'info');
            // Mark read
            try {
              await api.post(`/notifications/${n.id}/read`);
            } catch (err) {
              console.warn('Failed to mark notification read', err);
            }
          }
        } catch (err) {
          // silently ignore polling errors
        }
      };

      // Initial fetch
      fetchNotifications();
      const handle = setInterval(() => { if (!cancelled) fetchNotifications(); }, pollInterval * 1000);
      return () => { cancelled = true; clearInterval(handle); };
    }, [toast, pollInterval]);

    return (
      <div className="flex bg-gray-50 min-h-screen">
        <Sidebar />
        <div className="flex-grow ml-64 flex flex-col">
          {/* Top Header */}
          <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 sticky top-0 z-10">
            <div className="flex items-center bg-gray-100 px-3 py-1.5 rounded-lg w-full max-w-lg">
              <HiSearch className="text-gray-400 w-5 h-5" />
              <input 
                type="text" 
                placeholder="Search leads, campaigns..." 
                className="bg-transparent border-none focus:ring-0 text-sm w-full ml-2"
              />
            </div>
            
            <div className="flex items-center gap-4">
              <button className="p-2 text-gray-500 hover:bg-gray-100 rounded-full transition-all relative">
                <HiBell className="w-6 h-6" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full border-2 border-white"></span>
              </button>
              <div className="h-8 border-l border-gray-200 mx-2"></div>
              <div className="flex items-center gap-3 cursor-pointer group">
                <div className="text-right">
                  <p className="text-sm font-semibold text-gray-900 leading-none">Admin User</p>
                  <p className="text-xs text-gray-500 mt-1 leading-none">Pro Plan</p>
                </div>
                <HiUserCircle className="w-10 h-10 text-gray-300 group-hover:text-blue-500 transition-all" />
              </div>
            </div>
          </header>

          {/* Content */}
          <main className="p-6 md:p-8">
            {children}
          </main>
        </div>
      </div>
    );
  };

  return (
    <ToastProvider>
      <Wrapper />
    </ToastProvider>
  );
};

export default Layout;