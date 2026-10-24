import { useCallback, useEffect, useRef, useState } from 'react';
import { backendUrl, getBackendHealth, viewerUrl } from './lib/api.js';
import { subscribeToTaskEvents } from './lib/events.js';

const Icon = ({ name, size = 18 }) => {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.7,
    strokeLinecap: 'round',
    strokeLinejoin: 'round',
    'aria-hidden': true,
  };
  const paths = {
    grid: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
    plus: <><path d="M12 5v14M5 12h14" /></>,
    clock: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3 2" /></>,
    settings: <><path d="M12 8.5a3.5 3.5 0 1 0 0 7 3.5 3.5 0 0 0 0-7Z" /><path d="m19.4 15 .1.1 1.2.9-1.2 2.1-1.4-.5a8 8 0 0 1-1.7 1l-.2 1.5h-2.4l-.3-1.5a8 8 0 0 1-1.8-.7l-1.2.8-1.8-1.7.8-1.3a8 8 0 0 1-.7-1.8l-1.5-.3v-2.4l1.5-.3a8 8 0 0 1 .7-1.8l-.8-1.2 1.7-1.8 1.3.8a8 8 0 0 1 1.8-.7l.3-1.5h2.4l.3 1.5a8 8 0 0 1 1.8.7l1.2-.8 1.8 1.7-.8 1.3a8 8 0 0 1 .7 1.8l1.5.3v2.4l-1.5.3a8 8 0 0 1-.7 1.8Z" transform="translate(-1 -1) scale(.95)" /></>,
    shield: <><path d="M12 3.5 19 6v5.2c0 4.3-2.8 7.7-7 9.3-4.2-1.6-7-5-7-9.3V6l7-2.5Z" /><path d="m9 12 2 2 4-4" /></>,
    monitor: <><rect x="3" y="4" width="18" height="13" rx="2" /><path d="M8 21h8m-4-4v4" /></>,
    refresh: <><path d="M20 7v5h-5M4 17v-5h5" /><path d="M5.5 9a7 7 0 0 1 11.8-2L20 12M4 12l2.7 5a7 7 0 0 0 11.8-2" /></>,
    expand: <><path d="M8 3H5a2 2 0 0 0-2 2v3m13-5h3a2 2 0 0 1 2 2v3M3 16v3a2 2 0 0 0 2 2h3m13-5v3a2 2 0 0 1-2 2h-3" /></>,
    external: <><path d="M14 4h6v6m-10 4L20 4" /><path d="M18 13v5a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h5" /></>,
    send: <><path d="m21 3-7.2 18-3.6-7.2L3 10.2 21 3Z" /><path d="M10.2 13.8 15 9" /></>,
    spark: <><path d="m12 3 1.3 5.7L19 10l-5.7 1.3L12 17l-1.3-5.7L5 10l5.7-1.3L12 3Z" /><path d="m19 16 .7 2.3L22 19l-2.3.7L19 22l-.7-2.3L16 19l2.3-.7L19 16Z" /></>,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5m0-8h.01" /></>,
    close: <><path d="m6 6 12 12M18 6 6 18" /></>,
    check: <><path d="m5 12 4 4L19 6" /></>,
    dot: <><circle cx="12" cy="12" r="4" fill="currentColor" stroke="none" /></>,
  };
  return <svg {...common}>{paths[name] ?? paths.info}</svg>;
};

function StatusDot({ state = 'idle' }) {
  return <span className={`status-dot status-dot--${state}`} aria-hidden="true" />;
}

function timeLabel(date) {
  return new Intl.DateTimeFormat(undefined, { hour: '2-digit', minute: '2-digit' }).format(date);
}

export default function App() {
  const [health, setHealth] = useState({ state: 'checking', reason: '' });
  const [activities, setActivities] = useState([]);
  const [viewerState, setViewerState] = useState(viewerUrl ? 'loading' : 'unconfigured');
  const [reloadKey, setReloadKey] = useState(0);
  const [prompt, setPrompt] = useState('');
  const [panelTab, setPanelTab] = useState('chat');
  const [modal, setModal] = useState('');
  const viewerRef = useRef(null);

  const refreshHealth = useCallback(async (signal) => {
    const result = await getBackendHealth({ signal });
    setHealth({
      state: result.available ? 'online' : 'offline',
      reason: result.reason ?? '',
    });
    setActivities((current) => {
      const nextStatus = result.available ? 'online' : 'offline';
      if (current[0]?.kind === 'backend' && current[0]?.status === nextStatus) return current;
      const message = result.available
        ? 'Desktop control service is reachable.'
        : result.reason || 'Desktop control service is unavailable.';
      return [{ id: `${Date.now()}-${nextStatus}`, kind: 'backend', status: nextStatus, message, at: new Date() }, ...current].slice(0, 20);
    });
  }, []);

  useEffect(() => {
    let controller;
    const checkHealth = () => {
      controller?.abort();
      controller = new AbortController();
      refreshHealth(controller.signal).catch((error) => {
        if (error.name !== 'AbortError') setHealth({ state: 'offline', reason: 'Health check failed.' });
      });
    };
    checkHealth();
    const timer = window.setInterval(checkHealth, 15000);
    const taskEvents = subscribeToTaskEvents();
    return () => {
      controller?.abort();
      window.clearInterval(timer);
      taskEvents.close();
    };
  }, [refreshHealth]);

  useEffect(() => {
    if (viewerState !== 'loading') return undefined;
    const timer = window.setTimeout(() => setViewerState('error'), 15000);
    return () => window.clearTimeout(timer);
  }, [viewerState, reloadKey]);

  useEffect(() => {
    if (viewerState !== 'connected' && viewerState !== 'error') return;
    const available = viewerState === 'connected';
    setActivities((current) => {
      const status = available ? 'online' : 'offline';
      if (current[0]?.kind === 'viewer' && current[0]?.status === status) return current;
      return [{
        id: `${Date.now()}-viewer-${status}`,
        kind: 'viewer',
        status,
        message: available ? 'Webtop viewer connected to the desktop.' : 'Webtop viewer did not connect.',
        at: new Date(),
      }, ...current].slice(0, 20);
    });
  }, [viewerState]);

  const handleNewTask = () => {
    setPrompt('');
    setPanelTab('chat');
    setModal('');
  };

  const reconnectViewer = () => {
    setViewerState(viewerUrl ? 'loading' : 'unconfigured');
    setReloadKey((value) => value + 1);
  };

  const enterFullscreen = async () => {
    try {
      await viewerRef.current?.requestFullscreen?.();
    } catch {
      // Fullscreen may be unavailable in embedded or restricted browser contexts.
    }
  };

  const submitInstruction = (event) => {
    event.preventDefault();
  };

  const desktopStatus = viewerState === 'connected' ? 'online' : viewerState === 'error' ? 'offline' : 'checking';

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-lockup">
          <div className="brand-mark"><span /><span /><span /><span /></div>
          <div className="brand-copy"><strong>friday</strong><span>DESKTOP AGENT</span></div>
        </div>

        <div className="workspace-switcher">
          <div className="workspace-avatar">F</div>
          <div className="workspace-copy"><span>WORKSPACE</span><strong>Local machine</strong></div>
          <span className="switcher-chevron">⌄</span>
        </div>

        <div className="side-label">BUILD</div>
        <nav className="primary-nav" aria-label="Main navigation">
          <button className="nav-item nav-item--active" aria-label="Workspace" onClick={handleNewTask}>
            <Icon name="grid" /><span>Workspace</span><span className="nav-shortcut">⌘ 1</span>
          </button>
          <button className="nav-item nav-item--new" aria-label="New task" onClick={handleNewTask}>
            <Icon name="plus" /><span>New task</span>
          </button>
          <button className="nav-item" aria-label="Task history" onClick={() => setModal('history')}>
            <Icon name="clock" /><span>Task history</span><span className="nav-tag">EMPTY</span>
          </button>
          <button className="nav-item" aria-label="Settings" onClick={() => setModal('settings')}>
            <Icon name="settings" /><span>Settings</span>
          </button>
          <button className="nav-item" aria-label="Permissions" onClick={() => setModal('permissions')}>
            <Icon name="shield" /><span>Permissions</span><span className="nav-tag">N/A</span>
          </button>
        </nav>

        <div className="sidebar-spacer" />

        <section className="connection-card" aria-label="Desktop connection status">
          <div className="connection-card-heading"><span>DESKTOP CONNECTION</span><Icon name="monitor" size={15} /></div>
          <div className="connection-state"><StatusDot state={desktopStatus} /><strong>{viewerState === 'connected' ? 'Viewer connected' : viewerState === 'error' ? 'Viewer unavailable' : viewerState === 'unconfigured' ? 'Not configured' : 'Connecting'}</strong></div>
          <div className="connection-meta"><span>Control service</span><span className={`mini-state mini-state--${health.state}`}>{health.state === 'online' ? 'Online' : health.state === 'checking' ? 'Checking' : 'Offline'}</span></div>
        </section>

        <div className="sidebar-profile">
          <div className="profile-avatar">JD</div>
          <div className="profile-copy"><strong>Local session</strong><span>Personal workspace</span></div>
          <span className="profile-menu">···</span>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="breadcrumbs"><span>Workspace</span><span className="breadcrumb-slash">/</span><strong>Desktop</strong><span className="local-pill"><StatusDot state="online" />LOCAL</span></div>
          <div className="topbar-right">
            <div className="agent-availability"><StatusDot state="offline" /><span>Agent execution unavailable</span></div>
            <span className="topbar-divider" />
            <button className="icon-button help-button" aria-label="About Friday" onClick={() => setModal('about')}><Icon name="info" /></button>
            <div className="topbar-avatar">JD</div>
          </div>
        </header>

        <div className="workspace-content">
          <section className="desktop-column" aria-label="Ubuntu desktop workspace">
            <div className="desktop-heading">
              <div>
                <div className="eyebrow"><span className="eyebrow-mark" />LIVE ENVIRONMENT</div>
                <h1>Ubuntu desktop</h1>
                <p>Interact directly with your local Linux environment.</p>
              </div>
              <div className="desktop-actions">
                {viewerUrl && <a className="icon-button" href={viewerUrl} target="_blank" rel="noreferrer" aria-label="Open desktop in a new tab" title="Open in new tab"><Icon name="external" /></a>}
                <button className="icon-button" onClick={reconnectViewer} aria-label="Reconnect viewer" title="Reconnect viewer"><Icon name="refresh" /></button>
                <button className="icon-button" onClick={enterFullscreen} aria-label="Fullscreen desktop" title="Fullscreen"><Icon name="expand" /></button>
              </div>
            </div>

            <div className={`viewer-frame viewer-frame--${viewerState}`} ref={viewerRef}>
              <div className="viewer-toolbar">
                <div className="window-controls"><i /><i /><i /></div>
                <div className="viewer-address"><StatusDot state={desktopStatus} /><span>{viewerUrl || 'Viewer URL not configured'}</span></div>
                <div className="viewer-badge">WEBTOP</div>
              </div>
              {!viewerUrl ? (
                <div className="viewer-placeholder" role="status">
                  <div className="placeholder-icon"><Icon name="monitor" size={26} /></div>
                  <h2>Connect your desktop</h2>
                  <p>Set <code>VITE_VIEWER_URL</code> in <code>frontend/.env.local</code> to the viewer URL printed by <code>python -m friday up</code>.</p>
                  <button className="text-button" onClick={() => setModal('settings')}>View connection settings <span>→</span></button>
                </div>
              ) : (
                <>
                  {viewerState === 'loading' && <div className="viewer-overlay" role="status"><span className="loading-ring" /><strong>Connecting to Ubuntu</strong><span>Opening the existing Webtop session…</span></div>}
                  {viewerState === 'error' && <div className="viewer-overlay viewer-overlay--error" role="alert"><div className="placeholder-icon"><Icon name="monitor" size={26} /></div><strong>Couldn’t connect to the viewer</strong><span>Check that the Friday sandbox is running, then reconnect.</span><button className="secondary-button" onClick={reconnectViewer}><Icon name="refresh" size={15} /> Try again</button></div>}
                  <iframe
                    key={reloadKey}
                    title="Ubuntu XFCE desktop"
                    src={viewerUrl}
                    className={`desktop-iframe ${viewerState === 'error' ? 'desktop-iframe--hidden' : ''}`}
                    allow="clipboard-read; clipboard-write; fullscreen"
                    onLoad={() => setViewerState('connected')}
                    onError={() => setViewerState('error')}
                  />
                </>
              )}
              <div className="viewer-footer"><span><StatusDot state={desktopStatus} />{viewerState === 'connected' ? 'Interactive desktop' : viewerState === 'error' ? 'Connection failed' : viewerState === 'unconfigured' ? 'No viewer URL' : 'Establishing connection'}</span><span>Input handled by Webtop</span></div>
            </div>

            <div className="desktop-note"><Icon name="info" size={15} /><span>Click inside the desktop to use your mouse and keyboard. The viewer remains independent from Friday’s task execution.</span></div>
          </section>

          <aside className="assistant-panel" aria-label="Friday task panel">
            <div className="panel-header">
              <div className="panel-title-wrap"><div className="panel-avatar"><Icon name="spark" size={17} /></div><div><h2>Friday</h2><span>DESKTOP ASSISTANT</span></div></div>
              <button className="icon-button panel-more" aria-label="About task support" onClick={() => setModal('about')}>···</button>
            </div>

            <div className="task-status-card">
              <div className="task-status-top"><span className="task-status-icon"><Icon name="info" size={16} /></span><span className="task-status-label">TASK STATUS</span><span className="status-pill status-pill--unavailable">UNAVAILABLE</span></div>
              <strong>Agent execution isn’t connected</strong>
              <p>The current backend has no task submission or status interface. You can still use the desktop directly.</p>
            </div>

            <div className="panel-tabs" role="tablist" aria-label="Assistant panel">
              <button role="tab" aria-selected={panelTab === 'chat'} className={panelTab === 'chat' ? 'panel-tab panel-tab--active' : 'panel-tab'} onClick={() => setPanelTab('chat')}>Instruction</button>
              <button role="tab" aria-selected={panelTab === 'activity'} className={panelTab === 'activity' ? 'panel-tab panel-tab--active' : 'panel-tab'} onClick={() => setPanelTab('activity')}>Activity <span className="tab-count">{activities.length}</span></button>
            </div>

            {panelTab === 'chat' ? (
              <div className="chat-view">
                <div className="chat-empty">
                  <div className="chat-empty-icon"><Icon name="spark" size={21} /></div>
                  <h3>What should Friday do?</h3>
                  <p>Describe a task for Friday to work on. Task execution will be available when an agent interface is connected.</p>
                  <div className="suggestion-chip"><span className="suggestion-spark">✦</span> Organize files in my workspace</div>
                  <div className="suggestion-chip"><span className="suggestion-spark">✦</span> Find the latest project notes</div>
                </div>
                <form className="composer" onSubmit={submitInstruction}>
                  <label className="sr-only" htmlFor="task-instruction">Describe a task</label>
                  <textarea id="task-instruction" value={prompt} onChange={(event) => setPrompt(event.target.value)} placeholder="Tell Friday what you’d like done…" rows="3" />
                  <div className="composer-bottom"><span><Icon name="info" size={13} /> Agent not connected</span><button type="submit" disabled title="Task submission is not available in this backend">Run task <Icon name="send" size={14} /></button></div>
                </form>
                <div className="controls-section">
                  <div className="controls-heading"><span>SESSION CONTROLS</span><span className="controls-unavailable">NOT SUPPORTED</span></div>
                  <div className="control-buttons"><button disabled title="No pause interface exists"><span>Ⅱ</span> Pause</button><button disabled title="No resume interface exists"><span>▶</span> Resume</button><button disabled title="No stop interface exists"><span>■</span> Stop</button></div>
                  <div className="take-control-row"><span><strong>Take control</strong><small>No agent is running</small></span><button disabled aria-label="Take control unavailable"><span className="toggle-knob" /></button></div>
                  <p className="control-footnote">Manual desktop input is available in the viewer. No agent/manual control lock exists yet.</p>
                </div>
              </div>
            ) : (
              <div className="activity-view" role="tabpanel" aria-label="Activity timeline">
                <div className="activity-intro"><span className="timeline-icon"><Icon name="clock" size={16} /></span><div><strong>Session activity</strong><span>Live connection checks only</span></div></div>
                {activities.length ? <ol className="activity-list">{activities.map((item) => <li key={item.id}><span className={`activity-marker activity-marker--${item.status}`} /><div><p>{item.message}</p><time>{timeLabel(item.at)}</time></div></li>)}</ol> : <div className="activity-empty"><div className="activity-empty-mark"><Icon name="clock" /></div><strong>No activity yet</strong><span>Connection events will appear here.</span></div>}
                <div className="events-notice"><Icon name="info" size={14} /><span>Task progress events are unavailable because the backend has no task event stream.</span></div>
              </div>
            )}

            <div className="panel-footer"><span><span className="privacy-dot" />Local session</span><span>Friday UI <b>·</b> 0.1</span></div>
          </aside>
        </div>
      </main>

      {modal && <div className="modal-backdrop" role="presentation" onMouseDown={(event) => { if (event.target === event.currentTarget) setModal(''); }}>
        <section className="modal-card" role="dialog" aria-modal="true" aria-labelledby="modal-heading">
          <div className="modal-heading"><div className="modal-symbol"><Icon name={modal === 'settings' ? 'settings' : modal === 'permissions' ? 'shield' : modal === 'history' ? 'clock' : 'info'} /></div><button className="icon-button" aria-label="Close" onClick={() => setModal('')}><Icon name="close" /></button></div>
          <h2 id="modal-heading">{modal === 'settings' ? 'Connection settings' : modal === 'permissions' ? 'Permissions' : modal === 'history' ? 'Task history' : 'About Friday'}</h2>
          {modal === 'settings' ? <div className="modal-content"><p>URLs are read from <code>frontend/.env.local</code> when Vite starts.</p><div className="setting-row"><span>Desktop viewer</span><code>{viewerUrl || 'Not configured'}</code></div><div className="setting-row"><span>Backend health</span><code>{backendUrl || 'Not configured'}</code></div><div className="modal-callout">The browser only checks the public health route. Private desktop-control credentials never enter the UI.</div></div>
            : modal === 'permissions' ? <div className="modal-content"><p>Permission prompts and approval gates are not exposed by the current backend.</p><div className="modal-callout">Friday is not running agent actions. Manual input is handled directly by the Webtop viewer.</div></div>
              : modal === 'history' ? <div className="modal-content"><div className="empty-history"><Icon name="clock" /><strong>No saved tasks</strong><span>Task history is not available because the backend has no task or persistence interface.</span></div></div>
                : <div className="modal-content"><p>Friday connects a local React workspace to the existing Ubuntu desktop sandbox.</p><div className="setting-row"><span>Desktop viewer</span><span>Webtop / Selkies</span></div><div className="setting-row"><span>Agent tasks</span><span>Not connected</span></div></div>}
          <button className="modal-done" onClick={() => setModal('')}>Done</button>
        </section>
      </div>}
    </div>
  );
}
