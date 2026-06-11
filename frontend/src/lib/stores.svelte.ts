/**
 * Reactive store for posture monitoring state.
 * Uses Svelte 5 runes ($state, $derived).
 */

export type PostureStatus = 'good' | 'fair' | 'poor' | 'no_detection' | 'disabled';

export interface PostureEntry {
  status: PostureStatus;
  confidence: number;
  issues: string[];
  message: string;
  timestamp: number;
}

export interface AppSettings {
  sensitivity: 'low' | 'medium' | 'high';
  language: 'en' | 'fr';
  notifications_enabled: boolean;
  alert_cooldown: number;
}

// ── global reactive state ────────────────────────────────────────────────────

export const posture = $state<PostureEntry>({
  status: 'no_detection',
  confidence: 0,
  issues: [],
  message: 'Connecting…',
  timestamp: Date.now()
});

export const monitoring = $state({ active: false });

export const settings = $state<AppSettings>({
  sensitivity: 'low',
  language: 'en',
  notifications_enabled: true,
  alert_cooldown: 30
});

export const history = $state<PostureEntry[]>([]);
export const wsState = $state<{ current: 'connecting' | 'open' | 'closed' | 'error' }>({ current: 'connecting' });
export const videoEnabled = $state({ active: false });

export const MAX_HISTORY = 60;

export function pushHistory(entry: PostureEntry) {
  history.unshift({ ...entry });
  if (history.length > MAX_HISTORY) history.splice(MAX_HISTORY);
}
