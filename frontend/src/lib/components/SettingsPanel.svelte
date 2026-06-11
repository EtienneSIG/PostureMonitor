<script lang="ts">
  import { send } from '$lib/websocket.js';
  import type { AppSettings } from '$lib/stores.svelte.js';

  interface Props {
    settings: AppSettings;
    onclose: () => void;
  }
  let { settings, onclose }: Props = $props();

  function update(patch: Partial<AppSettings>) {
    Object.assign(settings, patch);
    send({ type: 'settings_update', settings: { ...settings } });
  }
</script>

<div class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
  <div class="bg-slate-800 rounded-2xl border border-slate-700 p-6 w-[340px] space-y-5 shadow-2xl">

    <div class="flex items-center justify-between">
      <h2 class="text-lg font-semibold text-white">Settings</h2>
      <button onclick={onclose} class="text-slate-400 hover:text-white transition-colors text-xl leading-none">✕</button>
    </div>

    <!-- Sensitivity -->
    <div class="space-y-2">
      <p class="text-slate-300 text-sm font-medium">Alert Sensitivity</p>
      <div class="flex gap-2" role="group" aria-label="Alert sensitivity">
        {#each (['low', 'medium', 'high'] as const) as level}
          <button
            onclick={() => update({ sensitivity: level })}
            aria-pressed={settings.sensitivity === level}
            class={`flex-1 py-2 rounded-xl text-sm font-medium capitalize transition-all
              ${settings.sensitivity === level
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'}`}
          >
            {level}
          </button>
        {/each}
      </div>
    </div>

    <!-- Language -->
    <div class="space-y-2">
      <p class="text-slate-300 text-sm font-medium">Language</p>
      <div class="flex gap-2" role="group" aria-label="Language">
        {#each (['en', 'fr'] as const) as lang}
          <button
            onclick={() => update({ language: lang })}
            aria-pressed={settings.language === lang}
            class={`flex-1 py-2 rounded-xl text-sm font-medium transition-all
              ${settings.language === lang
                ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/20'
                : 'bg-slate-700 text-slate-400 hover:bg-slate-600 hover:text-white'}`}
          >
            {lang === 'en' ? '🇬🇧 English' : '🇫🇷 Français'}
          </button>
        {/each}
      </div>
    </div>

    <!-- Notifications -->
    <div class="flex items-center justify-between">
      <div>
        <p class="text-slate-300 text-sm font-medium">Desktop Notifications</p>
        <p class="text-slate-500 text-xs">Alert you when posture is poor</p>
      </div>
      <button
        role="switch"
        aria-label="Toggle desktop notifications"
        aria-checked={settings.notifications_enabled}
        onclick={() => update({ notifications_enabled: !settings.notifications_enabled })}
        class={`relative w-11 h-6 rounded-full transition-colors
          ${settings.notifications_enabled ? 'bg-blue-600' : 'bg-slate-600'}`}
      >
        <span class={`absolute top-0.5 left-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform
          ${settings.notifications_enabled ? 'translate-x-5' : 'translate-x-0'}`}>
        </span>
      </button>
    </div>

    <!-- Alert cooldown -->
    <div class="space-y-2">
      <label for="cooldown-slider" class="text-slate-300 text-sm font-medium block">
        Alert cooldown — {settings.alert_cooldown}s
      </label>
      <input
        id="cooldown-slider"
        type="range" min="10" max="120" step="5"
        value={settings.alert_cooldown}
        oninput={(e) => update({ alert_cooldown: Number((e.target as HTMLInputElement).value) })}
        class="w-full accent-blue-500"
      />
      <div class="flex justify-between text-xs text-slate-500">
        <span>10s</span><span>120s</span>
      </div>
    </div>

    <button
      onclick={onclose}
      class="w-full py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm transition-colors shadow-lg shadow-blue-500/20"
    >
      Save & Close
    </button>
  </div>
</div>
