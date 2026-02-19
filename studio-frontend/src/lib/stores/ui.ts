import { writable } from 'svelte/store';

export const rightPanelOpen = writable(true);
export const bottomPanelOpen = writable(true);
export const bottomPanelTab = writable<'chat' | 'console' | 'timeline' | 'code'>('console');
export const commandPaletteOpen = writable(false);
export const shortcutsModalOpen = writable(false);
