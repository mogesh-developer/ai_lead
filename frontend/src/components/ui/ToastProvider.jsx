import React, { createContext, useContext, useState, useEffect } from 'react';
import ReactDOM from 'react-dom/client';

const ToastContext = createContext(null);

export const useToast = () => useContext(ToastContext);

const Toast = ({ id, type = 'info', message, onClose }) => {
  const colors = {
    info: 'bg-blue-600',
    success: 'bg-green-600',
    error: 'bg-red-600',
    warn: 'bg-yellow-500'
  };
  useEffect(() => { const t = setTimeout(onClose, 4500); return () => clearTimeout(t); }, [onClose]);
  return (
    <div className={`text-white px-4 py-2 rounded shadow ${colors[type] || colors.info} max-w-xs`}>
      {message}
    </div>
  );
};

const ToastContainer = ({ toasts }) => {
  return (
    <div className="fixed right-6 top-6 z-50 flex flex-col gap-3">
      {toasts.map(t => (
        <Toast key={t.id} {...t} onClose={t.onClose} />
      ))}
    </div>
  );
};

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);
  const addToast = (message, type = 'info') => {
    const id = Date.now() + Math.random().toString(36).slice(2, 7);
    const t = { id, type, message, onClose: () => setToasts(curr => curr.filter(x => x.id !== id)) };
    setToasts(curr => [t, ...curr]);
    return id;
  };
  const value = { addToast };

  return (
    <ToastContext.Provider value={value}>
      {children}
      {/* Portal root */}
      <ToastContainer toasts={toasts} />
    </ToastContext.Provider>
  );
};

export default ToastProvider;