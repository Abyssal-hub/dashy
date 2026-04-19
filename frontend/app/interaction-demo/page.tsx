'use client';

import { useEffect, useState } from 'react';
import { useInteraction } from '@/hooks/useInteraction';
import { withInteractionTracking } from '@/components/withInteractionTracking';
import { logger } from '@/lib/logger';

// Demo component with automatic tracking
function DemoFormComponent() {
  const [value, setValue] = useState('');
  const { track } = useInteraction();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Track the submit interaction with automatic error handling
    await track(
      'click',
      { element: 'form-submit', component: 'DemoForm' },
      async () => {
        // Simulate API call
        await new Promise(resolve => setTimeout(resolve, 1000));
        alert(`Submitted: ${value}`);
      }
    );
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    
    // Manual tracking for input interaction
    const id = logger.start('input', { 
      element: 'text-input', 
      component: 'DemoForm' 
    });
    
    setValue(newValue);
    
    // End interaction
    logger.end(id);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="block text-sm font-medium">
          Test Input (tracked)
        </label>
        <input
          type="text"
          value={value}
          onChange={handleInputChange}
          className="border p-2 rounded w-full"
          placeholder="Type something..."
        />
      </div>
      <button
        type="submit"
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Submit (tracked with error handling)
      </button>
    </form>
  );
}

// Wrap with automatic tracking
const TrackedDemoForm = withInteractionTracking(DemoFormComponent, {
  type: 'navigation',
  name: 'DemoForm',
  trackLifecycle: true,
});

// Main page component
export default function InteractionDemoPage() {
  const { start, end, trackSync } = useInteraction();
  const [clickCount, setClickCount] = useState(0);

  useEffect(() => {
    // Set user ID when authenticated
    logger.setUserId('demo-user-123');
  }, []);

  const handleManualTrack = () => {
    // Manual tracking with start/end
    const id = start('click', { 
      element: 'manual-track-btn', 
      component: 'InteractionDemoPage' 
    });
    
    try {
      setClickCount(c => c + 1);
      end(id);
    } catch (e) {
      end(id, String(e));
    }
  };

  const handleTrackSync = () => {
    trackSync(
      'click',
      { element: 'track-sync-btn', component: 'InteractionDemoPage' },
      () => {
        // Some synchronous work
        setClickCount(c => c + 1);
        return 'success';
      }
    );
  };

  const handleErrorDemo = async () => {
    const id = start('click', { 
      element: 'error-demo-btn', 
      component: 'InteractionDemoPage' 
    });
    
    try {
      // Simulate an error
      throw new Error('Demo error for testing');
    } catch (e) {
      end(id, String(e));
      alert('Error logged! Check the logs API.');
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto space-y-8">
      <h1 className="text-2xl font-bold">Frontend Interaction Logging Demo</h1>
      
      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold mb-2">Click Count: {clickCount}</h2>
        
        <div className="space-x-2">
          <button
            onClick={handleManualTrack}
            className="bg-green-500 text-white px-4 py-2 rounded"
          >
            Manual Track (start/end)
          </button>
          
          <button
            onClick={handleTrackSync}
            className="bg-purple-500 text-white px-4 py-2 rounded"
          >
            trackSync Helper
          </button>
          
          <button
            onClick={handleErrorDemo}
            className="bg-red-500 text-white px-4 py-2 rounded"
          >
            Simulate Error
          </button>
        </div>
      </div>

      <div className="bg-gray-100 p-4 rounded">
        <h2 className="font-semibold mb-4">Tracked Form Component</h2>
        <TrackedDemoForm />
      </div>

      <div className="text-sm text-gray-600">
        <h3 className="font-semibold">Interactions Logged:</h3>
        <ul className="list-disc pl-5 space-y-1">
          <li>Click - Button clicks with element identification</li>
          <li>Input - Form input changes</li>
          <li>Navigation - Component mount/unmount</li>
          <li>Errors - Failed interactions with error messages</li>
        </ul>
        <p className="mt-4">
          Check the logs at <code>/api/logs?source=frontend</code>
        </p>
      </div>
    </div>
  );
}
