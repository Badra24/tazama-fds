import React, { useState, useEffect } from 'react';
import RuleEditor from './RuleEditor';

interface Rule {
    id: string;
    cfg: string;
}

interface NetworkMap {
    id?: string;
    active: boolean;
    cfg: string;
    messages: {
        typologies: {
            rules: Rule[];
        }[];
    }[];
}

// Master list of known rules from 04-network-map.sql
const MASTER_RULES: Rule[] = [
    { id: '901@1.0.0', cfg: '1.0.0' },
    { id: '902@1.0.0', cfg: '1.0.0' },
    { id: '006@1.0.0', cfg: '1.0.0' },
    { id: '018@1.0.0', cfg: '1.0.0' },
    { id: '903@1.0.0', cfg: '1.0.0' }
];

const RuleList: React.FC = () => {
    const [rules, setRules] = useState<(Rule & { status: 'Active' | 'Disabled' })[]>([]);
    const [networkMap, setNetworkMap] = useState<NetworkMap | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [successMessage, setSuccessMessage] = useState<string | null>(null);
    const [editingRule, setEditingRule] = useState<{ id: string, cfg: string } | null>(null);
    const [showRaw, setShowRaw] = useState(false);

    const [updatingRuleId, setUpdatingRuleId] = useState<string | null>(null);

    const fetchRules = async (silent = false) => {
        if (!silent) setLoading(true);
        setError(null);
        try {
            const response = await fetch('/v1/admin/configuration/network_map');
            if (!response.ok) throw new Error('Failed to fetch network map');
            const json = await response.json();
            const data: NetworkMap[] = json.data || json;

            if (data.length > 0) {
                // Use the last item in the array as it represents the latest configuration
                const latestMap = data[data.length - 1];
                setNetworkMap(latestMap);

                // Extract active rules
                const activeRulesMap = new Map<string, Rule>();
                latestMap.messages.forEach(msg => {
                    msg.typologies.forEach(topo => {
                        topo.rules.forEach(rule => {
                            activeRulesMap.set(rule.id, rule);
                        });
                    });
                });

                // Merge with MASTER_RULES to determine status
                const mergedRules = MASTER_RULES.map(masterRule => {
                    const isActive = activeRulesMap.has(masterRule.id);
                    return {
                        ...masterRule,
                        status: isActive ? 'Active' : 'Disabled'
                    } as (Rule & { status: 'Active' | 'Disabled' });
                });

                setRules(mergedRules);
            }
        } catch (e) {
            setError((e as Error).message);
        } finally {
            if (!silent) setLoading(false);
        }
    };

    useEffect(() => {
        fetchRules();
    }, []);

    const toggleRule = async (ruleId: string, currentStatus: 'Active' | 'Disabled') => {
        if (!networkMap) return;
        setUpdatingRuleId(ruleId);

        // Deep copy network map
        const updatedMap = JSON.parse(JSON.stringify(networkMap));
        let modified = false;

        const targetRule = MASTER_RULES.find(r => r.id === ruleId);
        if (!targetRule) {
            setError(`Rule definition for ${ruleId} not found in master list.`);
            setUpdatingRuleId(null);
            return;
        }

        updatedMap.messages.forEach((msg: any) => {
            msg.typologies.forEach((topo: any) => {
                if (currentStatus === 'Active') {
                    // DISABLE: Remove rule from topology
                    const originalLength = topo.rules.length;
                    topo.rules = topo.rules.filter((r: Rule) => r.id !== ruleId);
                    if (topo.rules.length !== originalLength) modified = true;
                } else {
                    // ENABLE: Add rule to topology if not exists
                    const exists = topo.rules.find((r: Rule) => r.id === ruleId);
                    if (!exists) {
                        topo.rules.push(targetRule);
                        modified = true;
                    }
                }
            });
        });

        if (!modified) {
            alert(`No changes needed (Rule was already ${currentStatus})`);
            setUpdatingRuleId(null);
            return;
        }

        try {
            const response = await fetch(`/v1/admin/configuration/network_map`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(updatedMap)
            });

            if (!response.ok) throw new Error('Failed to update map');

            const action = currentStatus === 'Active' ? 'disabled' : 'enabled';
            setSuccessMessage(`Rule ${ruleId} ${action}. Updates apply immediately.`);

            // Silent refresh to update UI without flashing
            await fetchRules(true);
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setUpdatingRuleId(null);
        }
    };

    return (
        <div className="rule-list-container">
            {editingRule && (
                <RuleEditor
                    ruleId={editingRule.id}
                    ruleCfg={editingRule.cfg}
                    onClose={() => setEditingRule(null)}
                />
            )}

            {loading ? (
                <div className="loading">
                    <div className="spinner"></div>
                </div>
            ) : error ? (
                <p className="error">{error}</p>
            ) : (
                <>
                    {successMessage && (
                        <div className="success">
                            <p>{successMessage}</p>
                            <button onClick={() => setSuccessMessage(null)} style={{ marginTop: '10px' }} className="btn">Dismiss</button>
                        </div>
                    )}

                    {rules.length === 0 ? (
                        <p>No rules found.</p>
                    ) : (
                        <ul className="rule-list">
                            {rules.map(rule => {
                                const isUpdating = (r: typeof rule) => updatingRuleId === r.id;
                                return (
                                    <li key={rule.id} className="rule-item" style={{ opacity: rule.status === 'Disabled' && !isUpdating(rule) ? 0.6 : 1 }}>
                                        <div className="rule-info">
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                                <span className="rule-id">Rule {rule.id}</span>
                                                <span className={`status-badge ${rule.status.toLowerCase()}`}
                                                    style={{
                                                        fontSize: '0.7rem',
                                                        padding: '2px 6px',
                                                        borderRadius: '4px',
                                                        backgroundColor: rule.status === 'Active' ? 'var(--color-status-pass)' : 'var(--color-status-inactive)',
                                                        color: 'white'
                                                    }}>
                                                    {rule.status}
                                                </span>
                                            </div>
                                            <span className="rule-cfg">Config: {rule.cfg}</span>
                                        </div>
                                        <div className="rule-actions">
                                            <button
                                                className="btn"
                                                onClick={() => setEditingRule(rule)}
                                                disabled={rule.status === 'Disabled' || updatingRuleId !== null}
                                            >
                                                Edit Config
                                            </button>
                                            <button
                                                className={`btn ${rule.status === 'Active' ? 'danger' : 'primary'}`}
                                                onClick={() => toggleRule(rule.id, rule.status)}
                                                disabled={updatingRuleId !== null}
                                                style={{ minWidth: '80px', position: 'relative' }}
                                            >
                                                {updatingRuleId === rule.id ? (
                                                    <span className="spinner-sm" style={{
                                                        width: '12px',
                                                        height: '12px',
                                                        border: '2px solid rgba(255,255,255,0.3)',
                                                        borderTopColor: '#fff',
                                                        borderRadius: '50%',
                                                        display: 'inline-block',
                                                        animation: 'spin 1s linear infinite'
                                                    }}></span>
                                                ) : (
                                                    rule.status === 'Active' ? 'Disable' : 'Enable'
                                                )}
                                            </button>
                                        </div>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                    <p className="hint">
                        Note: "Disable" removes the rule from the ACTIVE network map. "Edit Config" updates parameters like limits.
                    </p>

                    <div style={{ marginTop: '30px', borderTop: '1px solid #eee', paddingTop: '20px' }}>
                        <button
                            onClick={() => setShowRaw(!showRaw)}
                            style={{ background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: '0.9rem', textDecoration: 'underline' }}
                        >
                            {showRaw ? 'Hide' : 'Show'} Raw Database Configuration
                        </button>

                        {showRaw && networkMap && (
                            <div style={{ marginTop: '10px', background: '#f5f5f5', padding: '15px', borderRadius: '5px', overflowX: 'auto' }}>
                                <p style={{ margin: '0 0 10px 0', fontSize: '0.8rem', fontWeight: 'bold', color: '#333' }}>
                                    Current Active Rules (from Network Map {networkMap.cfg}):
                                </p>
                                <pre style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: '#333' }}>
                                    {JSON.stringify(rules.filter(r => r.status === 'Active'), null, 2)}
                                </pre>
                            </div>
                        )}
                    </div>
                </>
            )}
            <style>{`
                @keyframes spin { to { transform: rotate(360deg); } }
            `}</style>
        </div>
    );
};

export default RuleList;
