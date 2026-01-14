import RuleList from './RuleList'
import './App.css'

function App() {
    return (
        <div className="app-container">
            <header className="header">
                <div className="header-logo">
                    {/* Simple SVG Logo Placeholder matching Transfer UI style */}
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
                    </svg>
                    <div>
                        <h1>Tazama Admin</h1>
                        <span>FRAUD DETECTION SYSTEM</span>
                    </div>
                </div>
                <div className="header-actions">
                    <button className="btn btn-primary">Logout</button>
                </div>
            </header>

            <main className="main-content">
                <div className="card">
                    <h2>Rules Configuration</h2>
                    <p style={{ marginBottom: '20px', color: 'var(--color-text-secondary)' }}>
                        Manage your Fraud Detection System rules configuration. Disabling a rule removes it from the active network map immediately.
                    </p>
                    <RuleList />
                </div>
            </main>
        </div>
    )
}

export default App
