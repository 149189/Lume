import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ChatInterface from '@components/ChatInterface';

// Mock api client from parent repo
jest.mock('@root/api-client', () => ({
  api: {
    sendPrompt: jest.fn(async (prompt: string) => ({
      status: 200,
      data: {
        success: true,
        message: 'OK',
        intent: { service: 'gmail', action: 'send_email', parameters: {}, confidence: 0.9 },
        result: { action: 'send_email', status: 'success', message: 'Sent', details: {} },
        execution_time: 0.2,
        timestamp: new Date().toISOString(),
      },
    })),
  },
}));

describe('ChatInterface', () => {
  it('renders header and input', () => {
    render(<ChatInterface title="Lume" />);
    expect(screen.getByText('Lume')).toBeInTheDocument();
    expect(screen.getByLabelText('Message input')).toBeInTheDocument();
  });

  it('sends a message and shows assistant reply', async () => {
    render(<ChatInterface title="Lume" />);

    const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Hello' } });

    const sendButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendButton);

    // user message appears immediately
    expect(await screen.findByText('Hello')).toBeInTheDocument();

    // assistant response appears
    await waitFor(() => {
      expect(screen.getByText(/Sent|OK|Done\./i)).toBeInTheDocument();
    });
  });

  it('shows quick replies under assistant messages', async () => {
    render(<ChatInterface title="Lume" />);

    const textarea = screen.getByLabelText('Message input') as HTMLTextAreaElement;
    fireEvent.change(textarea, { target: { value: 'Email John' } });

    const sendButton = screen.getByRole('button', { name: /send message/i });
    fireEvent.click(sendButton);

    await waitFor(() => {
      expect(screen.getByText(/Draft a reply/i)).toBeInTheDocument();
    });
  });
});
