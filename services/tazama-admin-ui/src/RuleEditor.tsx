import React, { useState, useEffect } from 'react';

interface Band {
    subRuleRef: string;
    reason: string;
    lowerLimit?: number;
    upperLimit?: number;
}

interface RuleConfig {
    id: string;
    cfg: string;
    desc?: string;
    config: {
        bands?: Band[];
        parameters?: Record<string, any>;
        exitConditions?: any[];
    }
}

interface RuleEditorProps {
    ruleId: string;
    ruleCfg: string;
    onClose: () => void;
}

const RuleEditor: React.FC<RuleEditorProps> = ({ ruleId, ruleCfg, onClose }) => {
    const [rule, setRule] = useState<RuleConfig | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [saving, setSaving] = useState(false);

    useEffect(() => {
        const fetchRule = async () => {
            try {
                const response = await fetch(`/v1/admin/configuration/rule/${ruleId}/${ruleCfg}`);
                if (!response.ok) throw new Error('Failed to fetch rule details');
                const data = await response.json();
                setRule(data);
            } catch (e) {
                setError((e as Error).message);
            } finally {
                setLoading(false);
            }
        };
        fetchRule();
    }, [ruleId, ruleCfg]);

    const saveRule = async () => {
        if (!rule) return;
        setSaving(true);
        setError(null);
        try {
            const response = await fetch(`/v1/admin/configuration/rule/${ruleId}/${ruleCfg}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(rule)
            });

            if (!response.ok) throw new Error('Failed to update rule');

            alert('Rule updated successfully!');
            onClose();
        } catch (e) {
            setError((e as Error).message);
        } finally {
            setSaving(false);
        }
    };

    const updateBand = (index: number, field: keyof Band, value: any) => {
        if (!rule) return;
        const newBands = [...(rule.config.bands || [])];
        newBands[index] = { ...newBands[index], [field]: value };
        setRule({ ...rule, config: { ...rule.config, bands: newBands } });
    };

    const updateParam = (key: string, value: any) => {
        if (!rule) return;
        setRule({
            ...rule,
            config: {
                ...rule.config,
                parameters: { ...rule.config.parameters, [key]: value }
            }
        });
    };

    return (
        <div className="editor-overlay">
            <div className="editor-modal">
                <div className="editor-header">
                    <h3>Edit Rule {ruleId} ({ruleCfg})</h3>
                    <button className="close-btn" onClick={onClose}>&times;</button>
                </div>

                {loading ? (
                    <div className="loading">
                        <div className="spinner"></div>
                        <p style={{ marginLeft: '10px' }}>Loading rule configuration...</p>
                    </div>
                ) : error ? (
                    <div className="error-msg">
                        <p className="error">Error: {error}</p>
                        <button className="btn" onClick={onClose}>Close</button>
                    </div>
                ) : rule && rule.config ? (
                    <div className="config-form">
                        <h4>Description</h4>
                        <div className="form-group">
                            <input
                                value={rule.desc || ''}
                                onChange={(e) => setRule({ ...rule, desc: e.target.value })}
                                placeholder="Rule Description"
                            />
                        </div>

                        {rule.config.bands && rule.config.bands.length > 0 ? (
                            <>
                                <h4>Bands (Limits)</h4>
                                <div className="bands-container">
                                    {rule.config.bands.map((band, i) => (
                                        <div key={i} className="card" style={{ marginBottom: '10px', padding: '10px' }}>
                                            <div className="form-group">
                                                <span className="label">Ref: {band.subRuleRef}</span>
                                            </div>
                                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }} className="form-group">
                                                <label>
                                                    Lower Limit:
                                                    <input
                                                        type="number"
                                                        value={band.lowerLimit || ''}
                                                        onChange={(e) => updateBand(i, 'lowerLimit', parseFloat(e.target.value))}
                                                    />
                                                </label>
                                                <label>
                                                    Upper Limit:
                                                    <input
                                                        type="number"
                                                        value={band.upperLimit || ''}
                                                        onChange={(e) => updateBand(i, 'upperLimit', parseFloat(e.target.value))}
                                                    />
                                                </label>
                                            </div>
                                            <div className="form-group">
                                                <label>
                                                    Reason:
                                                    <input
                                                        type="text"
                                                        value={band.reason || ''}
                                                        onChange={(e) => updateBand(i, 'reason', e.target.value)}
                                                    />
                                                </label>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </>
                        ) : (
                            <p>No bands configured for this rule.</p>
                        )}

                        {rule.config.parameters && (
                            <>
                                <h4>Parameters</h4>
                                <div className="params-container">
                                    {Object.entries(rule.config.parameters).map(([key, value]) => (
                                        <div key={key} className="form-group">
                                            <label htmlFor={key}>{key}:</label>
                                            {typeof value === 'object' ? (
                                                <textarea readOnly value={JSON.stringify(value)} />
                                            ) : (
                                                <input
                                                    id={key}
                                                    value={value as string}
                                                    onChange={(e) => updateParam(key, e.target.value)}
                                                />
                                            )}
                                        </div>
                                    ))}
                                </div>
                            </>
                        )}

                        <div className="actions" style={{ marginTop: '20px', display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                            <button onClick={saveRule} disabled={saving} className="btn btn-primary">
                                {saving ? 'Saving...' : 'Save Changes'}
                            </button>
                            <button onClick={onClose} disabled={saving} className="btn">Cancel</button>
                        </div>
                    </div>
                ) : (
                    <p>Invalid rule configuration format.</p>
                )}
            </div>
        </div>
    );
};

export default RuleEditor;
