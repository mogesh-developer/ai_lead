import React, { useEffect, useState } from 'react';
import api from '../api';
import { useToast } from '../components/ui/ToastProvider';

const Reminders = () => {
  const [reminders, setReminders] = useState([]);
  const [message, setMessage] = useState('');
  const [remindAt, setRemindAt] = useState('');
  const [leadId, setLeadId] = useState('');
  const [recurrence, setRecurrence] = useState('none');
  const toast = useToast();

  const fetchReminders = async () => {
    try {
      const res = await api.get('/reminders');
      setReminders(res.data || []);
    } catch (err) {
      toast.addToast('Failed to fetch reminders', 'error');
    }
  };

  useEffect(() => { fetchReminders(); }, []);

  const createReminder = async (e) => {
    e.preventDefault();
    if (!message || !remindAt) return toast.addToast('Enter message and remind time', 'warn');
    try {
      await api.post('/reminders', { message, remind_at: remindAt, lead_id: leadId ? Number(leadId) : null, recurrence });
      toast.addToast('Reminder created', 'success');
      setMessage(''); setRemindAt(''); setLeadId(''); setRecurrence('none');
      fetchReminders();
    } catch (err) {
      toast.addToast('Failed to create reminder', 'error');
    }
  };

  const removeReminder = async (id) => {
    try {
      await api.delete(`/reminders/${id}`);
      toast.addToast('Reminder deleted', 'success');
      fetchReminders();
    } catch (err) {
      toast.addToast('Failed to delete', 'error');
    }
  };

  return (
    <div className="max-w-3xl">
      <h2 className="text-2xl font-semibold mb-4">Reminders</h2>

      <form className="bg-white p-4 rounded shadow mb-6 grid grid-cols-1 gap-3" onSubmit={createReminder}>
        <textarea placeholder="Reminder message" value={message} onChange={e => setMessage(e.target.value)} className="border px-3 py-2 rounded" />
        <div className="grid grid-cols-2 gap-3">
          <input type="datetime-local" value={remindAt} onChange={e => setRemindAt(e.target.value)} className="border px-3 py-2 rounded" />
          <input type="number" min="1" placeholder="Lead ID (optional)" value={leadId} onChange={e => setLeadId(e.target.value)} className="border px-3 py-2 rounded" />
        </div>
        <div>
          <select value={recurrence} onChange={e => setRecurrence(e.target.value)} className="border px-3 py-2 rounded">
            <option value="none">No recurrence</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
          </select>
        </div>
        <div className="text-right"><button className="bg-blue-600 text-white px-4 py-2 rounded" type="submit">Create Reminder</button></div>
      </form>

      <div className="space-y-3">
        {reminders.length === 0 && <div className="text-sm text-gray-500">No reminders scheduled.</div>}
        {reminders.map(r => (
          <div key={r.id} className="bg-white p-3 rounded shadow flex items-start justify-between">
            <div>
              <p className="font-medium">{r.message}</p>
              <p className="text-xs text-gray-500">Remind at: {new Date(r.remind_at).toLocaleString()} {r.lead_id ? `• Lead ${r.lead_id}` : ''}</p>
              {r.recurrence && r.recurrence !== 'none' && <p className="text-xs text-gray-400">Recurring: {r.recurrence}</p>}
            </div>
            <div className="flex gap-2">
              <button onClick={() => removeReminder(r.id)} className="text-sm text-red-500">Delete</button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default Reminders;
