/**
 * DECISION-MEMORY API Hook
 * Wraps fetch with auth headers and error handling.
 */

import { useState, useCallback } from 'react';

const API_BASE = '/api/decisions';
const POLICIES_API = '/api/policies';

export function useDecisionApi(token, teamId) {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const fetchWithAuth = useCallback(async (url, options = {}) => {
        setLoading(true);
        setError(null);
        try {
            const headers = {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...options.headers
            };

            // Auto-inject team_id if GET request query param, or body if POST
            // But middleware reads from query string or body.
            // Easiest is to append ?team_id=... to URL for GET
            // And add to body for POST if JSON.

            let finalUrl = url;
            if (options.method === 'GET' || !options.method) {
                finalUrl += (url.includes('?') ? '&' : '?') + `team_id=${teamId}`;
            }

            if (options.body && typeof options.body === 'string') {
                const bodyObj = JSON.parse(options.body);
                if (!bodyObj.team_id) bodyObj.team_id = teamId;
                options.body = JSON.stringify(bodyObj);
            }

            const response = await fetch(finalUrl, { ...options, headers });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || 'API request failed');
            }

            return data;
        } catch (err) {
            setError(err.message);
            throw err;
        } finally {
            setLoading(false);
        }
    }, [token, teamId]);

    // Decisions
    const createDecision = (data) => fetchWithAuth(API_BASE, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const listDecisions = (params = {}) => {
        const qs = new URLSearchParams(params).toString();
        return fetchWithAuth(`${API_BASE}?${qs}`);
    };

    const getDecision = (id) => fetchWithAuth(`${API_BASE}/${id}`);

    const lockDecision = (id) => fetchWithAuth(`${API_BASE}/${id}/lock`, {
        method: 'POST'
    });

    // Inputs
    const attachInput = (id, data) => fetchWithAuth(`${API_BASE}/${id}/inputs`, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const listInputs = (id) => fetchWithAuth(`${API_BASE}/${id}/inputs`);

    // Context
    const setContext = (id, data) => fetchWithAuth(`${API_BASE}/${id}/context`, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const getContext = (id) => fetchWithAuth(`${API_BASE}/${id}/context`);

    // Rationale
    const recordRationale = (id, data) => fetchWithAuth(`${API_BASE}/${id}/rationale`, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const getRationale = (id) => fetchWithAuth(`${API_BASE}/${id}/rationale`);

    // Actors
    const registerActor = (id, data) => fetchWithAuth(`${API_BASE}/${id}/actors`, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const listActors = (id) => fetchWithAuth(`${API_BASE}/${id}/actors`);

    // Overrides
    const createOverride = (id, reason) => fetchWithAuth(`${API_BASE}/${id}/overrides`, {
        method: 'POST',
        body: JSON.stringify({ reason })
    });

    const listOverrides = (id) => fetchWithAuth(`${API_BASE}/${id}/overrides`);

    // Risk
    const getRiskScore = (id) => fetchWithAuth(`${API_BASE}/${id}/risk`);

    // Policies
    const createPolicy = (data) => fetchWithAuth(POLICIES_API, {
        method: 'POST',
        body: JSON.stringify(data)
    });

    const listPolicies = (activeOnly = true) => fetchWithAuth(`${POLICIES_API}?active_only=${activeOnly}`);

    return {
        loading,
        error,
        createDecision,
        listDecisions,
        getDecision,
        lockDecision,
        attachInput,
        listInputs,
        setContext,
        getContext,
        recordRationale,
        getRationale,
        registerActor,
        listActors,
        createOverride,
        listOverrides,
        getRiskScore,
        createPolicy,
        listPolicies
    };
}
