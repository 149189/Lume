import dynamic from 'next/dynamic';

// Import ChatInterface from the parent repo via path alias
const ChatInterface = dynamic(() => import('@components/ChatInterface'), { ssr: false });

export default function HomePage() {
  return (
    <main className="min-h-screen flex flex-col">
      <div className="flex-1">
        <ChatInterface title="Lume" />
      </div>
    </main>
  );
}
