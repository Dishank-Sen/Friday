import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from './App.jsx';

const { getBackendHealth } = vi.hoisted(() => ({ getBackendHealth: vi.fn() }));

vi.mock('./lib/api.js', () => ({
  backendUrl: 'http://127.0.0.1:41197',
  viewerUrl: 'http://127.0.0.1:35723',
  getBackendHealth,
}));

describe('Friday workspace', () => {
  beforeEach(() => {
    getBackendHealth.mockReset();
    getBackendHealth.mockResolvedValue({ available: true, checkedAt: new Date() });
  });

  it('renders the workspace and embedded live desktop viewer', async () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'Ubuntu desktop' })).toBeInTheDocument();
    expect(screen.getByTitle('Ubuntu XFCE desktop')).toHaveAttribute('src', 'http://127.0.0.1:35723');
    expect(screen.getByRole('heading', { name: 'Friday', level: 2 })).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('Online')).toBeInTheDocument());
  });

  it('accepts a task instruction while making unsupported submission explicit', async () => {
    render(<App />);
    const input = screen.getByLabelText('Describe a task');
    fireEvent.change(input, { target: { value: 'Open the terminal' } });
    expect(input).toHaveValue('Open the terminal');
    expect(screen.getByRole('button', { name: /Run task/ })).toBeDisabled();
    expect(screen.getByText(/no task submission or status interface/i)).toBeInTheDocument();
    expect(getBackendHealth).toHaveBeenCalled();
  });

  it('shows a backend unavailable state and a real health-check activity entry', async () => {
    getBackendHealth.mockResolvedValue({ available: false, reason: 'Cannot reach the desktop control service.' });
    render(<App />);
    await waitFor(() => expect(screen.getByText('Offline')).toBeInTheDocument());
    fireEvent.click(screen.getByRole('tab', { name: /Activity/ }));
    expect(await screen.findByText('Cannot reach the desktop control service.')).toBeInTheDocument();
    expect(screen.getByText(/no task event stream/i)).toBeInTheDocument();
  });

  it('shows viewer loading and connected states, and reconnect remounts the viewer', async () => {
    render(<App />);
    expect(screen.getByText('Connecting to Ubuntu')).toBeInTheDocument();
    fireEvent.load(screen.getByTitle('Ubuntu XFCE desktop'));
    expect(screen.getByText('Interactive desktop')).toBeInTheDocument();
    const firstViewer = screen.getByTitle('Ubuntu XFCE desktop');
    fireEvent.click(screen.getByRole('button', { name: 'Reconnect viewer' }));
    expect(screen.getByText('Connecting to Ubuntu')).toBeInTheDocument();
    expect(screen.getByTitle('Ubuntu XFCE desktop')).not.toBe(firstViewer);
  });

  it('shows viewer failure after a connection timeout and offers reconnect', async () => {
    vi.useFakeTimers();
    render(<App />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(15000);
    });
    expect(screen.getByRole('alert')).toHaveTextContent('Couldn’t connect to the viewer');
    expect(screen.getByRole('button', { name: /Try again/ })).toBeInTheDocument();
    vi.useRealTimers();
  });

  it('keeps execution, pause, resume, stop, and take-control unavailable', () => {
    render(<App />);
    expect(screen.getByRole('button', { name: /Run task/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Pause/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Resume/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Stop/ })).toBeDisabled();
    expect(screen.getByRole('button', { name: /Take control unavailable/ })).toBeDisabled();
  });

  it('explains that task history is not persisted', () => {
    render(<App />);
    fireEvent.click(screen.getByRole('button', { name: /Task history/ }));
    expect(screen.getByRole('dialog')).toHaveTextContent('No saved tasks');
    expect(screen.getByRole('dialog')).toHaveTextContent('no task or persistence interface');
  });
});
