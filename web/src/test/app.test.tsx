import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import App from '../App';
describe('app', () => {
 it('keeps caveat and retry on API error', async () => { vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline'))); render(<App />); expect(await screen.findByRole('alert')).toHaveTextContent('Unable to load map data'); expect(screen.getByText(/Satellite-derived estimate/)).toBeVisible(); expect(screen.getByRole('button',{name:'Retry'})).toBeVisible(); });
 it('shows stale warning and filters', async () => { vi.stubGlobal('fetch', vi.fn((url:string) => Promise.resolve({ok:true,json:()=>Promise.resolve(url.includes('metadata')?{last_source_report_at_utc:'2026-10-18T18:00:00Z',freshness_status:'stale'}:{features:[]})}))); render(<App />); expect(await screen.findByText('Data may be delayed')).toBeVisible(); expect(screen.getByLabelText('Time range')).toBeVisible(); expect(screen.getByLabelText('Island')).toBeVisible(); });
});
